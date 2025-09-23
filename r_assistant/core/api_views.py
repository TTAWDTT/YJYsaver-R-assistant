"""
智能对话和其他API视图
"""

import json
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from django.utils import timezone

from services.langgraph_service import langgraph_service
from services.ai_service import AIServiceError
from services.code_analyzer import code_analyzer
from .models import ConversationHistory, RequestLog, CodeAnalysis

logger = logging.getLogger(__name__)


class BaseAPIView(View):
    """API视图基类"""
    
    def _get_session_id(self, request):
        """获取会话ID"""
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        return session_id
    
    def _create_request_log(self, request, request_type, input_content):
        """创建请求日志"""
        return RequestLog.objects.create(
            session_id=self._get_session_id(request),
            request_type=request_type,
            input_content=input_content,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _update_request_log(self, request_log, response_content='', processing_time=0, success=True, error_message=''):
        """更新请求日志"""
        request_log.response_content = response_content
        request_log.processing_time = processing_time
        request_log.success = success  # 使用success字段而不是status
        request_log.error_message = error_message
        request_log.save()
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class TalkAPIView(BaseAPIView):
    """智能对话API"""
    
    @require_http_methods(["POST"])
    def post(self, request: HttpRequest) -> JsonResponse:
        """处理智能对话请求"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({
                    'success': False,
                    'error': '请输入您的问题'
                }, status=400)
            
            session_id = self._get_session_id(request)
            
            # 获取对话历史
            conversation_history = list(
                ConversationHistory.objects.filter(
                    session_id=session_id
                ).order_by('timestamp').values('role', 'content')[-10:]  # 最近10条
            )
            
            # 创建请求日志
            request_log = self._create_request_log(request, 'talk', message)
            
            try:
                # 调用LangGraph服务
                result = langgraph_service.chat(message, conversation_history, session_id)
                
                # 保存用户消息
                ConversationHistory.objects.create(
                    session_id=session_id,
                    role='user',
                    content=message
                )
                
                # 保存AI回复
                ConversationHistory.objects.create(
                    session_id=session_id,
                    role='assistant',
                    content=result['content']
                )
                
                # 更新请求日志
                self._update_request_log(
                    request_log, 
                    result['content'], 
                    result['processing_time']
                )
                
                logger.info("Chat completed for session %s", session_id)
                
                return JsonResponse({
                    'success': True,
                    'response': result['content'],
                    'processing_time': result['processing_time']
                })
                
            except AIServiceError as e:
                # 更新请求日志记录错误
                self._update_request_log(
                    request_log, 
                    '', 
                    0, 
                    success=False, 
                    error_message=str(e)
                )
                
                logger.error("AI service error in chat: %s", str(e))
                
                return JsonResponse({
                    'success': False,
                    'error': '抱歉，AI服务暂时不可用，请稍后重试'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '无效的JSON数据'
            }, status=400)
        except Exception as e:
            logger.error("Unexpected error in chat: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeAPIView(BaseAPIView):
    """代码分析API"""
    
    @require_http_methods(["POST"])
    def post(self, request: HttpRequest) -> JsonResponse:
        """处理代码分析请求"""
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            analysis_type = data.get('type', 'quality')  # quality, test, optimization
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要分析的代码'
                }, status=400)
            
            # 创建请求日志
            request_log = self._create_request_log(request, 'analyze', code)
            session_id = self._get_session_id(request)
            
            try:
                if analysis_type == 'quality':
                    # 静态代码分析
                    analysis_result = code_analyzer.analyze(code)
                    
                    # AI代码质量分析
                    ai_result = langgraph_service.analyze_code_quality(code, session_id)
                    
                    # 合并结果
                    combined_result = {
                        'static_analysis': analysis_result,
                        'ai_analysis': ai_result['content'],
                        'processing_time': ai_result['processing_time']
                    }
                    
                    # 保存分析结果
                    CodeAnalysis.objects.create(
                        request_log=request_log,
                        analysis_type='quality',
                        score=analysis_result.get('quality_score', 0),
                        details=analysis_result,
                        suggestions=ai_result['content']
                    )
                    
                elif analysis_type == 'test':
                    # 测试用例生成
                    ai_result = langgraph_service.generate_tests(code, session_id)
                    combined_result = {
                        'test_cases': ai_result['content'],
                        'processing_time': ai_result['processing_time']
                    }
                    
                    CodeAnalysis.objects.create(
                        request_log=request_log,
                        analysis_type='testing',
                        details={'test_cases': ai_result['content']},
                        suggestions=ai_result['content']
                    )
                    
                elif analysis_type == 'optimization':
                    # 代码优化建议
                    ai_result = langgraph_service.optimize_code(code, session_id)
                    combined_result = {
                        'optimization_suggestions': ai_result['content'],
                        'processing_time': ai_result['processing_time']
                    }
                    
                    CodeAnalysis.objects.create(
                        request_log=request_log,
                        analysis_type='optimization',
                        details={'optimization': ai_result['content']},
                        suggestions=ai_result['content']
                    )
                    
                else:
                    return JsonResponse({
                        'success': False,
                        'error': '不支持的分析类型'
                    }, status=400)
                
                # 更新请求日志
                self._update_request_log(
                    request_log, 
                    str(combined_result), 
                    combined_result.get('processing_time', 0)
                )
                
                logger.info("Code analysis (%s) completed for session %s", analysis_type, request_log.session_id)
                
                return JsonResponse({
                    'success': True,
                    'analysis_type': analysis_type,
                    'result': combined_result
                })
                
            except AIServiceError as e:
                self._update_request_log(
                    request_log, 
                    '', 
                    0, 
                    success=False, 
                    error_message=str(e)
                )
                
                logger.error("AI service error in code analysis: %s", str(e))
                
                return JsonResponse({
                    'success': False,
                    'error': '抱歉，AI服务暂时不可用，请稍后重试'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '无效的JSON数据'
            }, status=400)
        except Exception as e:
            logger.error("Unexpected error in code analysis: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ClearHistoryAPIView(BaseAPIView):
    """清除对话历史API"""
    
    @require_http_methods(["POST"])
    def post(self, request: HttpRequest) -> JsonResponse:
        """清除当前会话的对话历史"""
        try:
            session_id = self._get_session_id(request)
            
            # 删除对话历史
            deleted_count = ConversationHistory.objects.filter(
                session_id=session_id
            ).delete()[0]
            
            logger.info("Cleared %d conversation records for session %s", deleted_count, session_id)
            
            return JsonResponse({
                'success': True,
                'message': f'已清除 {deleted_count} 条对话记录'
            })
            
        except Exception as e:
            logger.error("Error clearing conversation history: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '清除历史记录失败'
            }, status=500)


class HealthCheckAPIView(BaseAPIView):
    """健康检查API"""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """系统健康检查"""
        try:
            # 检查数据库连接
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            
            # 检查AI服务
            ai_status = 'available'
            try:
                test_result = langgraph_service.chat("test", [], "health_check_session")
                if not test_result.get('content'):
                    ai_status = 'degraded'
            except Exception:
                ai_status = 'unavailable'
            
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'services': {
                    'database': 'available',
                    'langgraph_service': ai_status
                }
            })
            
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return JsonResponse({
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ExplainAPIView(BaseAPIView):
    """代码解释API视图"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            analysis_mode = data.get('analysis_mode', 'full')
            full_code = data.get('full_code', '')
            selected_lines = data.get('selected_lines', [])
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要解释的R代码'
                }, status=400)
            
            # 记录请求日志
            log_content = code
            if analysis_mode == 'selected':
                log_content = f"[选中代码分析] 行号: {selected_lines}\n{code}"
            
            request_log = self._create_request_log(request, 'explain', log_content)
            session_id = self._get_session_id(request)
            
            try:
                # 使用LangGraph服务解释代码
                if analysis_mode == 'selected' and full_code:
                    # 为选中代码提供完整上下文
                    context_info = f"完整代码上下文：\n{full_code}\n\n需要解释的选中部分（第{min(selected_lines)}-{max(selected_lines)}行）：\n{code}"
                    result = langgraph_service.explain_code(context_info, session_id, mode='selected')
                else:
                    result = langgraph_service.explain_code(code, session_id, mode=analysis_mode)
                
                # 更新请求日志
                self._update_request_log(
                    request_log, 
                    result.get('content', ''),
                    result.get('processing_time', 0),
                    result.get('success', True),
                    result.get('error', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'explanation': result.get('content', ''),
                    'processing_time': result.get('processing_time', 0),
                    'metadata': result.get('metadata', {}),
                    'analysis_mode': analysis_mode
                })
                
            except AIServiceError as e:
                logger.error("代码解释失败: %s", str(e))
                self._update_request_log(request_log, '', 0, False, str(e))
                
                return JsonResponse({
                    'success': False,
                    'error': f'代码解释失败: {str(e)}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '请求数据格式错误'
            }, status=400)
        except Exception as e:
            logger.error("处理代码解释请求时出错: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerAPIView(BaseAPIView):
    """问题解答API视图"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            problem = data.get('problem', '').strip()
            
            if not problem:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要解决的问题'
                }, status=400)
            
            # 记录请求日志
            request_log = self._create_request_log(request, 'answer', problem)
            session_id = self._get_session_id(request)
            
            try:
                # 使用LangGraph服务解决问题
                result = langgraph_service.solve_problem(problem, session_id)
                
                # 更新请求日志
                self._update_request_log(
                    request_log,
                    f"生成了{len(result.get('solutions', []))}个解决方案",
                    result.get('processing_time', 0),
                    result.get('success', True),
                    result.get('error', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'solutions': result.get('solutions', []),
                    'processing_time': result.get('processing_time', 0),
                    'metadata': result.get('metadata', {})
                })
                
            except AIServiceError as e:
                logger.error("问题解答失败: %s", str(e))
                self._update_request_log(request_log, '', 0, False, str(e))
                
                return JsonResponse({
                    'success': False,
                    'error': f'问题解答失败: {str(e)}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '请求数据格式错误'
            }, status=400)
        except Exception as e:
            logger.error("处理问题解答请求时出错: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerStreamAPIView(BaseAPIView):
    """作业求解流式API视图 - 支持文件上传和实时更新"""
    
    def post(self, request):
        try:
            problem = request.POST.get('problem', '').strip()
            include_comments = request.POST.get('include_comments') == 'on'
            uploaded_files = request.FILES.getlist('uploaded_files')
            
            if not problem:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要解决的问题'
                }, status=400)
            
            session_id = self._get_session_id(request)
            
            # 处理上传的文件
            file_contents = []
            if uploaded_files:
                from .file_processors import process_uploaded_files
                processed_files = process_uploaded_files(uploaded_files)
                
                for file_info in processed_files:
                    file_contents.append({
                        'filename': file_info['filename'],
                        'content': file_info['content'],
                        'file_type': file_info['file_type'],
                        'preview': file_info['preview']
                    })
            
            # 创建请求日志
            request_log = self._create_request_log(
                request, 
                'answer', 
                f"问题: {problem}\n文件: {len(uploaded_files)} 个"
            )
            
            # 保存上传的文件到数据库
            from .models import UploadedFile
            uploaded_file_records = []
            for i, file in enumerate(uploaded_files):
                file_record = UploadedFile.objects.create(
                    request_log=request_log,
                    original_filename=file.name,
                    file_type=file.content_type,
                    file_size=file.size,
                    file_content=file_contents[i]['content'] if i < len(file_contents) else ''
                )
                uploaded_file_records.append(file_record)
            
            # 返回会话ID和初始状态，前端将使用这个ID来获取流式更新
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'request_log_id': str(request_log.id),
                'files_processed': len(uploaded_files),
                'message': '开始处理请求...'
            })
            
        except Exception as e:
            logger.error("处理流式问题解答请求时出错: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerHistoryAPIView(BaseAPIView):
    """作业求解历史记录API"""
    
    def get(self, request):
        """获取历史记录列表"""
        try:
            session_id = self._get_session_id(request)
            
            # 获取作业求解类型的历史记录
            history_records = RequestLog.objects.filter(
                session_id=session_id,
                request_type='answer'
            ).order_by('-created_at')[:20]  # 最近20条
            
            history_data = []
            for record in history_records:
                # 获取解决方案
                solutions = []
                for solution in record.solutions.all():
                    solutions.append({
                        'title': solution.title,
                        'code': solution.code,
                        'explanation': solution.explanation,
                        'filename': solution.filename
                    })
                
                # 获取上传文件
                uploaded_files = []
                for file in record.uploadedfile_set.all():
                    uploaded_files.append({
                        'filename': file.original_filename,
                        'file_type': file.file_type,
                        'file_size': file.file_size
                    })
                
                history_data.append({
                    'id': str(record.id),
                    'input_content': record.input_content,
                    'created_at': record.created_at.isoformat(),
                    'success': record.success,
                    'processing_time': record.processing_time,
                    'solutions': solutions,
                    'uploaded_files': uploaded_files
                })
            
            return JsonResponse({
                'success': True,
                'history': history_data
            })
            
        except Exception as e:
            logger.error("获取历史记录失败: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '获取历史记录失败'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerHistoryDetailAPIView(BaseAPIView):
    """历史记录详情API"""
    
    def get(self, request, record_id):
        """获取单条历史记录详情"""
        try:
            session_id = self._get_session_id(request)
            
            record = RequestLog.objects.get(
                id=record_id,
                session_id=session_id,
                request_type='answer'
            )
            
            # 获取解决方案
            solutions = []
            for solution in record.solutions.all():
                solutions.append({
                    'title': solution.title,
                    'code': solution.code,
                    'explanation': solution.explanation,
                    'filename': solution.filename
                })
            
            # 获取上传文件
            uploaded_files = []
            for file in record.uploadedfile_set.all():
                uploaded_files.append({
                    'filename': file.original_filename,
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'content': file.file_content[:1000] if file.file_content else ''  # 限制内容长度
                })
            
            record_data = {
                'id': str(record.id),
                'input_content': record.input_content,
                'response_content': record.response_content,
                'created_at': record.created_at.isoformat(),
                'success': record.success,
                'processing_time': record.processing_time,
                'error_message': record.error_message,
                'solutions': solutions,
                'uploaded_files': uploaded_files
            }
            
            return JsonResponse({
                'success': True,
                'record': record_data
            })
            
        except RequestLog.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '历史记录不存在'
            }, status=404)
        except Exception as e:
            logger.error("获取历史记录详情失败: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '获取历史记录详情失败'
            }, status=500)
    
    def delete(self, request, record_id):
        """删除单条历史记录"""
        try:
            session_id = self._get_session_id(request)
            
            record = RequestLog.objects.get(
                id=record_id,
                session_id=session_id,
                request_type='answer'
            )
            
            record.delete()
            
            return JsonResponse({
                'success': True,
                'message': '历史记录已删除'
            })
            
        except RequestLog.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '历史记录不存在'
            }, status=404)
        except Exception as e:
            logger.error("删除历史记录失败: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '删除历史记录失败'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ClearHistoryAPIView(BaseAPIView):
    """清空历史记录API"""
    
    def post(self, request):
        """清空历史记录"""
        try:
            data = json.loads(request.body)
            clear_type = data.get('type', 'session')  # 'session' 或 'all'
            
            session_id = self._get_session_id(request)
            
            if clear_type == 'session':
                # 只清空当前会话的记录
                deleted_count = RequestLog.objects.filter(
                    session_id=session_id,
                    request_type='answer'
                ).delete()[0]
            elif clear_type == 'all':
                # 清空所有记录（仅限当前会话的所有类型）
                deleted_count = RequestLog.objects.filter(
                    session_id=session_id
                ).delete()[0]
            else:
                return JsonResponse({
                    'success': False,
                    'error': '无效的清空类型'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': f'已清空 {deleted_count} 条记录'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '请求数据格式错误'
            }, status=400)
        except Exception as e:
            logger.error("清空历史记录失败: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '清空历史记录失败'
            }, status=500)
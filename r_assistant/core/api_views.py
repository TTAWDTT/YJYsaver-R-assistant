"""
智能对话和其他API视图
"""

import json
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone

from services.ai_service import ai_service, AIServiceError
from services.code_analyzer import code_analyzer
from .models import ConversationHistory, RequestLog, CodeAnalysis

logger = logging.getLogger(__name__)


class BaseAPIView:
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
            ip_address=self._get_client_ip(request)
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
                # 调用AI服务
                result = ai_service.chat(message, conversation_history)
                
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
            
            try:
                if analysis_type == 'quality':
                    # 静态代码分析
                    analysis_result = code_analyzer.analyze(code)
                    
                    # AI代码质量分析
                    ai_result = ai_service.analyze_code_quality(code)
                    
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
                    ai_result = ai_service.generate_tests(code)
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
                    ai_result = ai_service.optimize_code(code)
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
                test_result = ai_service.chat("test", [])
                if not test_result.get('content'):
                    ai_status = 'degraded'
            except Exception:
                ai_status = 'unavailable'
            
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'services': {
                    'database': 'available',
                    'ai_service': ai_status
                }
            })
            
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return JsonResponse({
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }, status=500)
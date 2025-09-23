"""
核心视图
处理主要的页面请求
"""

import json
import uuid
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db import models
from datetime import timedelta

from .models import RequestLog, CodeSolution, ConversationHistory, UserSession
from services.ai_service import ai_service, AIServiceError
from services.code_analyzer import code_analyzer

logger = logging.getLogger(__name__)


class IndexView(View):
    """首页视图"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示首页"""
        # 更新用户会话
        self._update_user_session(request)
        
        context = {
            'title': 'R语言智能助手',
            'description': '专业的R语言学习与开发助手'
        }
        return render(request, 'core/index.html', context)
    
    def _update_user_session(self, request: HttpRequest):
        """更新用户会话信息"""
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # 获取客户端信息
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # 更新或创建用户会话
        user_session, created = UserSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
                'last_activity': timezone.now()
            }
        )
        
        if not created:
            user_session.last_activity = timezone.now()
            user_session.save()
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ExplainView(View):
    """代码解释视图"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示代码解释页面"""
        context = {
            'title': '代码解释 - R语言智能助手',
            'page_type': 'explain'
        }
        return render(request, 'core/explain.html', context)


class AnswerView(View):
    """作业求解视图"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示作业求解页面"""
        context = {
            'title': '作业求解 - R语言智能助手',
            'page_type': 'answer'
        }
        return render(request, 'core/answer.html', context)


class TalkView(View):
    """智能对话视图"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示智能对话页面"""
        # 获取会话历史
        session_id = request.session.session_key
        if session_id:
            history = ConversationHistory.objects.filter(
                session_id=session_id
            ).order_by('timestamp')[:50]  # 限制历史记录数量
        else:
            history = []
        
        context = {
            'title': '智能对话 - R语言智能助手',
            'page_type': 'talk',
            'conversation_history': history
        }
        return render(request, 'core/talk.html', context)


class HistoryView(View):
    """历史记录视图"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示历史记录页面"""
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        # 获取用户的历史记录
        request_logs = RequestLog.objects.filter(
            session_id=session_id
        ).order_by('-created_at')[:50]
        
        context = {
            'title': '历史记录 - R语言智能助手',
            'request_logs': request_logs
        }
        return render(request, 'core/history.html', context)


class MonitorView(View):
    """性能监控视图（管理员）"""
    
    def get(self, request: HttpRequest) -> HttpResponse:
        """显示性能监控页面"""
        if not request.user.is_staff:
            return redirect('core:index')
        
        # 统计数据
        total_requests = RequestLog.objects.count()
        today_requests = RequestLog.objects.filter(
            created_at__gte=timezone.now().date()
        ).count()
        
        success_rate = 0
        if total_requests > 0:
            successful_requests = RequestLog.objects.filter(success=True).count()
            success_rate = (successful_requests / total_requests) * 100
        
        # 按类型统计
        request_types = RequestLog.objects.values('request_type').annotate(
            count=models.Count('id')
        )
        
        context = {
            'title': '性能监控 - R语言智能助手',
            'total_requests': total_requests,
            'today_requests': today_requests,
            'success_rate': round(success_rate, 2),
            'request_types': request_types
        }
        return render(request, 'core/monitor.html', context)


# API视图基类
class BaseAPIView(View):
    """API视图基类"""
    
    def _get_session_id(self, request: HttpRequest) -> str:
        """获取会话ID"""
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        return session_id
    
    def _create_request_log(self, request: HttpRequest, request_type: str, 
                          input_content: str) -> RequestLog:
        """创建请求日志"""
        session_id = self._get_session_id(request)
        
        return RequestLog.objects.create(
            session_id=session_id,
            request_type=request_type,
            input_content=input_content,
            user=request.user if request.user.is_authenticated else None
        )
    
    def _update_request_log(self, request_log: RequestLog, response_content: str, 
                          processing_time: float, success: bool = True, 
                          error_message: str = None):
        """更新请求日志"""
        request_log.response_content = response_content
        request_log.processing_time = processing_time
        request_log.success = success
        request_log.error_message = error_message
        request_log.save()
    
    def _parse_solution_response(self, response_content: str) -> list:
        """解析AI响应中的解决方案"""
        solutions = []
        
        # 简单的解析逻辑，实际项目中可能需要更复杂的解析
        # 这里假设AI返回的格式是固定的
        
        # 使用正则表达式或其他方法解析三个方案
        # 这是一个简化的实现
        import re
        
        # 查找方案标题
        solution_pattern = r'\*\*方案[一二三]：([^*]+)\*\*'
        code_pattern = r'```r\n(.*?)\n```'
        explanation_pattern = r'解释：([^\n]+)'
        
        titles = re.findall(solution_pattern, response_content)
        codes = re.findall(code_pattern, response_content, re.DOTALL)
        explanations = re.findall(explanation_pattern, response_content)
        
        for i in range(min(len(titles), len(codes), 3)):
            solutions.append({
                'solution_number': i + 1,
                'title': titles[i].strip(),
                'code': codes[i].strip(),
                'explanation': explanations[i].strip() if i < len(explanations) else '',
                'filename': f'solution{i + 1}.R'
            })
        
        return solutions


@method_decorator(csrf_exempt, name='dispatch')
class ExplainAPIView(BaseAPIView):
    """代码解释API"""
    
    @require_http_methods(["POST"])
    def post(self, request: HttpRequest) -> JsonResponse:
        """处理代码解释请求"""
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip()
            
            if not code:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要解释的代码'
                }, status=400)
            
            # 创建请求日志
            request_log = self._create_request_log(request, 'explain', code)
            
            try:
                # 调用AI服务
                result = ai_service.explain_code(code)
                
                # 更新请求日志
                self._update_request_log(
                    request_log, 
                    result['content'], 
                    result['processing_time']
                )
                
                logger.info("Code explanation completed for session %s", request_log.session_id)
                
                return JsonResponse({
                    'success': True,
                    'explanation': result['content'],
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
                
                logger.error("AI service error in code explanation: %s", str(e))
                
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
            logger.error("Unexpected error in code explanation: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerAPIView(BaseAPIView):
    """作业求解API"""
    
    @require_http_methods(["POST"])
    def post(self, request: HttpRequest) -> JsonResponse:
        """处理作业求解请求"""
        try:
            data = json.loads(request.body)
            problem = data.get('problem', '').strip()
            
            if not problem:
                return JsonResponse({
                    'success': False,
                    'error': '请提供要解决的问题'
                }, status=400)
            
            # 创建请求日志
            request_log = self._create_request_log(request, 'answer', problem)
            
            try:
                # 调用AI服务
                result = ai_service.solve_problem(problem)
                
                # 解析解决方案
                solutions = self._parse_solution_response(result['content'])
                
                # 保存解决方案
                for solution_data in solutions:
                    CodeSolution.objects.create(
                        request_log=request_log,
                        **solution_data
                    )
                
                # 更新请求日志
                self._update_request_log(
                    request_log, 
                    result['content'], 
                    result['processing_time']
                )
                
                logger.info("Problem solving completed for session %s", request_log.session_id)
                
                return JsonResponse({
                    'success': True,
                    'solutions': solutions,
                    'raw_response': result['content'],
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
                
                logger.error("Unexpected error in chat: %s", str(e))
                
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
            logger.error("Unexpected error in problem solving: %s", str(e))
            return JsonResponse({
                'success': False,
                'error': '服务器内部错误'
            }, status=500)
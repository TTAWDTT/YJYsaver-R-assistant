import json
import logging
import time
from datetime import datetime, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView, ListView
from django.views import View

from .models import RequestLog, CodeSolution, ConversationHistory, UserSession

logger = logging.getLogger(__name__)


def get_session_id(request):
    """获取或创建会话ID"""
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key
    return session_id


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def simple_ai_response(request_type, user_input):
    """简单的AI回复模拟，实际应用中应该调用真实的AI API"""
    
    if request_type == 'explain':
        return f"""
这段R代码的解释：

```r
{user_input}
```

基本功能分析：
1. 这段代码的主要目的是处理数据
2. 涉及的主要函数和操作
3. 代码执行流程
4. 可能的输出结果

注意事项：
- 确保数据格式正确
- 检查变量名拼写
- 注意函数参数的使用

建议优化：
- 可以添加错误处理
- 考虑代码的可读性
- 添加适当的注释

*注：这是一个演示回复，实际使用时请配置真实的AI API密钥*
"""
    
    elif request_type == 'answer':
        solutions = [
            {
                'title': '基础解决方案',
                'code': f'# 基于您的问题：{user_input}\n\n# 方案一：基础实现\nlibrary(ggplot2)\ndata <- read.csv("data.csv")\nresult <- summary(data)\nprint(result)',
                'explanation': '这是一个基础的解决方案，适用于初学者。使用了R语言的基本函数来处理数据。'
            },
            {
                'title': '进阶解决方案', 
                'code': f'# 方案二：进阶实现\nlibrary(dplyr)\nlibrary(ggplot2)\n\ndata %>%\n  filter(!is.na(value)) %>%\n  group_by(category) %>%\n  summarise(mean_val = mean(value)) %>%\n  ggplot(aes(x = category, y = mean_val)) +\n  geom_col()',
                'explanation': '这是一个更高级的解决方案，使用了tidyverse生态系统，代码更简洁易读。'
            },
            {
                'title': '专业解决方案',
                'code': f'# 方案三：专业实现\nlibrary(data.table)\nlibrary(plotly)\n\nDT <- fread("data.csv")\nresult <- DT[, .(mean_val = mean(value, na.rm = TRUE)), by = category]\np <- plot_ly(result, x = ~category, y = ~mean_val, type = "bar")\np',
                'explanation': '这是一个专业级的解决方案，使用了高性能的data.table包和交互式可视化。'
            }
        ]
        
        response = f"针对您的问题：{user_input}\n\n我为您提供三种解决方案：\n\n"
        for i, sol in enumerate(solutions, 1):
            response += f"**方案{i}：{sol['title']}**\n```r\n{sol['code']}\n```\n{sol['explanation']}\n\n"
        
        response += "*注：这是一个演示回复，实际使用时请配置真实的AI API密钥*"
        return response, solutions
    
    elif request_type == 'talk':
        return f"""
关于您提到的"{user_input}"，我来为您详细解答：

作为R语言助手，我可以帮助您：
- 解释R语言代码的功能和语法
- 提供数据分析的解决方案
- 回答R语言相关的学习问题
- 协助解决编程中遇到的问题

如果您有具体的R语言问题，欢迎继续提问！

*注：这是一个演示回复，实际使用时请配置真实的AI API密钥*
"""
    
    return "抱歉，我暂时无法处理这类请求。"


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
            ip_address=get_client_ip(request)
        )
    
    def _update_request_log(self, request_log, response_content='', processing_time=0, success=True, error_message=''):
        """更新请求日志"""
        request_log.response_content = response_content
        request_log.processing_time = processing_time
        request_log.success = success
        request_log.error_message = error_message
        request_log.save()


class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取或创建用户会话
        session_id = get_session_id(self.request)
            
        user_session, created = UserSession.objects.get_or_create(
            session_id=session_id,
            defaults={'created_at': timezone.now()}
        )
        
        # 更新最后访问时间
        user_session.last_accessed = timezone.now()
        user_session.save()
        
        # 获取统计信息
        context.update({
            'total_requests': RequestLog.objects.filter(session_id=session_id).count(),
            'successful_requests': RequestLog.objects.filter(
                session_id=session_id, 
                success=True
            ).count(),
            'recent_solutions': CodeSolution.objects.filter(
                request_log__session_id=session_id
            ).order_by('-created_at')[:3],
        })
        
        return context


class ExplainView(TemplateView):
    template_name = 'core/explain.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取会话ID
        session_id = get_session_id(self.request)
        
        # 获取最近的代码解释历史
        recent_explanations = RequestLog.objects.filter(
            session_id=session_id,
            request_type='explain'
        ).order_by('-created_at')[:5]
        
        context['recent_explanations'] = recent_explanations
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            r_code = request.POST.get('r_code', '').strip()
            
            if not r_code:
                return self.render_to_response(
                    self.get_context_data(error_message="请输入要解释的R代码")
                )
            
            # 获取会话ID
            session_id = get_session_id(request)
            
            # 记录开始时间
            start_time = time.time()
            
            # 创建请求日志
            request_log = RequestLog.objects.create(
                session_id=session_id,
                request_type='explain',
                input_content=r_code,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            try:
                # 调用简单AI回复
                explanation = simple_ai_response('explain', r_code)
                
                # 计算响应时间
                processing_time = time.time() - start_time
                
                # 更新请求日志
                request_log.response_content = explanation
                request_log.success = True
                request_log.processing_time = processing_time
                request_log.save()
                
                context = self.get_context_data()
                context.update({
                    'explanation_result': explanation,
                    'original_code': r_code,
                    'processing_time': processing_time
                })
                
                return self.render_to_response(context)
                
            except Exception as e:
                logger.error("处理代码解释时出错: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"解释代码时出现错误: {str(e)}"
                return self.render_to_response(context)
                
        except Exception as e:
            logger.error("处理代码解释请求时出错: %s", str(e))
            return self.render_to_response(
                self.get_context_data(error_message="系统错误，请稍后重试")
            )


class AnswerView(TemplateView):
    template_name = 'core/answer.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取会话ID
        session_id = get_session_id(self.request)
        
        # 获取最近的作业求解历史
        recent_solutions = RequestLog.objects.filter(
            session_id=session_id,
            request_type='answer'
        ).order_by('-created_at')[:5]
        
        context['recent_solutions'] = recent_solutions
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            problem = request.POST.get('problem', '').strip()
            
            if not problem:
                context = self.get_context_data()
                context['error_message'] = "请输入要求解的问题"
                return self.render_to_response(context)
            
            # 获取会话ID
            session_id = get_session_id(request)
            
            # 记录开始时间
            start_time = time.time()
            
            # 创建请求日志
            request_log = RequestLog.objects.create(
                session_id=session_id,
                request_type='answer',
                input_content=problem,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            try:
                # 调用简单AI回复，获取回复和解决方案
                response_content, solutions = simple_ai_response('answer', problem)
                
                # 计算响应时间
                processing_time = time.time() - start_time
                
                # 更新请求日志
                request_log.response_content = response_content
                request_log.success = True
                request_log.processing_time = processing_time
                request_log.save()
                
                # 创建代码解决方案记录
                for i, solution in enumerate(solutions):
                    CodeSolution.objects.create(
                        request_log=request_log,
                        solution_number=i + 1,
                        title=solution['title'],
                        code=solution['code'],
                        explanation=solution['explanation'],
                        filename=f'solution_{i+1}.R'
                    )
                
                context = self.get_context_data()
                context.update({
                    'answer_result': response_content,
                    'original_problem': problem,
                    'solutions': solutions,
                    'processing_time': processing_time
                })
                
                return self.render_to_response(context)
                
            except Exception as e:
                logger.error("处理问题求解时出错: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"求解问题时出现错误: {str(e)}"
                return self.render_to_response(context)
                
        except Exception as e:
            logger.error("处理问题求解请求时出错: %s", str(e))
            context = self.get_context_data()
            context['error_message'] = "系统错误，请稍后重试"
            return self.render_to_response(context)


class TalkView(TemplateView):
    template_name = 'core/talk.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取会话ID
        session_id = get_session_id(self.request)
        
        # 获取对话历史
        conversation_history = ConversationHistory.objects.filter(
            session_id=session_id
        ).order_by('timestamp')[:50]  # 限制显示最近50条
        
        context['conversation_history'] = conversation_history
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            message = request.POST.get('message', '').strip()
            
            if not message:
                return self.render_to_response(
                    self.get_context_data(error_message="请输入消息内容")
                )
            
            # 获取会话ID
            session_id = get_session_id(request)
            
            # 记录用户消息
            user_message = ConversationHistory.objects.create(
                session_id=session_id,
                role='user',
                content=message
            )
            
            # 记录开始时间
            start_time = time.time()
            
            # 创建请求日志
            request_log = RequestLog.objects.create(
                session_id=session_id,
                request_type='talk',
                input_content=message,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            try:
                # 调用简单AI回复
                response = simple_ai_response('talk', message)
                
                # 计算响应时间
                processing_time = time.time() - start_time
                
                # 记录AI回复
                ConversationHistory.objects.create(
                    session_id=session_id,
                    role='assistant',
                    content=response
                )
                
                # 更新请求日志
                request_log.response_content = response
                request_log.success = True
                request_log.processing_time = processing_time
                request_log.save()
                
                # 重定向到同一页面以刷新对话历史
                return redirect('core:talk')
                
            except Exception as e:
                logger.error("处理对话时出错: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"对话时出现错误: {str(e)}"
                return self.render_to_response(context)
                
        except Exception as e:
            logger.error("处理对话请求时出错: %s", str(e))
            return self.render_to_response(
                self.get_context_data(error_message="系统错误，请稍后重试")
            )


class HistoryView(ListView):
    model = RequestLog
    template_name = 'core/history.html'
    context_object_name = 'history_records'
    paginate_by = 10
    
    def get_queryset(self):
        # 获取会话ID
        session_id = get_session_id(self.request)
        
        queryset = RequestLog.objects.filter(session_id=session_id)
        
        # 筛选条件
        request_type = self.request.GET.get('request_type')
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        date_range = self.request.GET.get('date_range')
        if date_range:
            now = timezone.now()
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                queryset = queryset.filter(created_at__gte=start_date)
            elif date_range == 'week':
                start_date = now - timedelta(days=7)
                queryset = queryset.filter(created_at__gte=start_date)
            elif date_range == 'month':
                start_date = now - timedelta(days=30)
                queryset = queryset.filter(created_at__gte=start_date)
        
        return queryset.order_by('-created_at')


def clear_history(request):
    """清除对话历史"""
    if request.method == 'POST':
        session_id = get_session_id(request)
        ConversationHistory.objects.filter(session_id=session_id).delete()
        messages.success(request, '对话历史已清除')
    
    return redirect('core:talk')
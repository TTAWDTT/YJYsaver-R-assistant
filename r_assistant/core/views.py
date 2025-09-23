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
from services.langgraph_service import langgraph_service
from services.ai_service import AIServiceError

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
                # 使用LangGraph服务进行代码解释
                result = langgraph_service.explain_code(r_code, session_id)
                
                # 计算响应时间
                processing_time = result.get('processing_time', 0)
                
                # 更新请求日志
                request_log.response_content = result['content']
                request_log.success = result['success']
                request_log.processing_time = processing_time
                if not result['success']:
                    request_log.error_message = "LangGraph工作流执行失败"
                request_log.save()
                
                context = self.get_context_data()
                context.update({
                    'explanation': result['content'],
                    'original_code': r_code,
                    'processing_time': processing_time,
                    'workflow_metadata': result.get('metadata', {}),
                    'quality_score': result.get('metadata', {}).get('quality_score'),
                    'code_analysis': result.get('metadata', {}).get('code_analysis')
                })
                
                return self.render_to_response(context)
                
            except AIServiceError as e:
                logger.error("LangGraph代码解释失败: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"代码解释失败: {str(e)}"
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
            uploaded_files = request.FILES.getlist('uploaded_files')
            
            if not problem:
                context = self.get_context_data()
                context['error_message'] = "请输入要求解的问题"
                return self.render_to_response(context)
            
            # 验证上传文件
            if len(uploaded_files) > 5:
                context = self.get_context_data()
                context['error_message'] = "最多只能上传5个文件"
                return self.render_to_response(context)
            
            # 验证文件大小和类型
            max_file_size = 10 * 1024 * 1024  # 10MB
            allowed_extensions = ['csv', 'txt', 'xlsx', 'xls', 'r', 'rmd', 'json', 'xml', 'py', 'js', 'html', 'css']
            
            for uploaded_file in uploaded_files:
                if uploaded_file.size > max_file_size:
                    context = self.get_context_data()
                    context['error_message'] = f"文件 '{uploaded_file.name}' 大小超过10MB"
                    return self.render_to_response(context)
                
                file_ext = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
                if file_ext not in allowed_extensions:
                    context = self.get_context_data()
                    context['error_message'] = f"不支持的文件类型：{file_ext}"
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
            
            # 处理上传的文件
            file_contents = []
            for uploaded_file in uploaded_files:
                try:
                    # 读取文件内容
                    if uploaded_file.content_type.startswith('text/') or uploaded_file.name.endswith(('.csv', '.txt', '.r', '.rmd', '.json', '.xml', '.py', '.js', '.html', '.css')):
                        content = uploaded_file.read().decode('utf-8')
                    else:
                        content = f"[二进制文件: {uploaded_file.name}, 大小: {uploaded_file.size} 字节]"
                    
                    # 保存文件信息到数据库
                    file_type = self._get_file_type(uploaded_file.name)
                    from .models import UploadedFile
                    UploadedFile.objects.create(
                        request_log=request_log,
                        original_filename=uploaded_file.name,
                        file_type=file_type,
                        file_size=uploaded_file.size,
                        file_content=content,
                        mime_type=uploaded_file.content_type,
                        encoding='utf-8'
                    )
                    
                    file_contents.append({
                        'filename': uploaded_file.name,
                        'content': content,
                        'size': uploaded_file.size,
                        'type': file_type
                    })
                    
                except Exception as e:
                    logger.error(f"处理上传文件 {uploaded_file.name} 时出错: {str(e)}")
                    context = self.get_context_data()
                    context['error_message'] = f"处理文件 '{uploaded_file.name}' 时出错"
                    return self.render_to_response(context)
            
            try:
                # 使用LangGraph服务进行问题求解，包含文件内容
                result = langgraph_service.solve_problem(problem, session_id, uploaded_files=file_contents)
                
                # 计算响应时间
                processing_time = result.get('processing_time', 0)
                
                # 更新请求日志
                request_log.response_content = result['content']
                request_log.success = result['success']
                request_log.processing_time = processing_time
                if not result['success']:
                    request_log.error_message = "LangGraph工作流执行失败"
                request_log.save()
                
                # 保存解决方案到数据库
                solutions = result.get('solutions', [])
                for i, solution in enumerate(solutions):
                    CodeSolution.objects.create(
                        request_log=request_log,
                        solution_number=i + 1,
                        title=solution['title'],
                        code=solution['code'],
                        explanation=solution['explanation'],
                        filename=solution.get('filename', f'solution_{i+1}.R')
                    )
                
                context = self.get_context_data()
                context.update({
                    'answer_result': result['content'],
                    'original_problem': problem,
                    'solutions': solutions,
                    'processing_time': processing_time,
                    'workflow_metadata': result.get('metadata', {}),
                    'problem_type': result.get('metadata', {}).get('problem_type'),
                    'uploaded_files': request_log.uploaded_files.all() if uploaded_files else None
                })
                
                return self.render_to_response(context)
                
            except AIServiceError as e:
                logger.error("LangGraph问题求解失败: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"问题求解失败: {str(e)}"
                return self.render_to_response(context)
                
        except Exception as e:
            logger.error("处理问题求解请求时出错: %s", str(e))
            context = self.get_context_data()
            context['error_message'] = "系统错误，请稍后重试"
            return self.render_to_response(context)
    
    def _get_file_type(self, filename):
        """根据文件名确定文件类型"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        type_mapping = {
            'csv': 'csv',
            'txt': 'txt',
            'xlsx': 'xlsx',
            'xls': 'xlsx',
            'r': 'r',
            'rmd': 'rmd',
            'json': 'json',
            'xml': 'xml',
        }
        return type_mapping.get(ext, 'other')


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
                # 获取对话历史
                conversation_history = list(
                    ConversationHistory.objects.filter(
                        session_id=session_id
                    ).order_by('-timestamp').values('role', 'content')[:10]  # 最近10条
                )
                # 反转顺序，使最早的消息在前面
                conversation_history.reverse()
                
                # 使用LangGraph服务进行智能对话
                result = langgraph_service.chat(message, conversation_history, session_id)
                
                # 计算响应时间
                processing_time = result.get('processing_time', 0)
                
                # 保存AI回复
                ai_response = result['content']
                ConversationHistory.objects.create(
                    session_id=session_id,
                    role='assistant',
                    content=ai_response
                )
                
                # 更新请求日志
                request_log.response_content = ai_response
                request_log.success = result['success']
                request_log.processing_time = processing_time
                if not result['success']:
                    request_log.error_message = "LangGraph工作流执行失败"
                request_log.save()
                
                # 重定向到同一页面以刷新对话历史
                return redirect('core:talk')
                
            except AIServiceError as e:
                logger.error("LangGraph智能对话失败: %s", str(e))
                
                # 更新请求日志
                request_log.success = False
                request_log.error_message = str(e)
                request_log.processing_time = time.time() - start_time
                request_log.save()
                
                context = self.get_context_data()
                context['error_message'] = f"智能对话失败: {str(e)}"
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
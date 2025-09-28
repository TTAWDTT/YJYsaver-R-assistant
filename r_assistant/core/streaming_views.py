import json
import logging
import asyncio
import time
from datetime import datetime
from django.http import StreamingHttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from .models import RequestLog, CodeSolution, UploadedFile
from .views import get_session_id, get_client_ip
from services.langgraph_service import langgraph_service
from services.ai_service import AIServiceError

logger = logging.getLogger(__name__)


# 全局存储流式数据（在生产环境中应使用Redis等）
streaming_data = {}


def stream_updates(request, session_id):
    """SSE流式更新端点"""
    
    def event_generator():
        # 发送连接确认事件
        yield f"data: {json.dumps({'type': 'connected', 'message': '连接已建立'})}\n"
        
        # 模拟发送一些更新
        try:
            # 这里应该从某个地方获取实际的流式数据
            # 由于这是一个简化的实现，我们发送一些模拟数据
            yield f"data: {json.dumps({'type': 'progress', 'progress': 30, 'message': '正在分析问题...'})}\n"
            time.sleep(1)
            
            yield f"data: {json.dumps({'type': 'progress', 'progress': 50, 'message': '正在生成解决方案...'})}\n"
            time.sleep(1)
            
            # 发送一个模拟的解决方案
            solution = {
                'number': 1,
                'title': '基础解决方案',
                'code': '# 基础R代码示例\nlibrary(ggplot2)\ndata(mtcars)\nhead(mtcars)',
                'explanation': '<p>这是一个基础的R代码解决方案，展示了如何加载ggplot2包并查看mtcars数据集的前几行。</p>'
            }
            yield f"data: {json.dumps({'type': 'solution', 'solution': solution})}\n"
            time.sleep(1)
            
            yield f"data: {json.dumps({'type': 'progress', 'progress': 80, 'message': '正在优化代码...'})}\n"
            time.sleep(1)
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'complete', 'message': '所有解决方案生成完成'})}\n"
            
        except Exception as e:
            logger.error(f"流式更新出错: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': '流式更新出错'})}\n"
    
    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


class StreamingResponseMixin:
    """流式响应混入类"""
    
    def create_sse_response(self, generator):
        """创建SSE流式响应"""
        # Use the proper SSE content type and avoid setting hop-by-hop headers
        response = StreamingHttpResponse(
            generator,
            content_type='text/event-stream; charset=utf-8'
        )
        # Prevent caching and disable proxy buffering. Do NOT set 'Connection' header
        # because WSGI / Django will reject hop-by-hop headers.
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲
        return response
    
    def format_sse_data(self, data_type, data):
        """格式化SSE数据"""
        return f"data: {json.dumps({'type': data_type, 'data': data}, ensure_ascii=False)}\n\n"


@method_decorator(csrf_exempt, name='dispatch')
class StreamingExplainView(View, StreamingResponseMixin):
    """流式代码解释视图"""
    
    def post(self, request):
        try:
            # 解析请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                code = data.get('code', '').strip()
            else:
                code = request.POST.get('code', '').strip()
            
            if not code:
                return JsonResponse({'error': '请输入要解释的代码'}, status=400)
            
            # 获取会话信息
            session_id = get_session_id(request)
            
            # 创建流式响应生成器
            def explain_generator():
                try:
                    # 发送开始事件
                    yield self.format_sse_data('start', {
                        'message': '开始分析代码...',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 创建请求日志
                    request_log = RequestLog.objects.create(
                        session_id=session_id,
                        request_type='explain',
                        input_content=code,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在分析代码结构...',
                        'step': 1,
                        'total': 4
                    })
                    
                    # 执行代码解释
                    start_time = time.time()
                    
                    # 这里应该调用异步的解释服务
                    # 由于当前服务是同步的，我们需要适配
                    def run_async_explain():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                langgraph_service.workflow_engine.execute_workflow(
                                    request_type="explain",
                                    user_input=code,
                                    session_id=session_id
                                )
                            )
                        finally:
                            loop.close()
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在生成详细解释...',
                        'step': 2,
                        'total': 4
                    })
                    
                    # 执行解释
                    result = run_async_explain()
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在优化展示格式...',
                        'step': 3,
                        'total': 4
                    })
                    
                    # 处理结果
                    processing_time = time.time() - start_time
                    success = result.get('status') == 'success'
                    
                    # 更新请求日志
                    request_log.response_content = result.get('explanation_result', '') or result.get('ai_response', '')
                    request_log.success = success
                    request_log.processing_time = processing_time
                    if not success:
                        request_log.error_message = '; '.join(result.get('errors', []))
                    request_log.save()
                    
                    yield self.format_sse_data('progress', {
                        'message': '解释完成!',
                        'step': 4,
                        'total': 4
                    })
                    
                    # 发送最终结果
                    yield self.format_sse_data('result', {
                        'success': success,
                        'explanation': result.get('explanation_result', '') or result.get('ai_response', ''),
                        'analysis': result.get('code_analysis', {}),
                        'complexity': result.get('complexity_analysis', {}),
                        'quality_score': result.get('quality_score'),
                        'processing_time': processing_time,
                        'total_tokens': result.get('total_tokens', 0),
                        'processing_steps': result.get('processing_steps', []),
                        'warnings': result.get('warnings', []),
                        'errors': result.get('errors', [])
                    })
                    
                    # 发送完成事件
                    yield self.format_sse_data('complete', {
                        'message': '代码解释完成',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"流式代码解释失败: {str(e)}")
                    yield self.format_sse_data('error', {
                        'message': f'解释失败: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return self.create_sse_response(explain_generator())
            
        except Exception as e:
            logger.error(f"处理流式解释请求失败: {str(e)}")
            return JsonResponse({'error': '系统错误，请稍后重试'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StreamingAnswerView(View, StreamingResponseMixin):
    """流式作业求解视图"""
    
    def post(self, request):
        try:
            # 解析请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                problem = data.get('problem', '').strip()
                uploaded_files = data.get('uploaded_files', [])
            else:
                problem = request.POST.get('problem', '').strip()
                uploaded_files = request.FILES.getlist('uploaded_files')
            
            if not problem:
                return JsonResponse({'error': '请输入要求解的问题'}, status=400)
            
            # 获取会话信息
            session_id = get_session_id(request)
            
            # 创建流式响应生成器
            def solve_generator():
                try:
                    # 发送开始事件
                    yield self.format_sse_data('start', {
                        'message': '开始分析问题...',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 创建请求日志
                    request_log = RequestLog.objects.create(
                        session_id=session_id,
                        request_type='answer',
                        input_content=problem,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在理解问题需求...',
                        'step': 1,
                        'total': 6
                    })
                    
                    # 处理上传文件
                    file_contents = []
                    if uploaded_files:
                        yield self.format_sse_data('progress', {
                            'message': '正在处理上传的文件...',
                            'step': 2,
                            'total': 6
                        })
                        
                        # 这里需要处理文件，暂时简化
                        # 实际应该调用文件处理逻辑
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在生成解决方案...',
                        'step': 3,
                        'total': 6
                    })
                    
                    # 执行问题求解
                    start_time = time.time()
                    
                    def run_async_solve():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                langgraph_service.workflow_engine.execute_workflow(
                                    request_type="answer",
                                    user_input=problem,
                                    session_id=session_id
                                )
                            )
                        finally:
                            loop.close()
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在优化代码解决方案...',
                        'step': 4,
                        'total': 6
                    })
                    
                    # 执行求解
                    result = run_async_solve()
                    
                    yield self.format_sse_data('progress', {
                        'message': '正在验证解决方案...',
                        'step': 5,
                        'total': 6
                    })
                    
                    # 处理结果
                    processing_time = time.time() - start_time
                    success = result.get('status') == 'success'
                    
                    # 保存解决方案到数据库
                    solutions = result.get('code_solutions', [])
                    formatted_solutions = []
                    
                    for i, solution in enumerate(solutions):
                        # 保存到数据库
                        db_solution = CodeSolution.objects.create(
                            request_log=request_log,
                            solution_number=i + 1,
                            title=solution.title,
                            code=solution.code,
                            explanation=solution.explanation,
                            filename=getattr(solution, 'filename', f'solution_{i+1}.R')
                        )
                        
                        formatted_solutions.append({
                            'title': solution.title,
                            'code': solution.code,
                            'explanation': solution.explanation,
                            'filename': getattr(solution, 'filename', f'solution_{i+1}.R')
                        })
                    
                    # 更新请求日志
                    request_log.response_content = result.get('ai_response', '')
                    request_log.success = success
                    request_log.processing_time = processing_time
                    if not success:
                        request_log.error_message = '; '.join(result.get('errors', []))
                    request_log.save()
                    
                    yield self.format_sse_data('progress', {
                        'message': '求解完成!',
                        'step': 6,
                        'total': 6
                    })
                    
                    # 发送最终结果
                    yield self.format_sse_data('result', {
                        'success': success,
                        'answer_result': result.get('ai_response', ''),
                        'solutions': formatted_solutions,
                        'processing_time': processing_time,
                        'total_tokens': result.get('total_tokens', 0),
                        'processing_steps': result.get('processing_steps', []),
                        'warnings': result.get('warnings', []),
                        'errors': result.get('errors', []),
                        'problem_type': result.get('problem_type')
                    })
                    
                    # 发送完成事件
                    yield self.format_sse_data('complete', {
                        'message': '问题求解完成',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"流式问题求解失败: {str(e)}")
                    yield self.format_sse_data('error', {
                        'message': f'求解失败: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return self.create_sse_response(solve_generator())
            
        except Exception as e:
            logger.error(f"处理流式求解请求失败: {str(e)}")
            return JsonResponse({'error': '系统错误，请稍后重试'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StreamingTalkView(View, StreamingResponseMixin):
    """简化的流式智能对话视图"""
    
    def post(self, request):
        try:
            # 解析请求数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                message = data.get('message', '').strip()
                conversation_history = data.get('history', [])
            else:
                message = request.POST.get('message', '').strip()
                conversation_history = []
            
            if not message:
                return JsonResponse({'error': '请输入消息'}, status=400)
            
            # 获取会话信息
            session_id = get_session_id(request)
            
            # 创建流式响应生成器
            def talk_generator():
                try:
                    # 发送开始事件
                    yield self.format_sse_data('start', {
                        'message': '正在思考...',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # 创建请求日志
                    request_log = RequestLog.objects.create(
                        session_id=session_id,
                        request_type='talk',
                        input_content=message,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    # 执行对话
                    start_time = time.time()
                    
                    def run_async_talk():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            return loop.run_until_complete(
                                langgraph_service.workflow_engine.execute_workflow(
                                    request_type="talk",
                                    user_input=message,
                                    session_id=session_id
                                )
                            )
                        finally:
                            loop.close()
                    
                    # 执行对话
                    result = run_async_talk()
                    
                    # 处理结果
                    processing_time = time.time() - start_time
                    success = result.get('status') == 'success'
                    ai_response = result.get('ai_response', '')
                    
                    # 更新请求日志
                    request_log.response_content = ai_response
                    request_log.success = success
                    request_log.processing_time = processing_time
                    if not success:
                        request_log.error_message = '; '.join(result.get('errors', []))
                    request_log.save()
                    
                    # 发送回复（模拟逐字输出）
                    if ai_response:
                        words = ai_response.split()
                        current_text = ""
                        for i, word in enumerate(words):
                            current_text += word + " "
                            yield self.format_sse_data('message_chunk', {
                                'text': current_text.strip(),
                                'is_complete': i == len(words) - 1
                            })
                            # 稍微延迟以模拟打字效果
                            time.sleep(0.05)
                    
                    # 发送最终结果
                    yield self.format_sse_data('result', {
                        'success': success,
                        'response': ai_response,
                        'processing_time': processing_time,
                        'total_tokens': result.get('total_tokens', 0)
                    })
                    
                    # 发送完成事件
                    yield self.format_sse_data('complete', {
                        'message': '对话完成',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"流式对话失败: {str(e)}")
                    yield self.format_sse_data('error', {
                        'message': f'对话失败: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
            
            return self.create_sse_response(talk_generator())
            
        except Exception as e:
            logger.error(f"处理流式对话请求失败: {str(e)}")
            return JsonResponse({'error': '系统错误，请稍后重试'}, status=500)
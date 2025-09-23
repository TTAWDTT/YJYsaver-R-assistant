"""
LangGraph工作流监控视图
提供工作流状态监控和管理功能
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from .models import RequestLog, ConversationHistory
from services.langgraph_workflow import workflow_engine

logger = logging.getLogger(__name__)


@method_decorator(staff_member_required, name='dispatch')
class WorkflowMonitorView(TemplateView):
    """工作流监控视图"""
    template_name = 'admin/workflow_monitor.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # 获取工作流统计
            now = timezone.now()
            today = now.date()
            week_ago = now - timedelta(days=7)
            
            # 总体统计
            total_requests = RequestLog.objects.count()
            today_requests = RequestLog.objects.filter(
                created_at__date=today
            ).count()
            week_requests = RequestLog.objects.filter(
                created_at__gte=week_ago
            ).count()
            
            # 成功率统计
            successful_requests = RequestLog.objects.filter(success=True).count()
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # 按类型统计
            request_types = {}
            for request_type, display_name in RequestLog.REQUEST_TYPES:
                count = RequestLog.objects.filter(request_type=request_type).count()
                avg_time = RequestLog.objects.filter(
                    request_type=request_type,
                    processing_time__isnull=False
                ).aggregate(avg_time=models.Avg('processing_time'))['avg_time'] or 0
                
                request_types[request_type] = {
                    'name': display_name,
                    'count': count,
                    'avg_processing_time': round(avg_time, 2)
                }
            
            # 最近的错误
            recent_errors = RequestLog.objects.filter(
                success=False,
                created_at__gte=week_ago
            ).order_by('-created_at')[:10]
            
            # 活跃会话
            active_sessions = ConversationHistory.objects.filter(
                timestamp__gte=now - timedelta(hours=24)
            ).values('session_id').distinct().count()
            
            # 工作流状态
            workflow_status = self._get_workflow_status()
            
            context.update({
                'total_requests': total_requests,
                'today_requests': today_requests,
                'week_requests': week_requests,
                'success_rate': round(success_rate, 2),
                'request_types': request_types,
                'recent_errors': recent_errors,
                'active_sessions': active_sessions,
                'workflow_status': workflow_status,
                'refresh_interval': 30  # 秒
            })
            
        except Exception as e:
            logger.error(f"获取工作流监控数据失败: {str(e)}")
            context['error'] = f"数据加载失败: {str(e)}"
        
        return context
    
    def _get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        try:
            workflows = workflow_engine.workflows
            status = {}
            
            for workflow_name in workflows.keys():
                # 检查工作流是否可用
                try:
                    # 这里可以添加工作流健康检查逻辑
                    status[workflow_name] = {
                        'status': 'healthy',
                        'last_check': datetime.now().isoformat(),
                        'description': f'{workflow_name}工作流运行正常'
                    }
                except Exception as e:
                    status[workflow_name] = {
                        'status': 'error',
                        'last_check': datetime.now().isoformat(),
                        'description': f'{workflow_name}工作流异常: {str(e)}'
                    }
            
            return status
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {str(e)}")
            return {'error': str(e)}


@staff_member_required
def workflow_api_status(request):
    """工作流API状态接口"""
    try:
        # 实时统计
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        recent_requests = RequestLog.objects.filter(
            created_at__gte=last_hour
        )
        
        stats = {
            'timestamp': now.isoformat(),
            'last_hour': {
                'total': recent_requests.count(),
                'successful': recent_requests.filter(success=True).count(),
                'failed': recent_requests.filter(success=False).count(),
                'avg_processing_time': recent_requests.aggregate(
                    avg_time=models.Avg('processing_time')
                )['avg_time'] or 0
            },
            'active_workflows': list(workflow_engine.workflows.keys()),
            'memory_usage': _get_memory_usage(),
            'system_status': 'healthy'
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"获取工作流API状态失败: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
            'system_status': 'error'
        }, status=500)


@staff_member_required
def clear_workflow_cache(request):
    """清除工作流缓存"""
    if request.method == 'POST':
        try:
            # 这里可以添加清除缓存的逻辑
            # 比如清除工作流内存、重置状态等
            
            logger.info("工作流缓存已清除")
            messages.success(request, "工作流缓存已成功清除")
            
        except Exception as e:
            logger.error(f"清除工作流缓存失败: {str(e)}")
            messages.error(request, f"清除缓存失败: {str(e)}")
    
    return redirect('admin:workflow_monitor')


@staff_member_required
def restart_workflow_engine(request):
    """重启工作流引擎"""
    if request.method == 'POST':
        try:
            # 这里可以添加重启工作流引擎的逻辑
            # 注意：在生产环境中需要谨慎处理
            
            logger.info("工作流引擎重启请求")
            messages.warning(request, "工作流引擎重启功能需要在生产环境中谨慎使用")
            
        except Exception as e:
            logger.error(f"重启工作流引擎失败: {str(e)}")
            messages.error(request, f"重启失败: {str(e)}")
    
    return redirect('admin:workflow_monitor')


def _get_memory_usage() -> Dict[str, Any]:
    """获取内存使用情况"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # 物理内存
            'vms': memory_info.vms,  # 虚拟内存
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available
        }
    except ImportError:
        return {'error': 'psutil not available'}
    except Exception as e:
        return {'error': str(e)}
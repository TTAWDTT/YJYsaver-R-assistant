"""
Core app URL configuration
"""

from django.urls import path
from . import views
from . import workflow_monitor
from . import api_views

app_name = 'core'

urlpatterns = [
    # Page routes
    path('', views.IndexView.as_view(), name='index'),
    path('explain/', views.ExplainView.as_view(), name='explain'),
    path('answer/', views.AnswerView.as_view(), name='answer'),
    path('talk/', views.TalkView.as_view(), name='talk'),
    path('history/', views.HistoryView.as_view(), name='history'),
    
    # API endpoints  
    path('api/explain/', api_views.ExplainAPIView.as_view(), name='api_explain'),
    path('api/answer/', api_views.AnswerAPIView.as_view(), name='api_answer'),
    path('api/answer/stream/', api_views.AnswerStreamAPIView.as_view(), name='answer_stream'),
    path('api/talk/', api_views.TalkAPIView.as_view(), name='api_talk'),
    
    # History API endpoints
    path('api/history/answer/', api_views.AnswerHistoryAPIView.as_view(), name='api_answer_history'),
    path('api/history/answer/<uuid:record_id>/', api_views.AnswerHistoryDetailAPIView.as_view(), name='api_answer_history_detail'),
    path('api/history/clear/', api_views.ClearHistoryAPIView.as_view(), name='api_clear_history'),
    
    # Functional operations
    path('clear-history/', views.clear_history, name='clear_history'),
    
    # Workflow monitoring (admin only)
    path('admin/workflow-monitor/', workflow_monitor.WorkflowMonitorView.as_view(), name='workflow_monitor'),
    path('admin/workflow-status/', workflow_monitor.workflow_api_status, name='workflow_api_status'),
    path('admin/clear-cache/', workflow_monitor.clear_workflow_cache, name='clear_workflow_cache'),
    path('admin/restart-engine/', workflow_monitor.restart_workflow_engine, name='restart_workflow_engine'),
]
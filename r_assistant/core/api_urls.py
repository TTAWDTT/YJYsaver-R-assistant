"""
API URL配置
"""

from django.urls import path
from . import views, api_views

app_name = 'api'

urlpatterns = [
    # API路由
    path('explain/', views.ExplainAPIView.as_view(), name='explain'),
    path('answer/', views.AnswerAPIView.as_view(), name='answer'),
    path('talk/', api_views.TalkAPIView.as_view(), name='talk'),
    path('analyze/', api_views.AnalyzeAPIView.as_view(), name='analyze'),
    path('clear-history/', api_views.ClearHistoryAPIView.as_view(), name='clear_history'),
    path('health/', api_views.HealthCheckAPIView.as_view(), name='health'),
]
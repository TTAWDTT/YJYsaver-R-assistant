"""
Core app URL configuration
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Page routes
    path('', views.IndexView.as_view(), name='index'),
    path('explain/', views.ExplainView.as_view(), name='explain'),
    path('answer/', views.AnswerView.as_view(), name='answer'),
    path('talk/', views.TalkView.as_view(), name='talk'),
    path('history/', views.HistoryView.as_view(), name='history'),
    
    # Functional operations
    path('clear-history/', views.clear_history, name='clear_history'),
]
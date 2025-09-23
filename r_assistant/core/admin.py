"""Admin configuration for core models."""
from django.contrib import admin
from .models import (
    RequestLog, CodeSolution, ConversationHistory, 
    UserSession, PerformanceMetric, CodeAnalysis
)


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    """Admin view for RequestLog model."""
    list_display = ['id', 'request_type', 'user', 'success', 'processing_time', 'created_at']
    list_filter = ['request_type', 'success', 'created_at']
    search_fields = ['user__username', 'input_content']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(CodeSolution)
class CodeSolutionAdmin(admin.ModelAdmin):
    """Admin view for CodeSolution model."""
    list_display = ['title', 'solution_number', 'request_log', 'created_at']
    list_filter = ['solution_number', 'created_at']
    search_fields = ['title', 'code', 'explanation']
    readonly_fields = ['id', 'created_at']


@admin.register(ConversationHistory)
class ConversationHistoryAdmin(admin.ModelAdmin):
    """Admin view for ConversationHistory model."""
    list_display = ['session_id', 'role', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['session_id', 'content']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin view for UserSession model."""
    list_display = ['session_id', 'user', 'ip_address', 'last_activity', 'created_at']
    list_filter = ['last_activity', 'created_at']
    search_fields = ['session_id', 'user__username', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-last_activity']


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    """Admin view for PerformanceMetric model."""
    list_display = ['metric_name', 'metric_type', 'value', 'unit', 'timestamp']
    list_filter = ['metric_type', 'timestamp']
    search_fields = ['metric_name']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']


@admin.register(CodeAnalysis)
class CodeAnalysisAdmin(admin.ModelAdmin):
    """Admin view for CodeAnalysis model."""
    list_display = ['analysis_type', 'score', 'request_log', 'created_at']
    list_filter = ['analysis_type', 'created_at']
    search_fields = ['suggestions']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
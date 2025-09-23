from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class RequestLog(models.Model):
    """请求日志模型"""
    REQUEST_TYPES = [
        ('explain', '代码解释'),
        ('answer', '作业求解'),
        ('talk', '智能对话'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    input_content = models.TextField()
    response_content = models.TextField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # 处理时间（秒）
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # 添加IP地址字段
    user_agent = models.TextField(null=True, blank=True)  # 添加用户代理字段
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'request_logs'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class CodeSolution(models.Model):
    """代码解决方案模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.ForeignKey(RequestLog, on_delete=models.CASCADE, related_name='solutions')
    solution_number = models.IntegerField()  # 方案序号（1, 2, 3）
    title = models.CharField(max_length=255)
    code = models.TextField()
    explanation = models.TextField()
    filename = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'code_solutions'
        ordering = ['solution_number']
        unique_together = ['request_log', 'solution_number']
        
    def __str__(self):
        return f"{self.title} - 方案{self.solution_number}"


class ConversationHistory(models.Model):
    """对话历史模型"""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI助手'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'conversation_history'
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.get_role_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class UserSession(models.Model):
    """用户会话模型"""
    session_id = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
        
    def __str__(self):
        return f"Session {self.session_id[:8]}... - {self.last_activity.strftime('%Y-%m-%d %H:%M')}"


class UploadedFile(models.Model):
    """上传文件模型"""
    FILE_TYPES = [
        ('csv', 'CSV文件'),
        ('txt', '文本文件'),
        ('xlsx', 'Excel文件'),
        ('r', 'R脚本'),
        ('rmd', 'R Markdown'),
        ('json', 'JSON文件'),
        ('xml', 'XML文件'),
        ('other', '其他'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.ForeignKey(RequestLog, on_delete=models.CASCADE, related_name='uploaded_files')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.BigIntegerField()  # 文件大小（字节）
    file_content = models.TextField()  # 存储文件内容
    file_path = models.CharField(max_length=500, null=True, blank=True)  # 文件路径（如果保存到磁盘）
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    encoding = models.CharField(max_length=50, default='utf-8')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'uploaded_files'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.original_filename} ({self.get_file_type_display()})"
    
    def get_file_extension(self):
        """获取文件扩展名"""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''
    
    def is_text_file(self):
        """判断是否为文本文件"""
        text_extensions = ['txt', 'csv', 'r', 'rmd', 'json', 'xml', 'py', 'js', 'html', 'css']
        return self.get_file_extension() in text_extensions


class PerformanceMetric(models.Model):
    """性能指标模型"""
    METRIC_TYPES = [
        ('api_call', 'API调用'),
        ('response_time', '响应时间'),
        ('error_rate', '错误率'),
        ('user_activity', '用户活动'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=255)
    value = models.FloatField()
    unit = models.CharField(max_length=50, null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)  # 额外的上下文信息
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'performance_metrics'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit or ''}"


class CodeAnalysis(models.Model):
    """代码分析结果模型"""
    ANALYSIS_TYPES = [
        ('quality', '代码质量'),
        ('complexity', '复杂度分析'),
        ('optimization', '优化建议'),
        ('testing', '测试建议'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.ForeignKey(RequestLog, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)
    score = models.FloatField(null=True, blank=True)  # 分数（0-100）
    details = models.JSONField(default=dict)  # 详细分析结果
    suggestions = models.TextField(null=True, blank=True)  # 改进建议
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'code_analyses'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.score or 'N/A'}"
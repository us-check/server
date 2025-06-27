from django.db import models
from django.contrib.auth.models import User

class QRCode(models.Model):
    """QR 코드 정보 모델"""
    
    QR_TYPE_CHOICES = [
        ('tourism_selection', '관광지 선택'),
        ('user_profile', '사용자 프로필'),
        ('event', '이벤트'),
        ('general', '일반'),
    ]
    
    # 기본 정보
    qr_type = models.CharField(max_length=50, choices=QR_TYPE_CHOICES, default='general')
    data = models.JSONField(default=dict, verbose_name="QR 코드 데이터")
    
    # 파일 정보
    file_path = models.CharField(max_length=500, verbose_name="파일 경로")
    filename = models.CharField(max_length=200, verbose_name="파일명", blank=True)
    
    # URL 정보
    url = models.URLField(verbose_name="접근 URL")
    gcp_url = models.URLField(verbose_name="GCP Storage URL", blank=True)
    
    # 연관 정보
    related_id = models.CharField(max_length=100, verbose_name="연관 ID", blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # 상태 정보
    is_active = models.BooleanField(default=True)
    access_count = models.IntegerField(default=0, verbose_name="접근 횟수")
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="만료일")
    
    class Meta:
        verbose_name = "QR 코드"
        verbose_name_plural = "QR 코드 목록"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_qr_type_display()} - {self.related_id or self.id}"
    
    def increment_access_count(self):
        """접근 횟수 증가"""
        self.access_count += 1
        self.save(update_fields=['access_count'])
    
    def is_expired(self):
        """만료 여부 확인"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at

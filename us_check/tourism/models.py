from django.db import models
from django.contrib.auth.models import User
import json

class TourismSpot(models.Model):
    """의성군 관광지 정보 모델"""
    
    # Firestore document ID
    firestore_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # 기본 정보
    name = models.CharField(max_length=200, verbose_name="관광지명")
    description = models.TextField(verbose_name="설명", blank=True)
    address = models.CharField(max_length=300, verbose_name="주소", blank=True)
    
    # 위치 정보
    latitude = models.FloatField(verbose_name="위도", null=True, blank=True)
    longitude = models.FloatField(verbose_name="경도", null=True, blank=True)
    
    # 분류 정보
    category = models.CharField(max_length=100, verbose_name="카테고리", blank=True)
    tags = models.JSONField(default=list, verbose_name="태그", blank=True)
    
    # 추가 정보
    contact_info = models.CharField(max_length=200, verbose_name="연락처", blank=True)
    website = models.URLField(verbose_name="웹사이트", blank=True)
    opening_hours = models.TextField(verbose_name="운영시간", blank=True)
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Firestore에서 가져온 원본 JSON 데이터
    raw_data = models.JSONField(default=dict, verbose_name="원본 데이터")
    
    class Meta:
        verbose_name = "관광지"
        verbose_name_plural = "관광지 목록"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'firestore_id': self.firestore_id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'category': self.category,
            'tags': self.tags,
            'contact_info': self.contact_info,
            'website': self.website,
            'opening_hours': self.opening_hours,
            'raw_data': self.raw_data,
        }


class UserTourismSelection(models.Model):
    """사용자의 관광지 선택 기록"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, verbose_name="세션 ID", blank=True)
    
    # 선택된 관광지
    selected_spots = models.ManyToManyField(TourismSpot, verbose_name="선택된 관광지")
    
    # 사용자 쿼리 정보
    original_query = models.TextField(verbose_name="원본 쿼리")
    processed_query = models.TextField(verbose_name="처리된 쿼리", blank=True)
    
    # Gemini AI 분석 결과
    ai_analysis = models.JSONField(default=dict, verbose_name="AI 분석 결과")
    
    # QR 코드 정보
    qr_code_url = models.URLField(verbose_name="QR 코드 URL", blank=True)
    qr_code_path = models.CharField(max_length=500, verbose_name="QR 코드 파일 경로", blank=True)
    
    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "사용자 관광지 선택"
        verbose_name_plural = "사용자 관광지 선택 기록"
        ordering = ['-created_at']
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Session: {self.session_id}"
        return f"{user_info} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

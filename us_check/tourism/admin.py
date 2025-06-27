from django.contrib import admin
from .models import TourismSpot, UserTourismSelection

@admin.register(TourismSpot)
class TourismSpotAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'address', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'address', 'category']
    readonly_fields = ['firestore_id', 'created_at', 'updated_at']
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description', 'category', 'tags')
        }),
        ('위치 정보', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('연락처 정보', {
            'fields': ('contact_info', 'website', 'opening_hours')
        }),
        ('시스템 정보', {
            'fields': ('firestore_id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('원본 데이터', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        })
    )

@admin.register(UserTourismSelection)
class UserTourismSelectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'original_query', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['original_query', 'user__username', 'session_id']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['selected_spots']
    fieldsets = (
        ('사용자 정보', {
            'fields': ('user', 'session_id')
        }),
        ('쿼리 정보', {
            'fields': ('original_query', 'processed_query', 'ai_analysis')
        }),
        ('선택된 관광지', {
            'fields': ('selected_spots',)
        }),
        ('QR 코드 정보', {
            'fields': ('qr_code_url', 'qr_code_path')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

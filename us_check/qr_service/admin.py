from django.contrib import admin
from .models import QRCode

@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'qr_type', 'related_id', 'user', 'is_active', 'access_count', 'created_at']
    list_filter = ['qr_type', 'is_active', 'created_at', 'expires_at']
    search_fields = ['related_id', 'user__username', 'filename']
    readonly_fields = ['created_at', 'updated_at', 'access_count']
    fieldsets = (
        ('기본 정보', {
            'fields': ('qr_type', 'related_id', 'user')
        }),
        ('파일 정보', {
            'fields': ('file_path', 'filename', 'url', 'gcp_url')
        }),
        ('상태 정보', {
            'fields': ('is_active', 'access_count', 'expires_at')
        }),
        ('데이터', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

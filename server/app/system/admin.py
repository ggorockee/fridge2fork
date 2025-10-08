from django.contrib import admin
from .models import Feedback, AdConfig, AppVersion


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """피드백 관리자"""
    list_display = ['id', 'feedback_type', 'title', 'user_or_session', 'contact_email', 'created_at']
    list_filter = ['feedback_type', 'created_at']
    search_fields = ['title', 'content', 'contact_email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def user_or_session(self, obj):
        """사용자 또는 세션 정보"""
        if obj.user:
            return f'{obj.user.username} (회원)'
        return f'비회원 ({obj.session_key[:8]}...)' if obj.session_key else '비회원'
    user_or_session.short_description = '작성자'


@admin.register(AdConfig)
class AdConfigAdmin(admin.ModelAdmin):
    """광고 설정 관리자"""
    list_display = ['id', 'ad_type', 'platform', 'ad_unit_id_short', 'is_active', 'updated_at']
    list_filter = ['platform', 'ad_type', 'is_active']
    search_fields = ['ad_unit_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['platform', 'ad_type']

    fieldsets = (
        ('기본 정보', {
            'fields': ('ad_type', 'platform', 'ad_unit_id', 'is_active')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def ad_unit_id_short(self, obj):
        """광고 ID 축약 표시"""
        if len(obj.ad_unit_id) > 30:
            return f'{obj.ad_unit_id[:30]}...'
        return obj.ad_unit_id
    ad_unit_id_short.short_description = '광고 단위 ID'


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    """앱 버전 관리자"""
    list_display = ['id', 'platform', 'version_name', 'version_code', 'force_update', 'is_active', 'release_date']
    list_filter = ['platform', 'force_update', 'is_active', 'release_date']
    search_fields = ['version_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-version_code']

    fieldsets = (
        ('기본 정보', {
            'fields': ('platform', 'version_name', 'version_code', 'is_active')
        }),
        ('업데이트 설정', {
            'fields': ('min_supported_version_code', 'force_update', 'update_message', 'download_url')
        }),
        ('출시 정보', {
            'fields': ('release_date',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

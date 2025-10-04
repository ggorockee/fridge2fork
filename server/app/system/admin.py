from django.contrib import admin
from .models import Feedback


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

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class FeedbackType(models.TextChoices):
    """피드백 유형"""
    BUG = 'BUG', '버그 리포트'
    FEATURE = 'FEATURE', '기능 제안'
    IMPROVEMENT = 'IMPROVEMENT', '개선 제안'
    OTHER = 'OTHER', '기타'


class Feedback(models.Model):
    """사용자 피드백"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name='사용자',
        help_text='회원인 경우 사용자 정보'
    )
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='세션 키',
        help_text='비회원인 경우 세션 키'
    )
    feedback_type = models.CharField(
        max_length=20,
        choices=FeedbackType.choices,
        default=FeedbackType.OTHER,
        db_index=True,
        verbose_name='피드백 유형'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='제목'
    )
    content = models.TextField(
        verbose_name='내용'
    )
    contact_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='연락처 이메일',
        help_text='답변 받을 이메일 (선택)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='생성일시'
    )

    class Meta:
        db_table = 'system_feedback'
        verbose_name = '피드백'
        verbose_name_plural = '피드백'
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.username if self.user else f'비회원({self.session_key[:8]})'
        return f'[{self.get_feedback_type_display()}] {self.title} - {user_info}'

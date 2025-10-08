from django.db import models
from django.contrib.auth import get_user_model
from core.models import CommonModel

User = get_user_model()


class Platform(models.TextChoices):
    """플랫폼"""
    ANDROID = 'ANDROID', 'Android'
    IOS = 'IOS', 'iOS'


class AdType(models.TextChoices):
    """광고 타입"""
    BANNER_TOP = 'BANNER_TOP', '배너 광고 (상단)'
    BANNER_BOTTOM = 'BANNER_BOTTOM', '배너 광고 (하단)'
    INTERSTITIAL_1 = 'INTERSTITIAL_1', '전면 광고 1'
    INTERSTITIAL_2 = 'INTERSTITIAL_2', '전면 광고 2'
    NATIVE_1 = 'NATIVE_1', '네이티브 광고 1'
    NATIVE_2 = 'NATIVE_2', '네이티브 광고 2'


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


class AdConfig(CommonModel):
    """AdMob 광고 설정"""
    ad_type = models.CharField(
        max_length=50,
        choices=AdType.choices,
        verbose_name='광고 타입'
    )
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        db_index=True,
        verbose_name='플랫폼'
    )
    ad_unit_id = models.CharField(
        max_length=255,
        verbose_name='광고 단위 ID',
        help_text='AdMob 광고 단위 ID (예: ca-app-pub-xxx/yyy)'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='활성화 여부'
    )

    class Meta:
        db_table = 'system_ad_config'
        verbose_name = '광고 설정'
        verbose_name_plural = '광고 설정'
        ordering = ['platform', 'ad_type']
        unique_together = [['ad_type', 'platform']]
        indexes = [
            models.Index(fields=['platform', 'is_active']),
        ]

    def __str__(self):
        return f'[{self.get_platform_display()}] {self.get_ad_type_display()}'


class AppVersion(CommonModel):
    """앱 버전 관리"""
    platform = models.CharField(
        max_length=20,
        choices=Platform.choices,
        db_index=True,
        verbose_name='플랫폼'
    )
    version_name = models.CharField(
        max_length=50,
        verbose_name='버전명',
        help_text='예: 1.2.3'
    )
    version_code = models.IntegerField(
        verbose_name='버전 코드',
        help_text='비교용 정수 (예: 1.2.3 → 10203)'
    )
    min_supported_version_code = models.IntegerField(
        verbose_name='최소 지원 버전 코드',
        help_text='이 버전보다 낮으면 강제 업데이트'
    )
    force_update = models.BooleanField(
        default=False,
        verbose_name='강제 업데이트 여부'
    )
    update_message = models.TextField(
        verbose_name='업데이트 안내 메시지',
        help_text='사용자에게 표시할 업데이트 메시지'
    )
    download_url = models.URLField(
        max_length=500,
        verbose_name='다운로드 URL',
        help_text='앱 스토어 URL'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='활성화 여부',
        help_text='최신 버전만 True로 설정'
    )
    release_date = models.DateTimeField(
        verbose_name='출시 일시'
    )

    class Meta:
        db_table = 'system_app_version'
        verbose_name = '앱 버전'
        verbose_name_plural = '앱 버전'
        ordering = ['-version_code']
        unique_together = [['platform', 'version_code']]
        indexes = [
            models.Index(fields=['platform', 'is_active']),
            models.Index(fields=['platform', 'version_code']),
        ]

    def __str__(self):
        return f'[{self.get_platform_display()}] {self.version_name} (코드: {self.version_code})'

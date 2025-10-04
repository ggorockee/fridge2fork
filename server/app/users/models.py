"""
User 모델 정의

email 기반 인증을 사용하는 Custom User 모델을 정의합니다.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom User Manager

    email을 사용자명으로 사용하는 사용자 관리자
    """

    def create_user(self, email, password=None, username=None, **extra_fields):
        """
        일반 사용자 생성

        Args:
            email: 사용자 이메일 (필수, unique)
            password: 비밀번호
            username: 사용자명 (선택, 없으면 email에서 추출)
            **extra_fields: 추가 필드

        Returns:
            User: 생성된 사용자 객체
        """
        if not email:
            raise ValueError('이메일은 필수입니다.')

        # 이메일 정규화 (소문자 변환)
        email = self.normalize_email(email)

        # username이 없으면 email의 "@" 앞부분 사용
        if not username:
            username = email.split('@')[0]

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        슈퍼유저 생성

        Args:
            email: 사용자 이메일
            password: 비밀번호
            **extra_fields: 추가 필드

        Returns:
            User: 생성된 슈퍼유저 객체
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('슈퍼유저는 is_staff=True여야 합니다.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('슈퍼유저는 is_superuser=True여야 합니다.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User 모델

    email을 사용자명으로 사용하며, username은 선택적 필드입니다.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="이메일",
        help_text="사용자 이메일 주소 (로그인 ID)"
    )
    username = models.CharField(
        max_length=150,
        verbose_name="사용자명",
        help_text="사용자명 (선택사항, 중복 허용)",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성 상태",
        help_text="사용자 활성 여부"
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="스태프 권한",
        help_text="관리자 사이트 접근 권한"
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name="가입일시",
        help_text="사용자가 가입한 시각"
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'  # 로그인 시 사용할 필드
    REQUIRED_FIELDS = []  # createsuperuser 시 추가로 물어볼 필드

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자"
        ordering = ['-date_joined']

    def __str__(self):
        """사용자 문자열 표현"""
        return self.email

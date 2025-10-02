"""
User 모델 테스트
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """User 모델 테스트"""

    def test_create_user_with_email_and_password(self):
        """email과 password로 사용자 생성 테스트"""
        email = "test@example.com"
        password = "testpass123"

        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_username(self):
        """username 없이 생성 시 email에서 자동 추출 테스트"""
        email = "testuser@example.com"
        password = "testpass123"

        user = User.objects.create_user(
            email=email,
            password=password
        )

        # email의 "@" 앞부분이 username으로 설정되어야 함
        self.assertEqual(user.username, "testuser")

    def test_username_is_optional(self):
        """username이 선택적 필드임을 확인"""
        email = "test@example.com"
        password = "testpass123"

        # username 없이 사용자 생성 가능
        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertIsNotNone(user.username)
        self.assertTrue(user.username)  # 빈 문자열이 아님

    def test_duplicate_username_allowed(self):
        """username 중복 허용 확인"""
        User.objects.create_user(
            email="user1@example.com",
            password="pass123",
            username="duplicated"
        )

        # 같은 username으로 다른 사용자 생성 가능
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123",
            username="duplicated"
        )

        self.assertEqual(user2.username, "duplicated")
        self.assertEqual(User.objects.filter(username="duplicated").count(), 2)

    def test_email_is_unique(self):
        """email은 unique 제약 확인"""
        email = "duplicate@example.com"

        User.objects.create_user(
            email=email,
            password="pass123"
        )

        # 같은 email로 사용자 생성 시 에러 발생
        with self.assertRaises(Exception):
            User.objects.create_user(
                email=email,
                password="pass456"
            )

    def test_email_is_normalized(self):
        """email 정규화 확인 (도메인 소문자 변환)"""
        email = "Test@Example.COM"

        user = User.objects.create_user(
            email=email,
            password="pass123"
        )

        # 도메인 부분이 소문자로 정규화되어야 함
        self.assertEqual(user.email, "Test@example.com")

    def test_create_superuser(self):
        """슈퍼유저 생성 테스트"""
        email = "admin@example.com"
        password = "adminpass123"

        user = User.objects.create_superuser(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

"""
인증 API 테스트 (TDD)
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class AuthAPITest(TestCase):
    """인증 API 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.register_url = '/auth/register'
        self.login_url = '/auth/login'
        self.me_url = '/auth/me'

    def test_register_with_email_password(self):
        """이메일과 비밀번호로 회원가입 성공"""
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'username': 'testuser'
        }
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # 토큰 확인
        self.assertIn('token', response_data)
        self.assertIn('access_token', response_data['token'])
        self.assertEqual(response_data['token']['token_type'], 'bearer')

        # 사용자 정보 확인
        self.assertIn('user', response_data)
        self.assertEqual(response_data['user']['email'], 'test@example.com')
        self.assertEqual(response_data['user']['username'], 'testuser')

        # DB에 사용자 생성 확인
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpassword123'))

    def test_register_without_username(self):
        """username 없이 회원가입 - 이메일에서 자동 생성"""
        data = {
            'email': 'auto@example.com',
            'password': 'password123'
        }
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # username이 자동 생성되었는지 확인 (이메일 @ 앞부분)
        self.assertEqual(response_data['user']['username'], 'auto')

        # DB 확인
        user = User.objects.get(email='auto@example.com')
        self.assertEqual(user.username, 'auto')

    def test_register_duplicate_email(self):
        """중복 이메일로 회원가입 시 에러"""
        # 먼저 사용자 생성
        User.objects.create_user(email='duplicate@example.com', password='pass123')

        # 같은 이메일로 회원가입 시도
        data = {
            'email': 'duplicate@example.com',
            'password': 'newpassword'
        }
        response = self.client.post(
            self.register_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_login_success(self):
        """로그인 성공 - 토큰 반환"""
        # 사용자 생성
        user = User.objects.create_user(
            email='login@example.com',
            password='loginpassword'
        )

        # 로그인
        data = {
            'email': 'login@example.com',
            'password': 'loginpassword'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # 토큰 확인
        self.assertIn('token', response_data)
        self.assertIn('access_token', response_data['token'])

        # 사용자 정보 확인
        self.assertIn('user', response_data)
        self.assertEqual(response_data['user']['email'], 'login@example.com')

    def test_login_invalid_credentials(self):
        """잘못된 인증 정보로 로그인 실패"""
        # 사용자 생성
        User.objects.create_user(
            email='user@example.com',
            password='correctpassword'
        )

        # 잘못된 비밀번호로 로그인
        data = {
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_get_current_user(self):
        """토큰으로 현재 사용자 정보 조회"""
        # 사용자 생성 및 로그인
        User.objects.create_user(
            email='current@example.com',
            password='password123',
            username='currentuser'
        )

        login_data = {
            'email': 'current@example.com',
            'password': 'password123'
        }
        login_response = self.client.post(
            self.login_url,
            data=json.dumps(login_data),
            content_type='application/json'
        )

        token = login_response.json()['token']['access_token']

        # 토큰으로 사용자 정보 조회
        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['email'], 'current@example.com')
        self.assertEqual(response_data['username'], 'currentuser')

    def test_get_current_user_without_token(self):
        """토큰 없이 사용자 정보 조회 시 401 에러"""
        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, 401)

    def test_get_current_user_invalid_token(self):
        """잘못된 토큰으로 사용자 정보 조회 시 401 에러"""
        response = self.client.get(
            self.me_url,
            HTTP_AUTHORIZATION='Bearer invalid_token_here'
        )

        self.assertEqual(response.status_code, 401)

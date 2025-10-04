"""
시스템 버전 API 테스트
"""

from django.test import TestCase, Client, override_settings


class SystemVersionAPITest(TestCase):
    """시스템 버전 API 테스트"""

    def setUp(self):
        """테스트용 클라이언트 생성"""
        self.client = Client()
        self.url = "/fridge2fork/v1/system/version"

    def test_get_version_success(self):
        """
        TC-1: 정상 응답 확인

        시스템 버전 API가 정상적으로 응답해야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 응답 데이터 존재 확인
        self.assertIsNotNone(data)

    def test_response_schema(self):
        """
        TC-2: 응답 스키마 검증

        version, environment, status 필드가 포함되어야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 필수 필드 확인
        required_fields = ['version', 'environment', 'status']
        for field in required_fields:
            self.assertIn(field, data)
            self.assertIsNotNone(data[field])

    @override_settings(DEBUG=True)
    def test_environment_development(self):
        """
        TC-3: 환경 정보 확인 (개발)

        DEBUG=True일 때 environment가 'development'여야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['environment'], 'development')

    @override_settings(DEBUG=False)
    def test_environment_production(self):
        """
        TC-4: 환경 정보 확인 (운영)

        DEBUG=False일 때 environment가 'production'이어야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['environment'], 'production')

    def test_status_healthy(self):
        """
        TC-5: 상태 정보 확인

        정상 작동 시 status가 'healthy'여야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['status'], 'healthy')

    def test_version_format(self):
        """
        버전 형식 확인

        version이 문자열이고 비어있지 않아야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIsInstance(data['version'], str)
        self.assertGreater(len(data['version']), 0)

    def test_no_authentication_required(self):
        """
        인증 불필요 확인

        인증 없이도 접근 가능해야 함
        """
        response = self.client.get(self.url)

        # 401 Unauthorized가 아닌 200 OK 응답
        self.assertEqual(response.status_code, 200)

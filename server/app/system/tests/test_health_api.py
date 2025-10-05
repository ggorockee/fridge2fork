"""
시스템 헬스 체크 API 테스트
"""

from django.test import TestCase, Client
import time


class SystemHealthAPITest(TestCase):
    """시스템 헬스 체크 API 테스트"""

    def setUp(self):
        """테스트용 클라이언트 생성"""
        self.client = Client()
        self.url = "/fridge2fork/v1/system/health"

    def test_health_check_success(self):
        """
        TC-1: 정상 응답 확인

        헬스 체크 API가 정상적으로 응답해야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 응답 데이터 존재 확인
        self.assertIsNotNone(data)
        self.assertEqual(data['status'], 'healthy')

    def test_response_schema(self):
        """
        TC-2: 응답 스키마 검증

        status 필드만 포함되어야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # status 필드 확인
        self.assertIn('status', data)
        self.assertIsNotNone(data['status'])

        # 불필요한 필드 없음 확인
        self.assertEqual(len(data), 1)

    def test_status_healthy(self):
        """
        TC-3: 상태 값 확인

        status가 'healthy'여야 함
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['status'], 'healthy')

    def test_no_authentication_required(self):
        """
        TC-4: 인증 불필요 확인

        인증 없이도 접근 가능해야 함
        """
        response = self.client.get(self.url)

        # 401 Unauthorized가 아닌 200 OK 응답
        self.assertEqual(response.status_code, 200)

    def test_fast_response_time(self):
        """
        TC-5: 빠른 응답 시간

        응답 시간이 100ms 미만이어야 함 (헬스 체크 용도)
        """
        start_time = time.time()
        response = self.client.get(self.url)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time_ms, 100)

    def test_minimal_response_size(self):
        """
        최소 응답 크기 확인

        불필요한 정보 없이 status만 반환
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 필드가 1개만 존재
        self.assertEqual(len(data.keys()), 1)

        # version, environment 필드 없음
        self.assertNotIn('version', data)
        self.assertNotIn('environment', data)

    def test_multiple_requests(self):
        """
        연속 요청 테스트

        여러 번 호출해도 일관된 응답
        """
        for _ in range(5):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'healthy')

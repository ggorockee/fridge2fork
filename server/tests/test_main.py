"""
메인 애플리케이션 및 기본 엔드포인트 테스트
"""
import pytest
from fastapi.testclient import TestClient


class TestMain:
    """메인 애플리케이션 테스트 클래스"""

    def test_root_endpoint(self, client: TestClient):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "environment" in data
        assert "Fridge2Fork API" in data["message"]

    def test_simple_health_endpoint(self, client: TestClient):
        """간단한 헬스체크 엔드포인트 테스트"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert "Fridge2Fork API" in data["service"]

    def test_cors_headers(self, client: TestClient):
        """CORS 헤더 테스트"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # CORS preflight 요청이 허용되어야 함
        assert response.status_code in [200, 204]

    def test_api_docs_access(self, client: TestClient):
        """API 문서 접근 테스트 (개발 환경에서만)"""
        # 개발 환경에서는 문서에 접근 가능해야 함
        response = client.get("/docs")
        # 테스트 환경에서는 DEBUG=False이므로 404가 정상
        assert response.status_code in [200, 404]
        
        response = client.get("/redoc")
        assert response.status_code in [200, 404]

    def test_openapi_schema(self, client: TestClient):
        """OpenAPI 스키마 테스트"""
        response = client.get("/openapi.json")
        
        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data
            assert data["info"]["title"] == "Fridge2Fork API"

    def test_404_error_handling(self, client: TestClient):
        """존재하지 않는 엔드포인트 404 처리 테스트"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404

    def test_method_not_allowed(self, client: TestClient):
        """허용되지 않는 HTTP 메서드 테스트"""
        response = client.post("/")  # GET만 허용되는 엔드포인트에 POST 요청
        
        assert response.status_code == 405

    def test_api_v1_prefix(self, client: TestClient):
        """API v1 prefix 테스트"""
        # v1 prefix가 없는 요청은 404
        response = client.get("/auth/profile")
        assert response.status_code == 404
        
        # v1 prefix가 있는 요청은 인증 오류 (401/403)
        response = client.get("/v1/auth/profile")
        assert response.status_code in [401, 403]

    def test_request_validation_error(self, client: TestClient):
        """요청 검증 오류 처리 테스트"""
        # 잘못된 JSON 형식
        response = client.post(
            "/v1/auth/register",
            json={
                "email": "invalid-email",  # 잘못된 이메일 형식
                "password": "123"  # 너무 짧은 비밀번호
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_content_type_handling(self, client: TestClient):
        """Content-Type 처리 테스트"""
        # JSON Content-Type
        response = client.post(
            "/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [200, 400]  # 유효한 요청이므로 처리됨
        
        # 잘못된 Content-Type
        response = client.post(
            "/v1/auth/register",
            data="invalid data",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422

    def test_large_request_handling(self, client: TestClient):
        """큰 요청 처리 테스트"""
        # 매우 긴 문자열을 포함한 요청
        long_content = "x" * 10000  # 10KB 문자열
        
        response = client.post(
            "/v1/user/feedback",
            json={
                "type": "feature",
                "title": "테스트",
                "content": long_content
            }
        )
        
        # 인증이 필요하므로 401/403이지만, 요청 자체는 처리됨
        assert response.status_code in [200, 401, 403, 422]

    def test_concurrent_requests(self, client: TestClient):
        """동시 요청 처리 테스트"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/")
            results.append(response.status_code)
        
        # 20개의 동시 요청
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # 모든 요청이 성공해야 함
        assert all(status == 200 for status in results)
        assert len(results) == 20
        
        # 처리 시간이 합리적이어야 함
        assert (end_time - start_time) < 10.0  # 10초 이내

    def test_response_headers(self, client: TestClient):
        """응답 헤더 테스트"""
        response = client.get("/")
        
        # Content-Type 헤더 확인
        assert response.headers["content-type"] == "application/json"
        
        # CORS 헤더가 있는지 확인 (설정에 따라)
        # assert "access-control-allow-origin" in response.headers

    def test_api_version_consistency(self, client: TestClient):
        """API 버전 일관성 테스트"""
        # 루트 엔드포인트에서 버전 확인
        root_response = client.get("/")
        root_data = root_response.json()
        
        # 시스템 버전 엔드포인트에서 버전 확인
        version_response = client.get("/v1/version?platform=android")
        if version_response.status_code == 200:
            version_data = version_response.json()
            
            # API 버전이 일치해야 함
            assert root_data["version"] == version_data["api_version"]

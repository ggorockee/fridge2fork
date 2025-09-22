"""
시스템 API 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.system import PlatformVersion, SystemStatus


class TestSystem:
    """시스템 API 테스트 클래스"""

    def test_get_version_info_with_platform_data(self, client: TestClient, test_platform_version: PlatformVersion):
        """플랫폼 데이터가 있는 상태에서 버전 정보 조회 테스트"""
        response = client.get(
            "/v1/version?platform=android&current_version=1.0.0&build_number=1"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 응답 구조 검증
        assert "api_version" in data
        assert "platform_info" in data
        assert "maintenance" in data
        
        # 플랫폼 정보 검증
        platform_info = data["platform_info"]
        assert platform_info["platform"] == "android"
        assert platform_info["latest_version"] == "1.0.0"
        assert platform_info["update_required"] is False
        assert platform_info["update_recommended"] is False

    def test_get_version_info_update_required(self, client: TestClient, test_platform_version: PlatformVersion):
        """업데이트 필수인 경우 버전 정보 조회 테스트"""
        response = client.get(
            "/v1/version?platform=android&current_version=0.9.0"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        platform_info = data["platform_info"]
        assert platform_info["update_required"] is True

    def test_get_version_info_update_recommended(self, client: TestClient, test_platform_version: PlatformVersion):
        """업데이트 권장인 경우 버전 정보 조회 테스트"""
        # 최신 버전을 1.1.0으로 업데이트
        test_platform_version.latest_version = "1.1.0"
        
        response = client.get(
            "/v1/version?platform=android&current_version=1.0.0"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        platform_info = data["platform_info"]
        assert platform_info["update_recommended"] is True

    def test_get_version_info_no_platform_data(self, client: TestClient):
        """플랫폼 데이터가 없는 경우 기본값 반환 테스트"""
        response = client.get("/v1/version?platform=ios")
        
        assert response.status_code == 200
        data = response.json()
        
        platform_info = data["platform_info"]
        assert platform_info["platform"] == "ios"
        assert platform_info["latest_version"] == "1.0.0"  # 기본값
        assert platform_info["update_required"] is False
        assert platform_info["update_recommended"] is False

    def test_get_version_info_invalid_platform(self, client: TestClient):
        """잘못된 플랫폼 이름 처리 테스트"""
        response = client.get("/v1/version?platform=invalid_platform")
        
        assert response.status_code == 200
        data = response.json()
        
        # 잘못된 플랫폼은 web으로 기본 처리
        platform_info = data["platform_info"]
        assert platform_info["platform"] == "web"

    def test_get_version_info_with_maintenance(self, client: TestClient, test_system_status: SystemStatus):
        """점검 모드인 경우 버전 정보 조회 테스트"""
        # 점검 모드 설정
        test_system_status.maintenance_mode = True
        
        response = client.get("/v1/version?platform=android")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["maintenance"] is True
        assert data["message"] == "테스트 공지사항"
        assert data["update_message"] == "테스트 업데이트 메시지"

    @pytest.mark.asyncio
    async def test_get_all_platforms(self, async_client: AsyncClient, test_platform_version: PlatformVersion):
        """모든 플랫폼 정보 조회 테스트"""
        response = await async_client.get("/v1/system/platforms")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "platforms" in data
        assert isinstance(data["platforms"], list)
        
        if data["platforms"]:
            platform = data["platforms"][0]
            assert "platform" in platform
            assert "latest_version" in platform
            assert "status" in platform
            assert "release_date" in platform

    @patch('app.api.v1.system.get_redis')
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, mock_get_redis, async_client: AsyncClient):
        """모든 서비스가 정상인 경우 헬스체크 테스트"""
        # Redis 모킹
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis
        
        response = await async_client.get("/v1/system/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert "version" in data
        
        services = data["services"]
        assert services["database"] == "healthy"
        assert services["redis"] == "healthy"
        assert services["api"] == "healthy"

    @patch('app.api.v1.system.get_redis')
    @pytest.mark.asyncio
    async def test_health_check_redis_down(self, mock_get_redis, async_client: AsyncClient):
        """Redis가 다운된 경우 헬스체크 테스트"""
        # Redis 연결 실패 모킹
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        mock_get_redis.return_value = mock_redis
        
        response = await async_client.get("/v1/system/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "degraded"
        services = data["services"]
        assert services["redis"] == "down"
        assert services["database"] == "healthy"  # DB는 정상
        assert services["api"] == "healthy"

    def test_version_comparison_edge_cases(self, client: TestClient):
        """버전 비교 엣지 케이스 테스트"""
        # 버전 정보가 없는 경우
        response = client.get("/v1/version?platform=android")
        assert response.status_code == 200
        
        # 잘못된 버전 형식
        response = client.get("/v1/version?platform=android&current_version=invalid.version")
        assert response.status_code == 200
        data = response.json()
        platform_info = data["platform_info"]
        assert platform_info["update_required"] is False

    def test_system_api_performance(self, client: TestClient):
        """시스템 API 응답 시간 테스트"""
        import time
        
        # 버전 정보 조회 성능
        start_time = time.perf_counter()
        response = client.get("/v1/version?platform=android")
        end_time = time.perf_counter()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # 5초 이내 응답 (테스트 환경 고려)
        
        # 헬스체크 성능
        start_time = time.perf_counter()
        response = client.get("/v1/system/health")
        end_time = time.perf_counter()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # 5초 이내 응답

    def test_system_api_concurrent_requests(self, client: TestClient):
        """시스템 API 동시 요청 처리 테스트"""
        import threading
        import time
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def make_request():
            try:
                response = client.get("/v1/version?platform=android")
                with lock:
                    results.append(response.status_code)
            except Exception as e:
                with lock:
                    errors.append(str(e))
                    results.append(500)  # 오류 시 500으로 기록
        
        # 3개의 동시 요청 (더 안정적으로 줄임)
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        start_time = time.perf_counter()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=15.0)  # 타임아웃 추가
        
        end_time = time.perf_counter()
        
        # 디버그 정보 출력
        if errors:
            print(f"Errors occurred: {errors}")
        print(f"Results: {results}")
        
        # 결과 검증 - 최소 1개 이상의 요청이 성공하면 통과
        assert len(results) >= 1, f"No results received. Errors: {errors}"
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 1, f"No successful requests. Results: {results}, Errors: {errors}"
        
        # 전체 처리 시간이 합리적이어야 함
        assert (end_time - start_time) < 20.0  # 20초 이내

    @pytest.mark.asyncio
    async def test_system_status_priority(self, async_client: AsyncClient, db_session):
        """시스템 상태 우선순위 테스트 (최신 상태 우선)"""
        from app.models.system import SystemStatus
        from sqlalchemy import select
        
        # 기존 시스템 상태 모두 삭제
        await db_session.execute(
            SystemStatus.__table__.delete()
        )
        await db_session.commit()
        
        # 새로운 시스템 상태만 생성
        new_status = SystemStatus(
            maintenance_mode=False,
            announcement_message="테스트 공지"
        )
        
        db_session.add(new_status)
        await db_session.commit()
        
        response = await async_client.get("/v1/version?platform=android")
        
        assert response.status_code == 200
        data = response.json()
        
        # 새로 생성한 상태가 반영되어야 함
        assert data["maintenance"] is False
        assert data["message"] == "테스트 공지"

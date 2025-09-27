# Kubernetes 환경 데이터 마이그레이션 가이드

## 개요

Kubernetes 클러스터 내의 PostgreSQL 데이터베이스에 CSV 데이터를 안전하게 마이그레이션하는 방법을 설명합니다. 외부에서 직접 접근이 불가능한 환경에서 Docker 컨테이너를 이용한 데이터 로딩 전략을 제시합니다.

## 문제 상황

- PostgreSQL이 Kubernetes 클러스터 내부에 존재
- 외부에서 직접 데이터베이스 접근 불가
- 대용량 CSV 파일 (3개 파일)을 데이터베이스에 입력 필요
- 재료 정규화 등 복잡한 데이터 처리 로직 필요

## 해결 전략

### 1. Docker 기반 데이터 마이그레이션 컨테이너

**아키텍처**:
```
로컬 CSV 파일 → Docker 컨테이너 → K8s PostgreSQL
```

**장점**:
- 네트워크 격리 환경에서 실행 가능
- 일회성 작업으로 컨테이너 자동 종료
- 환경 독립적 실행
- 로깅 및 모니터링 가능

### 2. 데이터 마이그레이션 방법 비교

| 방법 | 장점 | 단점 | 추천도 |
|------|------|------|--------|
| Job 컨테이너 | K8s 네이티브, 자동 정리 | 이미지 빌드 필요 | ⭐⭐⭐⭐⭐ |
| InitContainer | 앱과 함께 배포 | 앱 배포시마다 실행 | ⭐⭐⭐ |
| 직접 Pod 실행 | 간단한 테스트 | 수동 정리 필요 | ⭐⭐ |
| kubectl exec | 즉석 실행 | 대용량 처리 부적합 | ⭐ |

## 구현 방안

### 1. 데이터 마이그레이션 Docker 이미지

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements-migration.txt .
RUN pip install --no-cache-dir -r requirements-migration.txt

# 애플리케이션 코드 복사
COPY app/ /app/
COPY scripts/ /scripts/
COPY datas/ /datas/

# 작업 디렉토리 설정
WORKDIR /scripts

# 마이그레이션 스크립트 실행
CMD ["python", "migrate_data.py"]
```

**requirements-migration.txt**:
```txt
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
pandas==2.1.3
python-dotenv==1.0.0
tqdm==4.66.1
```

### 2. Kubernetes Job 매니페스트

**k8s/data-migration-job.yaml**:
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: fridge2fork-data-migration
  namespace: default
spec:
  # 완료 후 자동 삭제 (선택적)
  ttlSecondsAfterFinished: 600
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: data-migrator
        image: fridge2fork/data-migrator:latest
        env:
        - name: DATABASE_HOST
          value: "postgresql-service"  # K8s 서비스명
        - name: DATABASE_PORT
          value: "5432"
        - name: DATABASE_NAME
          value: "fridge2fork_db"
        - name: DATABASE_USER
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: username
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        - name: BATCH_SIZE
          value: "1000"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        # 볼륨 마운트 (로그 확인용)
        volumeMounts:
        - name: migration-logs
          mountPath: /logs
      volumes:
      - name: migration-logs
        emptyDir: {}
```

### 3. 데이터 마이그레이션 스크립트

**scripts/migrate_data.py** (핵심 로직):
```python
#!/usr/bin/env python3
"""
K8s 환경용 데이터 마이그레이션 스크립트
CSV 파일을 PostgreSQL로 배치 처리
"""

import os
import asyncio
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self):
        self.database_url = self._build_database_url()
        self.engine = create_async_engine(self.database_url)
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))

    def _build_database_url(self) -> str:
        """환경변수에서 데이터베이스 URL 구성"""
        host = os.getenv('DATABASE_HOST', 'localhost')
        port = os.getenv('DATABASE_PORT', '5432')
        name = os.getenv('DATABASE_NAME', 'fridge2fork_db')
        user = os.getenv('DATABASE_USER', 'postgres')
        password = os.getenv('DATABASE_PASSWORD', '')

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

    async def run_migration(self):
        """전체 마이그레이션 프로세스 실행"""
        try:
            logger.info("🚀 데이터 마이그레이션 시작")

            # 1. 연결 테스트
            await self._test_connection()

            # 2. CSV 파일 목록 확인
            csv_files = self._get_csv_files()
            logger.info(f"📁 발견된 CSV 파일: {len(csv_files)}개")

            # 3. 각 파일 처리
            total_processed = 0
            for csv_file in csv_files:
                processed = await self._process_csv_file(csv_file)
                total_processed += processed

            logger.info(f"✅ 마이그레이션 완료: 총 {total_processed}개 레코드 처리")

        except Exception as e:
            logger.error(f"❌ 마이그레이션 실패: {e}")
            raise
        finally:
            await self.engine.dispose()

    async def _test_connection(self):
        """데이터베이스 연결 테스트"""
        async with self.session_factory() as session:
            result = await session.execute("SELECT version()")
            version = result.fetchone()[0]
            logger.info(f"🔗 데이터베이스 연결 성공: {version}")

    def _get_csv_files(self) -> List[Path]:
        """CSV 파일 목록 반환"""
        data_dir = Path("/datas")
        csv_files = []

        # 인코딩별 파일 그룹
        euc_kr_files = [
            "TB_RECIPE_SEARCH-20231130.csv",
            "TB_RECIPE_SEARCH-220701.csv"
        ]
        utf8_files = [
            "TB_RECIPE_SEARCH_241226.csv"
        ]

        for filename in euc_kr_files + utf8_files:
            file_path = data_dir / filename
            if file_path.exists():
                csv_files.append(file_path)
                logger.info(f"📄 CSV 파일 발견: {filename}")

        return csv_files

    async def _process_csv_file(self, csv_file: Path) -> int:
        """개별 CSV 파일 처리"""
        logger.info(f"📝 처리 시작: {csv_file.name}")

        # 인코딩 감지
        encoding = 'euc-kr' if 'TB_RECIPE_SEARCH-' in csv_file.name else 'utf-8'

        try:
            # 청크 단위로 CSV 읽기
            chunk_iterator = pd.read_csv(
                csv_file,
                encoding=encoding,
                chunksize=self.batch_size,
                dtype=str,  # 모든 컬럼을 문자열로 읽기
                keep_default_na=False
            )

            total_rows = 0
            for chunk_num, chunk in enumerate(chunk_iterator):
                logger.info(f"📦 청크 {chunk_num + 1} 처리 중 ({len(chunk)}개 행)")

                # 데이터 정제 및 변환
                processed_data = await self._process_chunk(chunk)

                # 데이터베이스에 저장
                await self._save_to_database(processed_data)

                total_rows += len(chunk)
                logger.info(f"✅ 청크 {chunk_num + 1} 완료 (누적: {total_rows}개)")

            logger.info(f"🎉 {csv_file.name} 처리 완료: {total_rows}개 행")
            return total_rows

        except Exception as e:
            logger.error(f"❌ {csv_file.name} 처리 실패: {e}")
            raise

    async def _process_chunk(self, chunk: pd.DataFrame) -> List[Dict[str, Any]]:
        """데이터 청크 처리 및 정규화"""
        processed_recipes = []

        for _, row in chunk.iterrows():
            try:
                # 레시피 데이터 변환
                recipe_data = {
                    'rcp_sno': row.get('RCP_SNO', ''),
                    'title': row.get('RCP_TTL', ''),
                    'cooking_name': row.get('CKG_NM', ''),
                    'registrant_id': row.get('RGTR_ID', ''),
                    'registrant_name': row.get('RGTR_NM', ''),
                    'inquiry_count': self._safe_int(row.get('INQ_CNT', 0)),
                    'recommendation_count': self._safe_int(row.get('RCMM_CNT', 0)),
                    'scrap_count': self._safe_int(row.get('SRAP_CNT', 0)),
                    'cooking_method': row.get('CKG_MTH_ACTO_NM', ''),
                    'cooking_situation': row.get('CKG_STA_ACTO_NM', ''),
                    'cooking_material_category': row.get('CKG_MTRL_ACTO_NM', ''),
                    'cooking_kind': row.get('CKG_KND_ACTO_NM', ''),
                    'introduction': row.get('CKG_IPDC', ''),
                    'raw_ingredients': row.get('CKG_MTRL_CN', ''),
                    'serving_size': row.get('CKG_INBUN_NM', ''),
                    'difficulty': row.get('CKG_DODF_NM', ''),
                    'cooking_time': row.get('CKG_TIME_NM', ''),
                    'image_url': row.get('RCP_IMG_URL', ''),
                    'registered_at': self._parse_datetime(row.get('FIRST_REG_DT', ''))
                }

                # 재료 파싱 (상세 구현은 별도 모듈로)
                recipe_data['ingredients'] = await self._parse_ingredients(
                    row.get('CKG_MTRL_CN', '')
                )

                processed_recipes.append(recipe_data)

            except Exception as e:
                logger.warning(f"⚠️ 행 처리 실패 (RCP_SNO: {row.get('RCP_SNO', 'unknown')}): {e}")
                continue

        return processed_recipes

    def _safe_int(self, value: Any) -> int:
        """안전한 정수 변환"""
        try:
            return int(value) if value and str(value).strip() else 0
        except (ValueError, TypeError):
            return 0

    def _parse_datetime(self, dt_str: str) -> str:
        """날짜시간 문자열 파싱"""
        if not dt_str or len(dt_str) < 14:
            return None
        try:
            # YYYYMMDDHHMMSS 형식을 YYYY-MM-DD HH:MM:SS로 변환
            return f"{dt_str[:4]}-{dt_str[4:6]}-{dt_str[6:8]} {dt_str[8:10]}:{dt_str[10:12]}:{dt_str[12:14]}"
        except:
            return None

    async def _parse_ingredients(self, ingredients_str: str) -> List[Dict[str, Any]]:
        """재료 문자열 파싱"""
        # 간단한 파싱 구현 (실제로는 더 복잡한 로직 필요)
        if not ingredients_str:
            return []

        # "[재료]" 제거 후 "|"로 분리
        clean_str = ingredients_str.replace('[재료]', '').strip()
        ingredients = [ing.strip() for ing in clean_str.split('|') if ing.strip()]

        parsed_ingredients = []
        for ing in ingredients:
            # 기본적인 파싱 (실제로는 정규식 사용)
            parsed_ingredients.append({
                'raw_text': ing,
                'name': ing.split()[0] if ing.split() else ing,
                'quantity_text': ing
            })

        return parsed_ingredients

    async def _save_to_database(self, recipes_data: List[Dict[str, Any]]):
        """데이터베이스에 배치 저장"""
        async with self.session_factory() as session:
            try:
                # 실제 구현시에는 SQLAlchemy 모델 사용
                # 여기서는 간단한 예시만 제공

                for recipe_data in recipes_data:
                    # recipes 테이블에 저장
                    # ingredients 정규화 및 저장
                    # recipe_ingredients 관계 저장
                    pass

                await session.commit()
                logger.debug(f"💾 {len(recipes_data)}개 레시피 저장 완료")

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ 데이터베이스 저장 실패: {e}")
                raise

async def main():
    """메인 실행 함수"""
    migrator = DataMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())
```

## 실행 방법

### 1. Docker 이미지 빌드
```bash
# 프로젝트 루트에서 실행
docker build -t fridge2fork/data-migrator:latest -f docker/Dockerfile.migration .

# 이미지 푸시 (컨테이너 레지스트리에)
docker push fridge2fork/data-migrator:latest
```

### 2. Kubernetes 시크릿 생성
```bash
# 데이터베이스 접속 정보
kubectl create secret generic postgresql-secret \
  --from-literal=username=fridge2fork_user \
  --from-literal=password=your_password
```

### 3. Job 실행
```bash
# Job 생성 및 실행
kubectl apply -f k8s/data-migration-job.yaml

# 실행 상태 확인
kubectl get jobs
kubectl get pods -l job-name=fridge2fork-data-migration

# 로그 확인
kubectl logs -l job-name=fridge2fork-data-migration -f
```

### 4. 진행 상황 모니터링
```bash
# Job 상태 확인
kubectl describe job fridge2fork-data-migration

# Pod 리소스 사용량 확인
kubectl top pod -l job-name=fridge2fork-data-migration

# 완료 후 정리 (ttlSecondsAfterFinished 설정시 자동)
kubectl delete job fridge2fork-data-migration
```

## 모니터링 및 트러블슈팅

### 일반적인 문제들

1. **메모리 부족**:
   - Job의 memory limits 증가
   - 배치 크기 (BATCH_SIZE) 감소

2. **데이터베이스 연결 실패**:
   - 서비스명 및 포트 확인
   - 시크릿 정보 검증
   - 네트워크 정책 확인

3. **CSV 인코딩 문제**:
   - 파일별 인코딩 설정 확인
   - 한글 데이터 처리 검증

4. **Job 실행 실패**:
   - 이미지 pull 권한 확인
   - 리소스 할당량 검토
   - 볼륨 마운트 상태 확인

### 성능 튜닝

1. **병렬 처리**: 여러 Job을 파일별로 분할 실행
2. **배치 크기 조정**: 메모리와 처리 속도 최적화
3. **리소스 할당**: CPU/Memory 요청량 최적화
4. **인덱스 비활성화**: 대량 삽입시 임시 비활성화

이 방법을 통해 Kubernetes 환경에서도 안전하고 효율적으로 CSV 데이터를 데이터베이스에 마이그레이션할 수 있습니다.
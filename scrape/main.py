#!/usr/bin/env python3
"""
Fridge2Fork 데이터 처리 애플리케이션 (Kubernetes 환경 최적화)

주요 기능:
- CSV 데이터 마이그레이션 및 정규화
- 데이터베이스 스키마 관리
- 데이터 품질 검증 및 통계
- 헬스체크 및 상태 확인

환경변수로 실행 모드 제어:
- MODE: migrate, stats, health, verify (기본값: migrate)
- MAX_RECORDS: 마이그레이션 시 최대 레코드 수 (테스트용)
- CHUNK_SIZE: 배치 처리 크기 (기본값: 100)
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict
import logging

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 컨테이너 환경에서는 dotenv 없이도 동작
    pass

from scripts.migrate_csv_data import CSVDataMigrator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataManagementSystem:
    """레시피 데이터 관리 시스템"""

    def __init__(self):
        self.migrator = None

    async def initialize(self):
        """데이터베이스 연결 초기화"""
        self.migrator = CSVDataMigrator()
        await self.migrator.initialize()

    async def validate_data_integrity(self) -> Dict:
        """데이터 무결성 검증"""
        if not self.migrator:
            await self.initialize()

        async with self.migrator.async_session() as session:
            try:
                from sqlalchemy import text
            except ImportError:
                logger.error("SQLAlchemy not available")
                return {'error': 'Database not available'}

            # 데이터 무결성 검사 쿼리
            integrity_query = """
            SELECT
                -- 기본 통계
                (SELECT COUNT(*) FROM recipes) as total_recipes,
                (SELECT COUNT(*) FROM ingredients) as total_ingredients,
                (SELECT COUNT(*) FROM recipe_ingredients) as total_relations,

                -- 데이터 품질 검사
                (SELECT COUNT(*) FROM recipes WHERE rcp_ttl IS NULL OR rcp_ttl = '') as recipes_without_title,
                (SELECT COUNT(*) FROM ingredients WHERE name IS NULL OR name = '') as ingredients_without_name,
                (SELECT COUNT(*) FROM recipe_ingredients WHERE quantity_text IS NULL) as relations_without_quantity,

                -- 외래키 무결성 검사
                (SELECT COUNT(*) FROM recipe_ingredients ri
                 LEFT JOIN recipes r ON ri.rcp_sno = r.rcp_sno
                 WHERE r.rcp_sno IS NULL) as orphaned_recipe_relations,
                (SELECT COUNT(*) FROM recipe_ingredients ri
                 LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                 WHERE i.id IS NULL) as orphaned_ingredient_relations,

                -- 중복 데이터 검사
                (SELECT COUNT(*) - COUNT(DISTINCT name) FROM ingredients) as duplicate_ingredients,
                (SELECT COUNT(*) - COUNT(DISTINCT (rcp_sno, ingredient_id)) FROM recipe_ingredients) as duplicate_relations;
            """

            result = await session.execute(text(integrity_query))
            row = result.first()

            return {
                'basic_stats': {
                    'total_recipes': row.total_recipes,
                    'total_ingredients': row.total_ingredients,
                    'total_relations': row.total_relations
                },
                'data_quality': {
                    'recipes_without_title': row.recipes_without_title,
                    'ingredients_without_name': row.ingredients_without_name,
                    'relations_without_quantity': row.relations_without_quantity
                },
                'integrity_issues': {
                    'orphaned_recipe_relations': row.orphaned_recipe_relations,
                    'orphaned_ingredient_relations': row.orphaned_ingredient_relations,
                    'duplicate_ingredients': row.duplicate_ingredients,
                    'duplicate_relations': row.duplicate_relations
                }
            }

    async def analyze_ingredient_distribution(self) -> Dict:
        """재료 분포 분석"""
        if not self.migrator:
            await self.initialize()

        async with self.migrator.async_session() as session:
            try:
                from sqlalchemy import text
            except ImportError:
                logger.error("SQLAlchemy not available")
                return {'error': 'Database not available'}

            # 재료 분포 분석 쿼리
            distribution_query = """
            SELECT
                -- 카테고리별 재료 분포
                (SELECT json_agg(category_stats) FROM (
                    SELECT
                        COALESCE(category, 'unknown') as category,
                        COUNT(*) as ingredient_count
                    FROM ingredients
                    GROUP BY category
                    ORDER BY ingredient_count DESC
                ) category_stats) as category_distribution,

                -- 인기 재료 Top 20
                (SELECT json_agg(popular_ingredients) FROM (
                    SELECT
                        i.name,
                        i.category,
                        COUNT(ri.rcp_sno) as usage_count,
                        COUNT(CASE WHEN ri.importance = 'essential' THEN 1 END) as essential_count
                    FROM ingredients i
                    JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
                    GROUP BY i.id, i.name, i.category
                    ORDER BY usage_count DESC
                    LIMIT 20
                ) popular_ingredients) as top_ingredients,

                -- 레시피당 평균 재료 수
                (SELECT AVG(ingredient_count) FROM (
                    SELECT COUNT(*) as ingredient_count
                    FROM recipe_ingredients
                    GROUP BY rcp_sno
                ) recipe_ingredient_counts) as avg_ingredients_per_recipe,

                -- 중요도별 재료 분포
                (SELECT json_object_agg(importance, count) FROM (
                    SELECT
                        COALESCE(importance, 'normal') as importance,
                        COUNT(*) as count
                    FROM recipe_ingredients
                    GROUP BY importance
                ) importance_dist) as importance_distribution;
            """

            result = await session.execute(text(distribution_query))
            row = result.first()

            return {
                'category_distribution': row.category_distribution or [],
                'top_ingredients': row.top_ingredients or [],
                'avg_ingredients_per_recipe': float(row.avg_ingredients_per_recipe or 0),
                'importance_distribution': row.importance_distribution or {}
            }

    async def get_database_stats(self) -> Dict:
        """데이터베이스 통계 조회"""
        if not self.migrator:
            await self.initialize()

        async with self.migrator.async_session() as session:
            try:
                from sqlalchemy import text
            except ImportError:
                logger.error("SQLAlchemy not available")
                return {'error': 'Database not available'}

            stats_query = """
            SELECT
                (SELECT COUNT(*) FROM recipes) as total_recipes,
                (SELECT COUNT(*) FROM ingredients) as total_ingredients,
                (SELECT COUNT(*) FROM recipe_ingredients) as total_relations,
                (SELECT AVG(total_ing) FROM (
                    SELECT COUNT(*) as total_ing
                    FROM recipe_ingredients
                    GROUP BY rcp_sno
                ) sub) as avg_ingredients_per_recipe;
            """

            result = await session.execute(text(stats_query))
            row = result.first()

            return {
                'total_recipes': row.total_recipes,
                'total_ingredients': row.total_ingredients,
                'total_relations': row.total_relations,
                'avg_ingredients_per_recipe': round(float(row.avg_ingredients_per_recipe or 0), 2)
            }

    async def cleanup(self):
        """리소스 정리"""
        if self.migrator:
            await self.migrator.cleanup()


def print_data_integrity_report(integrity_data: Dict):
    """데이터 무결성 검증 결과 출력"""
    if 'error' in integrity_data:
        print(f"❌ 무결성 검사 실패: {integrity_data['error']}")
        return

    print("\n📊 데이터 무결성 검증 보고서")
    print("=" * 60)

    # 기본 통계
    stats = integrity_data['basic_stats']
    print(f"📈 기본 통계:")
    print(f"   총 레시피: {stats['total_recipes']:,}개")
    print(f"   총 재료: {stats['total_ingredients']:,}개")
    print(f"   총 관계: {stats['total_relations']:,}개")

    # 데이터 품질
    quality = integrity_data['data_quality']
    print(f"\n🔍 데이터 품질:")
    print(f"   제목 없는 레시피: {quality['recipes_without_title']:,}개")
    print(f"   이름 없는 재료: {quality['ingredients_without_name']:,}개")
    print(f"   수량 없는 관계: {quality['relations_without_quantity']:,}개")

    # 무결성 문제
    issues = integrity_data['integrity_issues']
    print(f"\n⚠️ 무결성 문제:")
    print(f"   고아 레시피 관계: {issues['orphaned_recipe_relations']:,}개")
    print(f"   고아 재료 관계: {issues['orphaned_ingredient_relations']:,}개")
    print(f"   중복 재료: {issues['duplicate_ingredients']:,}개")
    print(f"   중복 관계: {issues['duplicate_relations']:,}개")

    # 종합 평가
    total_issues = sum(issues.values()) + sum(quality.values())
    if total_issues == 0:
        print("\n✅ 모든 무결성 검사 통과!")
    else:
        print(f"\n⚠️ 총 {total_issues:,}개의 문제 발견")


def print_ingredient_distribution(distribution_data: Dict):
    """재료 분포 분석 결과 출력"""
    if 'error' in distribution_data:
        print(f"❌ 분포 분석 실패: {distribution_data['error']}")
        return

    print("\n📊 재료 분포 분석 보고서")
    print("=" * 60)

    # 카테고리별 분포
    if distribution_data['category_distribution']:
        print(f"\n📂 카테고리별 분포:")
        for category in distribution_data['category_distribution'][:10]:  # 상위 10개만
            print(f"   {category['category']}: {category['ingredient_count']:,}개")

    # 인기 재료
    if distribution_data['top_ingredients']:
        print(f"\n🏆 인기 재료 Top 10:")
        for i, ingredient in enumerate(distribution_data['top_ingredients'][:10], 1):
            category = ingredient['category'] or 'unknown'
            print(f"   {i:2d}. {ingredient['name']} ({category}): {ingredient['usage_count']:,}회 사용")

    # 평균 재료 수
    avg_ingredients = distribution_data['avg_ingredients_per_recipe']
    print(f"\n📈 평균 재료 수/레시피: {avg_ingredients:.1f}개")

    # 중요도 분포
    if distribution_data['importance_distribution']:
        print(f"\n⭐ 중요도별 분포:")
        for importance, count in distribution_data['importance_distribution'].items():
            print(f"   {importance}: {count:,}개")


def print_database_stats(stats: Dict):
    """데이터베이스 통계 출력"""
    print("\n📊 데이터베이스 통계")
    print("=" * 40)
    print(f"총 레시피 수: {stats['total_recipes']:,}개")
    print(f"총 재료 수: {stats['total_ingredients']:,}개")
    print(f"레시피-재료 연결: {stats['total_relations']:,}개")
    print(f"평균 재료 수/레시피: {stats['avg_ingredients_per_recipe']}개")


async def migrate_mode():
    """CSV 데이터 마이그레이션 모드"""
    logger.info("🚀 CSV 데이터 마이그레이션 시작")

    max_records = int(os.getenv('MAX_RECORDS', '0')) or None
    chunk_size = int(os.getenv('CHUNK_SIZE', '100'))

    migrator = CSVDataMigrator(
        chunk_size=chunk_size,
        max_records=max_records
    )

    try:
        await migrator.initialize()

        # CSV 파일 찾기
        datas_dir = project_root / "datas"
        csv_files = sorted(datas_dir.glob("*.csv"))

        if not csv_files:
            logger.error("❌ CSV 파일을 찾을 수 없습니다!")
            return 1

        # 마이그레이션 실행
        for csv_file in csv_files:
            logger.info(f"📄 {csv_file.name} 처리 중...")
            await migrator.migrate_file(csv_file)

        # 통계 출력
        await migrator.print_statistics()
        logger.info("✅ 마이그레이션 완료!")
        return 0

    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}")
        return 1
    finally:
        await migrator.cleanup()


async def verify_mode():
    """데이터 검증 모드"""
    logger.info("🔍 데이터 무결성 검증 시작")

    system = DataManagementSystem()
    try:
        await system.initialize()

        # 무결성 검증
        integrity_data = await system.validate_data_integrity()
        print_data_integrity_report(integrity_data)

        # 재료 분포 분석
        distribution_data = await system.analyze_ingredient_distribution()
        print_ingredient_distribution(distribution_data)

        return 0

    except Exception as e:
        logger.error(f"❌ 검증 실패: {e}")
        return 1
    finally:
        await system.cleanup()


async def stats_mode():
    """데이터베이스 통계 모드"""
    system = DataManagementSystem()
    try:
        await system.initialize()
        stats = await system.get_database_stats()
        print_database_stats(stats)
        return 0
    except Exception as e:
        logger.error(f"❌ 통계 조회 실패: {e}")
        return 1
    finally:
        await system.cleanup()


async def health_check():
    """헬스 체크"""
    try:
        system = DataManagementSystem()
        await system.initialize()
        stats = await system.get_database_stats()
        await system.cleanup()

        if 'error' in stats:
            logger.error("❌ 헬스 체크 실패")
            return 1

        logger.info("✅ 헬스 체크 성공")
        return 0
    except Exception as e:
        logger.error(f"❌ 헬스 체크 실패: {e}")
        return 1


async def maintenance_mode():
    """유지보수 모드 (컨테이너 유지용)"""
    logger.info("🔧 유지보수 모드 시작")
    logger.info("ℹ️ 데이터 처리 완료, 컨테이너 유지 중...")

    # 헬스 체크만 수행하고 대기
    health_result = await health_check()
    if health_result != 0:
        return health_result

    # 무한 대기 (Kubernetes에서 컨테이너 유지용)
    try:
        while True:
            await asyncio.sleep(300)  # 5분마다 로그
            logger.info("💓 데이터 시스템 실행 중...")
    except KeyboardInterrupt:
        logger.info("⚠️ 유지보수 모드 종료")
        return 0


def print_usage():
    """사용법 출력 (DB 연결 없이 실행 가능)"""
    print("\n🍽️ Fridge2Fork 데이터 마이그레이션 시스템")
    print("=" * 50)
    print("CSV 데이터를 PostgreSQL로 마이그레이션하는 도구")
    print()
    print("📋 사용 가능한 모드:")
    print("  migrate     - CSV 데이터 마이그레이션 실행")
    print("  verify      - 데이터 무결성 검증")
    print("  stats       - 데이터베이스 통계 조회")
    print("  health      - 헬스 체크")
    print("  maintenance - 유지보수 모드 (컨테이너 유지)")
    print("  help        - 이 도움말 표시")
    print()
    print("🔧 환경변수:")
    print("  MODE         - 실행 모드 (기본값: migrate)")
    print("  MAX_RECORDS  - 최대 처리 레코드 수 (0=전체)")
    print("  CHUNK_SIZE   - 배치 처리 크기 (기본값: 100)")
    print()
    print("💾 데이터베이스 설정:")
    print("  DATABASE_URL - 완전한 PostgreSQL URL")
    print("  또는 개별 설정:")
    print("    POSTGRES_SERVER   - 서버 주소")
    print("    POSTGRES_PORT     - 포트 (기본값: 5432)")
    print("    POSTGRES_DB       - 데이터베이스명")
    print("    POSTGRES_USER     - 사용자명")
    print("    POSTGRES_PASSWORD - 비밀번호")
    print()
    print("📝 사용 예시:")
    print("  # 전체 마이그레이션")
    print("  MODE=migrate python main.py")
    print()
    print("  # 테스트용 (1000개만)")
    print("  MODE=migrate MAX_RECORDS=1000 python main.py")
    print()
    print("  # 통계 확인")
    print("  MODE=stats python main.py")
    print()

async def main():
    """메인 함수 - 환경변수로 모드 결정"""
    mode = os.getenv('MODE', 'migrate').lower()

    # 도움말 모드는 DB 연결 없이 실행
    if mode in ['help', '--help', '-h']:
        print_usage()
        return 0

    logger.info(f"🎯 실행 모드: {mode}")

    mode_map = {
        'migrate': migrate_mode,
        'verify': verify_mode,
        'stats': stats_mode,
        'health': health_check,
        'maintenance': maintenance_mode
    }

    if mode in mode_map:
        return await mode_map[mode]()
    else:
        logger.error(f"❌ 알 수 없는 모드: {mode}")
        print_usage()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"🚨 예상치 못한 오류: {e}")
        sys.exit(1)
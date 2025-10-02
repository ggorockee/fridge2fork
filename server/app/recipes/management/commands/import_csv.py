"""
CSV Import Management Command

CSV 파일에서 레시피 데이터를 import
"""

from django.core.management.base import BaseCommand
from recipes.services.csv_import import import_csv_file


class Command(BaseCommand):
    """CSV Import 커맨드"""

    help = 'CSV 파일에서 레시피를 import합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='CSV 파일 경로'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='중복 레시피를 업데이트 (기본: 스킵)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        skip_duplicates = not options['update']

        self.stdout.write(self.style.SUCCESS(f'CSV Import 시작: {csv_file}\n'))

        try:
            result = import_csv_file(csv_file, skip_duplicates=skip_duplicates)

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCSV Import 완료!'
                    f'\n- 성공: {result["success"]}개'
                    f'\n- 중복 스킵: {result["skip"]}개'
                    f'\n- 오류: {result["error"]}개'
                )
            )

            if result['errors']:
                self.stdout.write(self.style.WARNING('\n오류 목록 (최대 10개):'))
                for error in result['errors'][:10]:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  - 레시피 {error["recipe_sno"]}: {error["error"]}'
                        )
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'CSV Import 실패: {str(e)}'))
            raise

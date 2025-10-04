"""
Core 모델 정의

모든 모델이 공통으로 사용하는 추상 베이스 모델을 정의합니다.
"""

from django.db import models


class CommonModel(models.Model):
    """
    모든 모델의 베이스 클래스

    생성일시와 수정일시를 자동으로 관리합니다.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시",
        help_text="레코드가 생성된 시각"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일시",
        help_text="레코드가 마지막으로 수정된 시각"
    )

    class Meta:
        abstract = True  # 추상 클래스로 설정 (DB 테이블 생성하지 않음)

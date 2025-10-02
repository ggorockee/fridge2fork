"""
Ingredient QuerySet 및 Manager
"""

from django.db import models


class IngredientQuerySet(models.QuerySet):
    """Ingredient 커스텀 QuerySet"""

    def search_normalized(self, name):
        """
        정규화된 재료명으로 검색

        Args:
            name: 검색할 정규화 재료명

        Returns:
            QuerySet: 해당 정규화 재료와 연결된 Ingredient들
        """
        return self.filter(normalized_ingredient__name=name)

    def exclude_seasonings(self):
        """
        범용 조미료 제외

        Returns:
            QuerySet: is_common_seasoning=False인 재료들
        """
        return self.exclude(normalized_ingredient__is_common_seasoning=True)

    def essentials_only(self):
        """
        필수 재료만 조회 (범용 조미료 제외)

        Returns:
            QuerySet: 범용 조미료가 아닌 재료들
        """
        return self.exclude_seasonings()

    def by_category(self, category):
        """
        카테고리별 필터링

        Args:
            category: NormalizedIngredient의 카테고리 (MEAT, VEGETABLE 등)

        Returns:
            QuerySet: 해당 카테고리의 재료들
        """
        return self.filter(normalized_ingredient__category=category)


class IngredientManager(models.Manager):
    """Ingredient 커스텀 Manager"""

    def get_queryset(self):
        """커스텀 QuerySet 반환"""
        return IngredientQuerySet(self.model, using=self._db)

    def search_normalized(self, name):
        """정규화된 재료명으로 검색"""
        return self.get_queryset().search_normalized(name)

    def exclude_seasonings(self):
        """범용 조미료 제외"""
        return self.get_queryset().exclude_seasonings()

    def essentials_only(self):
        """필수 재료만 조회"""
        return self.get_queryset().essentials_only()

    def by_category(self, category):
        """카테고리별 필터링"""
        return self.get_queryset().by_category(category)

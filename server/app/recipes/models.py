"""
Recipe 모델 정의

레시피 데이터를 저장하는 모델
"""

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CommonModel

User = get_user_model()


class IngredientCategory(CommonModel):
    """
    재료 카테고리 모델

    NormalizedIngredient의 카테고리를 동적으로 관리
    """

    CATEGORY_TYPE_CHOICES = [
        ('normalized', '정규화 재료 카테고리'),
        ('ingredient', '재료 카테고리'),
    ]

    name = models.CharField(
        max_length=50,
        verbose_name="카테고리명",
        help_text="예: 육류, 채소류, 필수 재료 등"
    )
    code = models.CharField(
        max_length=50,
        verbose_name="코드",
        help_text="시스템 내부 코드 (예: meat, vegetable)"
    )
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default='normalized',
        verbose_name="카테고리 타입",
        help_text="정규화 재료용 또는 재료용"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="아이콘",
        help_text="이모지 또는 아이콘 클래스 (예: 🥩, fas fa-meat)"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="표시 순서",
        help_text="낮을수록 먼저 표시"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화",
        help_text="비활성화 시 선택 불가"
    )
    description = models.TextField(
        blank=True,
        verbose_name="설명",
        help_text="카테고리 설명"
    )

    class Meta:
        verbose_name = "재료 카테고리"
        verbose_name_plural = "재료 카테고리"
        ordering = ['category_type', 'display_order', 'name']
        unique_together = [['code', 'category_type']]
        indexes = [
            models.Index(fields=['category_type', 'is_active'], name='category_type_active_idx'),
            models.Index(fields=['code'], name='category_code_idx'),
        ]

    def __str__(self):
        """카테고리 문자열 표현"""
        return f"{self.name} ({self.get_category_type_display()})"


class Recipe(CommonModel):
    """
    레시피 모델

    원본 CSV 데이터의 필드명을 유지하면서 한글 verbose_name 제공
    """

    recipe_sno = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="레시피 일련번호",
        help_text="원본 RCP_SNO"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="레시피 제목",
        help_text="RCP_TTL"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="요리명",
        help_text="CKG_NM"
    )
    introduction = models.TextField(
        blank=True,
        verbose_name="요리 소개",
        help_text="CKG_IPDC"
    )
    servings = models.CharField(
        max_length=20,
        verbose_name="인분",
        help_text="CKG_INBUN_NM (예: 4.0)"
    )
    difficulty = models.CharField(
        max_length=20,
        verbose_name="난이도",
        help_text="CKG_DODF_NM (예: 아무나)"
    )
    cooking_time = models.CharField(
        max_length=20,
        verbose_name="조리시간",
        help_text="CKG_TIME_NM (예: 30.0)"
    )
    method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="조리방법",
        help_text="CKG_MTH_ACTO_NM"
    )
    situation = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="상황",
        help_text="CKG_STA_ACTO_NM"
    )
    ingredient_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="재료별",
        help_text="CKG_MTRL_ACTO_NM"
    )
    recipe_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="요리종류",
        help_text="CKG_KND_ACTO_NM"
    )
    image_url = models.URLField(
        blank=True,
        verbose_name="이미지 URL",
        help_text="RCP_IMG_URL"
    )
    recipe_url = models.URLField(
        blank=True,
        verbose_name="레시피 URL",
        help_text="만개의 레시피 상세 페이지 URL (https://www.10000recipe.com/recipe/{RCP_SNO})"
    )
    views = models.IntegerField(
        default=0,
        verbose_name="조회수",
        help_text="INQ_CNT"
    )
    recommendations = models.IntegerField(
        default=0,
        verbose_name="추천수",
        help_text="RCMM_CNT"
    )
    scraps = models.IntegerField(
        default=0,
        verbose_name="스크랩수",
        help_text="SRAP_CNT"
    )

    class Meta:
        verbose_name = "레시피"
        verbose_name_plural = "레시피"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name'], name='recipe_name_idx'),
            models.Index(fields=['difficulty'], name='recipe_difficulty_idx'),
            models.Index(fields=['method'], name='recipe_method_idx'),
            models.Index(fields=['situation'], name='recipe_situation_idx'),
            models.Index(fields=['recipe_type'], name='recipe_type_idx'),
            models.Index(fields=['difficulty', 'cooking_time'], name='recipe_difficulty_time_idx'),
            models.Index(fields=['-created_at'], name='recipe_created_idx'),
        ]

    def __str__(self):
        """레시피 문자열 표현"""
        return self.name


class NormalizedIngredient(CommonModel):
    """
    정규화된 재료 모델

    다양한 원본 재료명을 하나의 정규화된 이름으로 통합 관리
    """

    # 하위 호환성을 위한 상수 유지 (deprecated)
    MEAT = 'meat'
    VEGETABLE = 'vegetable'
    SEAFOOD = 'seafood'
    SEASONING = 'seasoning'
    GRAIN = 'grain'
    DAIRY = 'dairy'
    ETC = 'etc'

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="정규화 재료명",
        help_text="통합된 재료명 (예: 돼지고기)"
    )
    category = models.ForeignKey(
        IngredientCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'category_type': 'normalized', 'is_active': True},
        related_name='normalized_ingredients',
        verbose_name="카테고리",
        help_text="재료 분류"
    )
    is_common_seasoning = models.BooleanField(
        default=False,
        verbose_name="범용 조미료",
        help_text="대부분의 레시피에 사용되는 조미료 여부"
    )
    description = models.TextField(
        blank=True,
        verbose_name="설명",
        help_text="관리자용 메모"
    )

    class Meta:
        verbose_name = "정규화 재료"
        verbose_name_plural = "정규화 재료"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category'], name='normalized_category_idx'),
            models.Index(fields=['is_common_seasoning'], name='normalized_seasoning_idx'),
            models.Index(fields=['category', 'is_common_seasoning'], name='normalized_cat_season_idx'),
        ]

    def __str__(self):
        """정규화 재료 문자열 표현"""
        return self.name

    def get_all_variations(self):
        """이 정규화 재료에 연결된 모든 원본 재료 조회"""
        return self.ingredients.all()


class Ingredient(CommonModel):
    """
    재료 모델

    레시피의 재료 정보를 저장하며, 원본 재료명과 정규화된 재료명을 구분
    """

    # 하위 호환성을 위한 상수 유지 (deprecated)
    ESSENTIAL = 'essential'
    SEASONING = 'seasoning'
    OPTIONAL = 'optional'

    # 커스텀 Manager 적용
    from .managers import IngredientManager
    objects = IngredientManager()

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name="레시피",
        help_text="이 재료가 속한 레시피"
    )
    normalized_ingredient = models.ForeignKey(
        NormalizedIngredient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ingredients',
        verbose_name="정규화 재료",
        help_text="연결된 정규화 재료"
    )
    original_name = models.CharField(
        max_length=100,
        verbose_name="원본 재료명",
        help_text="CSV에서 파싱한 원본 재료명"
    )
    normalized_name = models.CharField(
        max_length=100,
        verbose_name="정규화 재료명",
        help_text="매칭을 위해 정규화된 재료명 (기본값: original_name)"
    )
    category = models.ForeignKey(
        IngredientCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'category_type': 'ingredient', 'is_active': True},
        related_name='ingredients',
        verbose_name="카테고리",
        help_text="재료 카테고리 (필수/조미료/선택)"
    )
    quantity = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="수량",
        help_text="재료의 수량 정보 (Phase 2 이후 활용)"
    )
    is_essential = models.BooleanField(
        default=True,
        verbose_name="필수 재료",
        help_text="레시피에 필수적인 재료 여부"
    )

    class Meta:
        verbose_name = "재료"
        verbose_name_plural = "재료"
        ordering = ['recipe', 'category', 'original_name']
        indexes = [
            models.Index(fields=['original_name'], name='ingredient_original_idx'),
            models.Index(fields=['normalized_name'], name='ingredient_normalized_idx'),
            models.Index(fields=['recipe', 'category'], name='ingredient_recipe_cat_idx'),
            models.Index(fields=['normalized_ingredient', 'is_essential'], name='ingredient_norm_ess_idx'),
            models.Index(fields=['category'], name='ingredient_category_idx'),
        ]

    def save(self, *args, **kwargs):
        """저장 시 normalized_name 기본값 설정"""
        if not self.normalized_name:
            self.normalized_name = self.original_name
        super().save(*args, **kwargs)

    def __str__(self):
        """재료 문자열 표현 (단순 표시)"""
        return self.original_name


class Fridge(CommonModel):
    """
    냉장고 모델

    회원과 비회원 모두 사용 가능:
    - 회원: user FK 사용
    - 비회원: session_key 사용
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="사용자",
        help_text="회원인 경우 사용자"
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name="세션 키",
        help_text="비회원인 경우 세션 키"
    )

    class Meta:
        db_table = 'recipes_fridge'
        verbose_name = "냉장고"
        verbose_name_plural = "냉장고"
        # user 또는 session_key 중 하나는 필수
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False) | models.Q(session_key__isnull=False)
                ),
                name='fridge_owner_required'
            )
        ]
        indexes = [
            models.Index(fields=['user'], name='fridge_user_idx'),
            models.Index(fields=['session_key'], name='fridge_session_idx'),
        ]

    def get_normalized_ingredients(self):
        """냉장고의 정규화 재료 목록 반환"""
        return NormalizedIngredient.objects.filter(
            fridgeingredient__fridge=self
        ).distinct()

    def __str__(self):
        """냉장고 문자열 표현"""
        if self.user:
            return f"냉장고 (회원: {self.user.username})"
        return f"냉장고 (세션: {self.session_key})"


class FridgeIngredient(models.Model):
    """
    냉장고-재료 중간 모델

    냉장고에 담긴 재료를 관리
    """

    fridge = models.ForeignKey(
        Fridge,
        on_delete=models.CASCADE,
        verbose_name="냉장고"
    )
    normalized_ingredient = models.ForeignKey(
        NormalizedIngredient,
        on_delete=models.CASCADE,
        verbose_name="정규화 재료"
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="추가 일시"
    )

    class Meta:
        db_table = 'recipes_fridge_ingredient'
        verbose_name = "냉장고 재료"
        verbose_name_plural = "냉장고 재료"
        # 냉장고-재료 unique constraint
        unique_together = [['fridge', 'normalized_ingredient']]
        ordering = ['-added_at']

    def __str__(self):
        """냉장고 재료 문자열 표현"""
        return f"{self.fridge} - {self.normalized_ingredient.name}"

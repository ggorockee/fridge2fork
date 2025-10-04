"""
Recipe 및 Ingredient Admin 설정
"""

from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Recipe, Ingredient, NormalizedIngredient, Fridge, FridgeIngredient, IngredientCategory, RecommendationSettings
from .services.csv_import import import_csv_file


class IngredientInline(admin.TabularInline):
    """Recipe에서 인라인으로 재료 관리"""

    model = Ingredient
    extra = 5
    fields = ('original_name', 'normalized_ingredient', 'is_essential', 'category', 'quantity')
    autocomplete_fields = ['normalized_ingredient']

    def get_queryset(self, request):
        """필수 재료를 먼저 표시"""
        qs = super().get_queryset(request)
        return qs.order_by('-is_essential', 'original_name')


class HasAllNormalizedIngredientsFilter(admin.SimpleListFilter):
    """모든 재료가 정규화된 레시피만 필터"""
    title = '재료 정규화 상태'
    parameter_name = 'ingredient_normalization'

    def lookups(self, request, model_admin):
        return (
            ('all_normalized', '모두 정규화됨'),
            ('has_unnormalized', '정규화 안된 재료 포함'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'all_normalized':
            # 정규화되지 않은 재료가 없는 레시피만
            unnormalized_recipes = Recipe.objects.filter(
                ingredients__normalized_ingredient__isnull=True
            ).values_list('id', flat=True).distinct()
            return queryset.exclude(id__in=unnormalized_recipes)
        if self.value() == 'has_unnormalized':
            # 정규화되지 않은 재료가 있는 레시피
            return queryset.filter(ingredients__normalized_ingredient__isnull=True).distinct()
        return queryset


class LowIngredientCountFilter(admin.SimpleListFilter):
    """재료 개수 기반 필터"""
    title = '재료 개수'
    parameter_name = 'ingredient_count'

    def lookups(self, request, model_admin):
        return (
            ('simple', '간단 (5개 이하)'),
            ('medium', '보통 (6-10개)'),
            ('complex', '복잡 (11개 이상)'),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(ing_count=Count('ingredients'))
        if self.value() == 'simple':
            return queryset.filter(ing_count__lte=5)
        if self.value() == 'medium':
            return queryset.filter(ing_count__gte=6, ing_count__lte=10)
        if self.value() == 'complex':
            return queryset.filter(ing_count__gte=11)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Recipe Admin"""

    list_display = ('image_thumbnail', 'name', 'title', 'get_recipe_link', 'get_ingredient_count', 'get_essential_count', 'difficulty', 'cooking_time', 'views', 'created_at')
    list_filter = ('difficulty', 'method', 'situation', 'recipe_type', HasAllNormalizedIngredientsFilter, LowIngredientCountFilter, 'created_at')
    search_fields = ('name', 'title', 'introduction', 'recipe_sno')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'views', 'recommendations', 'scraps', 'image_preview', 'recipe_sno', 'get_recipe_link', 'get_ingredient_count', 'get_essential_count', 'get_seasoning_count')

    actions = ['validate_recipe_ingredients', 'export_recipe_with_ingredients']

    fieldsets = (
        ('기본 정보', {
            'fields': ('recipe_sno', 'name', 'title', 'introduction', 'image_url', 'image_preview', 'recipe_url', 'get_recipe_link')
        }),
        ('조리 정보', {
            'fields': ('servings', 'difficulty', 'cooking_time', 'method', 'situation')
        }),
        ('분류', {
            'fields': ('ingredient_type', 'recipe_type')
        }),
        ('재료 통계', {
            'fields': ('get_ingredient_count', 'get_essential_count', 'get_seasoning_count'),
            'classes': ('collapse',)
        }),
        ('통계', {
            'fields': ('views', 'recommendations', 'scraps'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [IngredientInline]

    def get_queryset(self, request):
        """재료 개수 최적화"""
        qs = super().get_queryset(request)
        return qs.annotate(
            ingredient_count=Count('ingredients', distinct=True),
            essential_count=Count('ingredients', filter=models.Q(ingredients__is_essential=True), distinct=True)
        )

    def get_ingredient_count(self, obj):
        """전체 재료 수"""
        if hasattr(obj, 'ingredient_count'):
            count = obj.ingredient_count
        else:
            count = obj.ingredients.count()

        return format_html(
            '<span style="font-weight: bold; color: #333;">{} 개</span>',
            count
        )
    get_ingredient_count.short_description = '전체 재료'
    get_ingredient_count.admin_order_field = 'ingredient_count'

    def get_essential_count(self, obj):
        """필수 재료 수"""
        if hasattr(obj, 'essential_count'):
            count = obj.essential_count
        else:
            count = obj.ingredients.filter(is_essential=True).count()

        return format_html(
            '<span style="font-weight: bold; color: green;">{} 개</span>',
            count
        )
    get_essential_count.short_description = '필수 재료'
    get_essential_count.admin_order_field = 'essential_count'

    def get_seasoning_count(self, obj):
        """조미료 수"""
        count = obj.ingredients.filter(
            normalized_ingredient__is_common_seasoning=True
        ).count()

        return format_html(
            '<span style="font-weight: bold; color: orange;">{} 개</span>',
            count
        )
    get_seasoning_count.short_description = '조미료'

    def image_thumbnail(self, obj):
        """목록에서 썸네일 이미지 표시"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;" />',
                obj.image_url
            )
        return format_html('<span style="color: #999;">이미지 없음</span>')
    image_thumbnail.short_description = '이미지'

    def image_preview(self, obj):
        """상세 페이지에서 큰 이미지 미리보기"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />',
                obj.image_url
            )
        return '이미지 없음'
    image_preview.short_description = '이미지 미리보기'

    def get_recipe_link(self, obj):
        """만개의 레시피 링크"""
        if obj.recipe_url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: 500;">🔗 만개의 레시피에서 보기</a>',
                obj.recipe_url
            )
        return '-'
    get_recipe_link.short_description = '레시피 링크'

    @admin.action(description='레시피 재료 유효성 검증')
    def validate_recipe_ingredients(self, request, queryset):
        """선택한 레시피의 재료 유효성 검증"""
        validation_results = []

        for recipe in queryset.prefetch_related('ingredients__normalized_ingredient'):
            issues = []

            # 정규화되지 않은 재료 탐지
            unnormalized = recipe.ingredients.filter(normalized_ingredient__isnull=True)
            if unnormalized.exists():
                issues.append(f"정규화 안됨: {unnormalized.count()}개")

            # 중복 재료 탐지 (normalized_ingredient 기준)
            from collections import Counter
            normalized_ids = [
                ing.normalized_ingredient_id
                for ing in recipe.ingredients.all()
                if ing.normalized_ingredient_id
            ]
            duplicates = [k for k, v in Counter(normalized_ids).items() if v > 1]
            if duplicates:
                issues.append(f"중복: {len(duplicates)}개")

            # 재료가 없는 경우
            if recipe.ingredients.count() == 0:
                issues.append("재료 없음")

            if issues:
                validation_results.append(f"{recipe.name}: {', '.join(issues)}")

        if validation_results:
            message = "검증 실패:\n" + "\n".join(validation_results[:10])
            if len(validation_results) > 10:
                message += f"\n... 외 {len(validation_results) - 10}개"
            self.message_user(request, message, level='warning')
        else:
            self.message_user(request, f'✅ {queryset.count()}개 레시피 모두 정상입니다.', level='success')

    @admin.action(description='JSON으로 내보내기')
    def export_recipe_with_ingredients(self, request, queryset):
        """레시피와 재료를 JSON 형식으로 내보내기"""
        import json
        from django.http import HttpResponse

        recipes_data = []
        for recipe in queryset.prefetch_related('ingredients__normalized_ingredient'):
            ingredients_data = []
            for ing in recipe.ingredients.all():
                ingredients_data.append({
                    'original_name': ing.original_name,
                    'normalized_name': ing.normalized_ingredient.name if ing.normalized_ingredient else None,
                    'category': ing.category,
                    'quantity': ing.quantity,
                    'is_essential': ing.is_essential
                })

            recipes_data.append({
                'recipe_sno': recipe.recipe_sno,
                'name': recipe.name,
                'title': recipe.title,
                'difficulty': recipe.difficulty,
                'cooking_time': recipe.cooking_time,
                'servings': recipe.servings,
                'ingredients': ingredients_data
            })

        # JSON 응답 생성
        response = HttpResponse(content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="recipes_export.json"'
        json.dump(recipes_data, response, ensure_ascii=False, indent=2)

        return response

    def get_urls(self):
        """커스텀 URL 추가"""
        urls = super().get_urls()
        custom_urls = [
            path('csv-upload/', self.admin_site.admin_view(self.csv_upload_view), name='recipes_recipe_csv_upload'),
        ]
        return custom_urls + urls

    def csv_upload_view(self, request):
        """CSV 업로드 뷰"""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')

            if not csv_file:
                messages.error(request, 'CSV 파일을 선택해주세요.')
                return redirect('..')

            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'CSV 파일만 업로드 가능합니다.')
                return redirect('..')

            try:
                # 임시 파일로 저장
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
                    for chunk in csv_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name

                # CSV Import
                skip_duplicates = request.POST.get('skip_duplicates') == 'on'
                result = import_csv_file(tmp_file_path, skip_duplicates=skip_duplicates)

                # 임시 파일 삭제
                os.unlink(tmp_file_path)

                # 결과 메시지
                messages.success(
                    request,
                    f'CSV 업로드 완료! '
                    f'성공: {result["success"]}개, '
                    f'중복 스킵: {result["skip"]}개, '
                    f'오류: {result["error"]}개'
                )

                if result['errors']:
                    for error in result['errors'][:5]:  # 최대 5개만 표시
                        messages.warning(
                            request,
                            f'레시피 {error["recipe_sno"]}: {error["error"]}'
                        )

                return redirect('..')

            except Exception as e:
                messages.error(request, f'CSV 업로드 실패: {str(e)}')
                return redirect('..')

        # GET 요청: 업로드 폼 표시
        context = {
            'title': 'CSV 파일 업로드',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/recipes/csv_upload.html', context)


class NotNormalizedFilter(admin.SimpleListFilter):
    """정규화되지 않은 재료 필터"""
    title = '정규화 상태'
    parameter_name = 'normalized_status'

    def lookups(self, request, model_admin):
        return (
            ('not_normalized', '정규화 안됨'),
            ('normalized', '정규화 완료'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'not_normalized':
            return queryset.filter(normalized_ingredient__isnull=True)
        if self.value() == 'normalized':
            return queryset.filter(normalized_ingredient__isnull=False)
        return queryset


class DuplicateNameFilter(admin.SimpleListFilter):
    """중복 의심 재료명 필터"""
    title = '중복 의심'
    parameter_name = 'duplicate_name'

    def lookups(self, request, model_admin):
        return (
            ('yes', '중복 의심 항목'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # normalized_name이 같은 항목이 2개 이상인 경우
            from django.db.models import Count
            duplicate_names = queryset.values('normalized_name').annotate(
                name_count=Count('id')
            ).filter(name_count__gt=1).values_list('normalized_name', flat=True)

            return queryset.filter(normalized_name__in=duplicate_names)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ingredient Admin"""

    list_display = ('original_name', 'get_normalized_name', 'get_normalized_ingredient', 'get_recipe_name', 'category', 'is_essential', 'created_at')
    list_filter = ('category', 'is_essential', 'normalized_ingredient__category', NotNormalizedFilter, DuplicateNameFilter, 'created_at')
    search_fields = ('original_name', 'normalized_name', 'recipe__name', 'normalized_ingredient__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['normalized_ingredient', 'recipe']

    actions = [
        'bulk_set_normalized_name',
        'find_duplicates',
        'bulk_normalize',
        'auto_normalize_selected',
        'mark_as_essential',
        'mark_as_optional',
        'change_category_to_essential',
        'change_category_to_seasoning',
        'change_category_to_optional',
    ]

    fieldsets = (
        ('재료 정보', {
            'fields': ('recipe', 'original_name', 'normalized_name', 'quantity')
        }),
        ('정규화', {
            'fields': ('normalized_ingredient',),
            'description': '이 재료와 연결된 정규화 재료를 선택하세요'
        }),
        ('분류', {
            'fields': ('category', 'is_essential')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_normalized_name(self, obj):
        """정규화된 이름 표시"""
        if obj.normalized_name:
            return obj.normalized_name
        return format_html('<span style="color: gray;">-</span>')
    get_normalized_name.short_description = '정규화 이름'

    def get_recipe_name(self, obj):
        """레시피 이름 링크"""
        if obj.recipe:
            url = f'/admin/recipes/recipe/{obj.recipe.id}/change/'
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.recipe.name[:30] + '...' if len(obj.recipe.name) > 30 else obj.recipe.name
            )
        return '-'
    get_recipe_name.short_description = '레시피'

    def get_normalized_ingredient(self, obj):
        """정규화 재료 표시"""
        if obj.normalized_ingredient:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.normalized_ingredient.name
            )
        return format_html('<span style="color: red;">✗ 미연결</span>')
    get_normalized_ingredient.short_description = '정규화 재료'

    @admin.action(description='일괄 정규화명 변경')
    def bulk_set_normalized_name(self, request, queryset):
        """선택한 재료들의 normalized_name을 일괄 변경 (및 NormalizedIngredient 연결)"""
        if 'apply' in request.POST:
            # POST 요청: 실제 업데이트 수행
            new_normalized_name = request.POST.get('normalized_name', '').strip()
            auto_link = request.POST.get('auto_link') == 'on'

            if not new_normalized_name:
                self.message_user(request, '정규화 재료명을 입력해주세요.', level='error')
                return

            updated_count = 0
            linked_count = 0
            created_normalized = False

            # 자동 연결이 체크된 경우
            if auto_link:
                # 기본 카테고리 가져오기 (code='etc')
                from .models import IngredientCategory
                default_category = IngredientCategory.objects.filter(
                    code='etc',
                    category_type='normalized'
                ).first()

                # NormalizedIngredient 찾기 또는 생성
                normalized_ingredient, created = NormalizedIngredient.objects.get_or_create(
                    name=new_normalized_name,
                    defaults={
                        'category': default_category,  # 기본 카테고리
                        'description': f'일괄 정규화를 통해 자동 생성됨'
                    }
                )
                created_normalized = created

                # 각 재료에 normalized_name과 normalized_ingredient 모두 업데이트
                for ingredient in queryset:
                    ingredient.normalized_name = new_normalized_name
                    ingredient.normalized_ingredient = normalized_ingredient
                    ingredient.save()
                    updated_count += 1
                    linked_count += 1

                # 성공 메시지
                message = f'✅ {updated_count}개 재료의 정규화명을 "{new_normalized_name}"(으)로 변경하고 연결했습니다.'
                if created_normalized:
                    message += f' (새로운 정규화 재료 생성됨)'
                else:
                    message += f' (기존 정규화 재료 "{normalized_ingredient.name}"에 연결됨)'

                self.message_user(request, message, level='success')
            else:
                # 자동 연결 없이 normalized_name만 업데이트
                updated_count = queryset.update(normalized_name=new_normalized_name)

                self.message_user(
                    request,
                    f'✅ {updated_count}개 재료의 정규화명을 "{new_normalized_name}"(으)로 변경했습니다.',
                    level='success'
                )
            return

        # GET 요청: 중간 확인 페이지 표시
        context = {
            'title': '일괄 정규화명 변경',
            'queryset': queryset,
            'opts': self.model._meta,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        }

        return render(request, 'admin/recipes/bulk_set_normalized_name.html', context)

    @admin.action(description='중복 재료 탐지')
    def find_duplicates(self, request, queryset):
        """유사한 재료명을 가진 Ingredient 찾기"""
        from collections import defaultdict

        duplicates = defaultdict(list)
        for ingredient in queryset:
            # normalized_name으로 그룹화
            if ingredient.normalized_name:
                duplicates[ingredient.normalized_name].append(ingredient)

        duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}

        if duplicate_groups:
            message = f"중복 그룹 발견: {len(duplicate_groups)}개"
            self.message_user(request, message)
        else:
            self.message_user(request, "중복 재료가 없습니다.")

    @admin.action(description='일괄 정규화 제안')
    def bulk_normalize(self, request, queryset):
        """선택한 재료들의 정규화 제안 생성"""
        from recipes.management.commands.analyze_ingredients import Command

        command = Command()
        suggestions = []

        for ingredient in queryset.filter(normalized_ingredient__isnull=True):
            base_name = command.extract_base_name(ingredient.original_name)
            if base_name:
                suggestions.append(f"{ingredient.original_name} → {base_name}")

        if suggestions:
            message = f"정규화 제안: {', '.join(suggestions[:5])}"
            if len(suggestions) > 5:
                message += f" 외 {len(suggestions) - 5}개"
            self.message_user(request, message)
        else:
            self.message_user(request, "정규화 제안을 생성할 수 없습니다.")

    @admin.action(description='자동 정규화 적용')
    def auto_normalize_selected(self, request, queryset):
        """선택한 Ingredient들의 정규화 자동 적용"""
        from recipes.management.commands.analyze_ingredients import Command

        command = Command()
        normalized_count = 0
        created_count = 0

        # 기타 카테고리 미리 조회
        etc_category = IngredientCategory.objects.filter(code='etc', category_type='normalized').first()

        for ingredient in queryset.filter(normalized_ingredient__isnull=True):
            base_name = command.extract_base_name(ingredient.original_name)
            if base_name:
                # 기존 NormalizedIngredient 찾기 또는 생성
                normalized, created = NormalizedIngredient.objects.get_or_create(
                    name=base_name,
                    defaults={'category': ingredient.category if ingredient.category else etc_category}
                )

                # Ingredient에 연결
                ingredient.normalized_ingredient = normalized
                ingredient.normalized_name = base_name
                ingredient.save()

                normalized_count += 1
                if created:
                    created_count += 1

        self.message_user(
            request,
            f'✅ {normalized_count}개 재료 정규화 완료 (새로 생성: {created_count}개)',
            level='success'
        )

    @admin.action(description='필수 재료로 표시')
    def mark_as_essential(self, request, queryset):
        """선택한 재료를 필수 재료로 표시"""
        updated = queryset.update(is_essential=True)
        self.message_user(
            request,
            f'{updated}개 재료를 필수 재료로 표시했습니다.',
            level='success'
        )

    @admin.action(description='선택 재료로 표시')
    def mark_as_optional(self, request, queryset):
        """선택한 재료를 선택 재료로 표시"""
        updated = queryset.update(is_essential=False)
        self.message_user(
            request,
            f'{updated}개 재료를 선택 재료로 표시했습니다.',
            level='success'
        )

    @admin.action(description='카테고리 → 필수 재료로 변경')
    def change_category_to_essential(self, request, queryset):
        """선택한 재료의 카테고리를 필수 재료로 변경"""
        category = IngredientCategory.objects.filter(code='essential', category_type='ingredient').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 필수 재료로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '필수 재료 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 조미료로 변경')
    def change_category_to_seasoning(self, request, queryset):
        """선택한 재료의 카테고리를 조미료로 변경"""
        category = IngredientCategory.objects.filter(code='seasoning', category_type='ingredient').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 조미료로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '조미료 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 선택 재료로 변경')
    def change_category_to_optional(self, request, queryset):
        """선택한 재료의 카테고리를 선택 재료로 변경"""
        category = IngredientCategory.objects.filter(code='optional', category_type='ingredient').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 선택 재료로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '선택 재료 카테고리를 찾을 수 없습니다.', level='error')

    # list_editable 기능 추가를 위한 설정
    list_editable = ('category',)


class NormalizedIngredientInline(admin.TabularInline):
    """NormalizedIngredient에서 관련 Ingredient 표시 (읽기 전용)"""

    model = Ingredient
    extra = 0
    can_delete = False
    fields = ('original_name', 'normalized_name', 'recipe', 'category')
    readonly_fields = ('original_name', 'normalized_name', 'recipe', 'category')
    verbose_name = "관련 재료"
    verbose_name_plural = "관련 재료 목록"


class HasIngredientsFilter(admin.SimpleListFilter):
    """Ingredient가 연결된 항목만 필터링"""
    title = '관련 재료 여부'
    parameter_name = 'has_ingredients'

    def lookups(self, request, model_admin):
        return (
            ('yes', '연결된 재료 있음'),
            ('no', '연결된 재료 없음 (삭제 대상)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.annotate(ing_count=Count('ingredients')).filter(ing_count__gt=0)
        if self.value() == 'no':
            return queryset.annotate(ing_count=Count('ingredients')).filter(ing_count=0)
        return queryset


class HighUsageFilter(admin.SimpleListFilter):
    """사용 빈도 높은 재료 필터"""
    title = '사용 빈도'
    parameter_name = 'usage_frequency'

    def lookups(self, request, model_admin):
        return (
            ('high', '높음 (10회 이상)'),
            ('medium', '중간 (5-9회)'),
            ('low', '낮음 (1-4회)'),
        )

    def queryset(self, request, queryset):
        queryset = queryset.annotate(usage_count=Count('ingredients'))
        if self.value() == 'high':
            return queryset.filter(usage_count__gte=10)
        if self.value() == 'medium':
            return queryset.filter(usage_count__gte=5, usage_count__lt=10)
        if self.value() == 'low':
            return queryset.filter(usage_count__gte=1, usage_count__lt=5)
        return queryset


@admin.register(NormalizedIngredient)
class NormalizedIngredientAdmin(admin.ModelAdmin):
    """NormalizedIngredient Admin"""

    list_display = ('name', 'category', 'is_common_seasoning', 'get_related_count', 'get_usage_count', 'created_at')
    list_filter = ('category', 'is_common_seasoning', HasIngredientsFilter, HighUsageFilter, 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'get_related_count', 'get_usage_count')

    actions = [
        'merge_normalized_ingredients',
        'mark_as_common_seasoning',
        'unmark_as_common_seasoning',
        'export_to_csv',
        'change_category_to_meat',
        'change_category_to_vegetable',
        'change_category_to_seafood',
        'change_category_to_seasoning',
        'change_category_to_grain',
        'change_category_to_dairy',
        'change_category_to_etc',
    ]

    # 자동완성 활성화
    autocomplete_fields = []  # NormalizedIngredient 자체는 자동완성 대상

    fieldsets = (
        ('재료 정보', {
            'fields': ('name', 'category', 'description')
        }),
        ('속성', {
            'fields': ('is_common_seasoning',),
            'description': '범용 조미료는 레시피 추천에서 제외됩니다'
        }),
        ('통계', {
            'fields': ('get_related_count', 'get_usage_count'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [NormalizedIngredientInline]

    def get_queryset(self, request):
        """관련 Ingredient 개수 및 사용 횟수 최적화"""
        qs = super().get_queryset(request)
        return qs.annotate(
            related_count=Count('ingredients', distinct=True),
            usage_count=Count('ingredients', distinct=True)
        )

    def get_related_count(self, obj):
        """관련 Ingredient 개수 표시"""
        if hasattr(obj, 'related_count'):
            count = obj.related_count
        else:
            count = obj.ingredients.count()

        if count > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{} 개</span>',
                count
            )
        return format_html('<span style="color: gray;">0 개</span>')
    get_related_count.short_description = '관련 재료 수'
    get_related_count.admin_order_field = 'related_count'

    def get_usage_count(self, obj):
        """레시피에서 사용된 횟수"""
        if hasattr(obj, 'usage_count'):
            count = obj.usage_count
        else:
            count = obj.ingredients.count()

        if count >= 10:
            color = 'green'
            label = '높음'
        elif count >= 5:
            color = 'orange'
            label = '중간'
        elif count > 0:
            color = 'gray'
            label = '낮음'
        else:
            return format_html('<span style="color: red;">사용 안됨</span>')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({} 회)</span>',
            color, label, count
        )
    get_usage_count.short_description = '사용 빈도'
    get_usage_count.admin_order_field = 'usage_count'

    @admin.action(description='선택한 재료를 하나로 병합')
    def merge_normalized_ingredients(self, request, queryset):
        """선택한 NormalizedIngredient들을 하나로 병합"""
        if queryset.count() < 2:
            self.message_user(request, '병합하려면 최소 2개 이상의 재료를 선택해주세요.', level='warning')
            return

        # 병합 대상 및 통계
        selected = list(queryset.order_by('name'))
        primary = selected[0]  # 첫 번째 항목을 기본으로 유지
        to_merge = selected[1:]

        total_ingredients = sum(
            ing.ingredients.count() for ing in to_merge
        )

        # 확인 메시지
        merge_info = f"'{primary.name}'로 병합됩니다. "
        merge_info += f"병합 대상: {', '.join([ing.name for ing in to_merge])} "
        merge_info += f"(영향받는 Ingredient: {total_ingredients}개)"

        # 실제 병합 수행
        for ingredient in to_merge:
            # 관련 Ingredient들의 normalized_ingredient를 primary로 변경
            ingredient.ingredients.all().update(normalized_ingredient=primary)
            # 병합 대상 삭제
            ingredient.delete()

        self.message_user(
            request,
            f"✅ {merge_info}",
            level='success'
        )

    @admin.action(description='범용 조미료로 표시')
    def mark_as_common_seasoning(self, request, queryset):
        """선택한 재료를 범용 조미료로 표시"""
        updated = queryset.update(is_common_seasoning=True)
        self.message_user(
            request,
            f'{updated}개 재료를 범용 조미료로 표시했습니다.',
            level='success'
        )

    @admin.action(description='범용 조미료 표시 해제')
    def unmark_as_common_seasoning(self, request, queryset):
        """범용 조미료 표시 해제"""
        updated = queryset.update(is_common_seasoning=False)
        self.message_user(
            request,
            f'{updated}개 재료의 범용 조미료 표시를 해제했습니다.',
            level='success'
        )

    @admin.action(description='CSV로 내보내기')
    def export_to_csv(self, request, queryset):
        """선택한 NormalizedIngredient를 CSV로 내보내기"""
        import csv
        from django.http import HttpResponse

        # CSV 응답 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="normalized_ingredients.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', '재료명', '카테고리', '범용조미료', '사용횟수', '생성일'])

        for obj in queryset.annotate(usage_count=Count('ingredients')):
            writer.writerow([
                obj.id,
                obj.name,
                obj.category.name if obj.category else '-',
                '예' if obj.is_common_seasoning else '아니오',
                obj.usage_count,
                obj.created_at.strftime('%Y-%m-%d')
            ])

        return response

    @admin.action(description='카테고리 → 육류로 변경')
    def change_category_to_meat(self, request, queryset):
        """선택한 재료의 카테고리를 육류로 변경"""
        category = IngredientCategory.objects.filter(code='meat', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 육류로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '육류 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 채소류로 변경')
    def change_category_to_vegetable(self, request, queryset):
        """선택한 재료의 카테고리를 채소류로 변경"""
        category = IngredientCategory.objects.filter(code='vegetable', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 채소류로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '채소류 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 해산물로 변경')
    def change_category_to_seafood(self, request, queryset):
        """선택한 재료의 카테고리를 해산물로 변경"""
        category = IngredientCategory.objects.filter(code='seafood', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 해산물로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '해산물 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 조미료로 변경')
    def change_category_to_seasoning(self, request, queryset):
        """선택한 재료의 카테고리를 조미료로 변경"""
        category = IngredientCategory.objects.filter(code='seasoning', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 조미료로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '조미료 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 곡물로 변경')
    def change_category_to_grain(self, request, queryset):
        """선택한 재료의 카테고리를 곡물로 변경"""
        category = IngredientCategory.objects.filter(code='grain', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 곡물로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '곡물 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 유제품로 변경')
    def change_category_to_dairy(self, request, queryset):
        """선택한 재료의 카테고리를 유제품로 변경"""
        category = IngredientCategory.objects.filter(code='dairy', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 유제품로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '유제품 카테고리를 찾을 수 없습니다.', level='error')

    @admin.action(description='카테고리 → 기타로 변경')
    def change_category_to_etc(self, request, queryset):
        """선택한 재료의 카테고리를 기타로 변경"""
        category = IngredientCategory.objects.filter(code='etc', category_type='normalized').first()
        if category:
            updated = queryset.update(category=category)
            self.message_user(
                request,
                f'{updated}개 재료의 카테고리를 기타로 변경했습니다.',
                level='success'
            )
        else:
            self.message_user(request, '기타 카테고리를 찾을 수 없습니다.', level='error')


    # list_editable 기능 추가를 위한 설정
    list_editable = ('category',)


class FridgeIngredientInline(admin.TabularInline):
    """Fridge에서 재료 관리 인라인"""

    model = FridgeIngredient
    extra = 1
    fields = ('normalized_ingredient', 'added_at')
    readonly_fields = ('added_at',)
    autocomplete_fields = ['normalized_ingredient']
    verbose_name = "냉장고 재료"
    verbose_name_plural = "냉장고 재료 목록"


@admin.register(Fridge)
class FridgeAdmin(admin.ModelAdmin):
    """Fridge Admin"""

    list_display = ('get_owner', 'get_ingredient_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at', 'get_ingredient_list')

    fieldsets = (
        ('소유자 정보', {
            'fields': ('user', 'session_key')
        }),
        ('냉장고 재료', {
            'fields': ('get_ingredient_list',),
            'description': '현재 냉장고에 담긴 재료 목록'
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [FridgeIngredientInline]

    def get_queryset(self, request):
        """냉장고 재료 개수 최적화"""
        qs = super().get_queryset(request)
        return qs.annotate(ingredient_count=Count('fridgeingredient'))

    def get_owner(self, obj):
        """소유자 표시 (회원/비회원 구분)"""
        if obj.user:
            return format_html(
                '<span style="color: green;">👤 {}</span>',
                obj.user.username
            )
        return format_html(
            '<span style="color: orange;">🔑 세션 {}</span>',
            obj.session_key[:20] + '...' if len(obj.session_key) > 20 else obj.session_key
        )
    get_owner.short_description = '소유자'

    def get_ingredient_count(self, obj):
        """냉장고 재료 개수 표시"""
        if hasattr(obj, 'ingredient_count'):
            count = obj.ingredient_count
        else:
            count = obj.fridgeingredient_set.count()

        if count > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">🥘 {} 개</span>',
                count
            )
        return format_html('<span style="color: gray;">📭 비어있음</span>')
    get_ingredient_count.short_description = '재료 수'
    get_ingredient_count.admin_order_field = 'ingredient_count'

    def get_ingredient_list(self, obj):
        """냉장고 재료 목록 표시 (읽기 전용 필드)"""
        ingredients = obj.get_normalized_ingredients()

        if not ingredients.exists():
            return format_html('<p style="color: gray;">냉장고가 비어있습니다.</p>')

        items = []
        for ing in ingredients:
            # 카테고리 아이콘
            if ing.category and ing.category.icon:
                category_icon = ing.category.icon
            else:
                category_icon = '📦'

            items.append(f'{category_icon} {ing.name}')

        return format_html('<div>{}</div>', ', '.join(items))
    get_ingredient_list.short_description = '재료 목록'


@admin.register(FridgeIngredient)
class FridgeIngredientAdmin(admin.ModelAdmin):
    """FridgeIngredient Admin"""

    list_display = ('get_owner', 'normalized_ingredient', 'get_category', 'added_at')
    list_filter = ('normalized_ingredient__category', 'added_at')
    search_fields = ('fridge__user__username', 'normalized_ingredient__name')
    ordering = ('-added_at',)
    readonly_fields = ('added_at',)
    autocomplete_fields = ['fridge', 'normalized_ingredient']

    fieldsets = (
        ('냉장고 정보', {
            'fields': ('fridge',)
        }),
        ('재료 정보', {
            'fields': ('normalized_ingredient',)
        }),
        ('시스템 정보', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )

    def get_owner(self, obj):
        """냉장고 소유자 표시"""
        if obj.fridge.user:
            return format_html(
                '<span style="color: green;">👤 {}</span>',
                obj.fridge.user.username
            )
        return format_html(
            '<span style="color: orange;">🔑 세션</span>'
        )
    get_owner.short_description = '소유자'

    def get_category(self, obj):
        """재료 카테고리 표시"""
        # 카테고리 아이콘 (카테고리 객체의 icon 필드 사용 또는 기본값)
        if obj.normalized_ingredient.category and obj.normalized_ingredient.category.icon:
            category_icon = obj.normalized_ingredient.category.icon
        else:
            category_icon = '📦'

        category_name = obj.normalized_ingredient.category.name if obj.normalized_ingredient.category else '미분류'
        return format_html(
            '{} {}',
            category_icon,
            category_name
        )
    get_category.short_description = '카테고리'


@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    """IngredientCategory Admin - 재료 카테고리 관리"""

    list_display = ('name', 'code', 'category_type', 'get_icon_display', 'display_order', 'is_active', 'get_usage_count')
    list_filter = ('category_type', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('category_type', 'display_order', 'name')
    readonly_fields = ('created_at', 'updated_at', 'get_usage_count')

    list_editable = ('display_order', 'is_active')

    fieldsets = (
        ('카테고리 정보', {
            'fields': ('name', 'code', 'category_type', 'icon', 'display_order')
        }),
        ('상태', {
            'fields': ('is_active', 'description')
        }),
        ('통계', {
            'fields': ('get_usage_count',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """사용 횟수 최적화"""
        qs = super().get_queryset(request)
        return qs.annotate(
            normalized_usage=Count('normalized_ingredients', distinct=True),
            ingredient_usage=Count('ingredients', distinct=True)
        )

    def get_icon_display(self, obj):
        """아이콘 표시"""
        if obj.icon:
            return format_html(
                '<span style="font-size: 20px;">{}</span>',
                obj.icon
            )
        return '-'
    get_icon_display.short_description = '아이콘'

    def get_usage_count(self, obj):
        """사용 횟수 표시 (category_type에 따라 다르게)"""
        if obj.category_type == 'normalized':
            if hasattr(obj, 'normalized_usage'):
                count = obj.normalized_usage
            else:
                count = obj.normalized_ingredients.count()
            label = '정규화 재료'
        else:  # ingredient
            if hasattr(obj, 'ingredient_usage'):
                count = obj.ingredient_usage
            else:
                count = obj.ingredients.count()
            label = '재료'

        if count > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{} {} 개</span>',
                label, count
            )
        return format_html('<span style="color: gray;">사용 안됨</span>')
    get_usage_count.short_description = '사용 횟수'


@admin.register(RecommendationSettings)
class RecommendationSettingsAdmin(admin.ModelAdmin):
    """RecommendationSettings Admin - 레시피 추천 설정 관리"""

    list_display = ('min_match_rate', 'default_algorithm', 'default_limit', 'exclude_seasonings_default', 'updated_at')
    readonly_fields = ('updated_at', 'get_algorithm_explanation')

    fieldsets = (
        ('📊 추천 알고리즘 설정', {
            'fields': ('default_algorithm', 'get_algorithm_explanation', 'min_match_rate'),
            'description': (
                '<strong>레시피 추천 API의 기본 알고리즘 및 최소 매칭률 설정</strong><br>'
                '사용자가 API 호출 시 알고리즘을 지정하지 않으면 여기 설정된 값을 사용합니다.'
            )
        }),
        ('⚙️ 기본 옵션', {
            'fields': ('default_limit', 'exclude_seasonings_default'),
            'description': '추천 레시피 기본 개수 및 조미료 제외 여부 설정'
        }),
        ('🕐 시스템 정보', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def get_algorithm_explanation(self, obj):
        """알고리즘 설명 표시 (두 알고리즘 모두 표시)"""
        return format_html(
            '<div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 10px 0;">'
            '<h2 style="margin-top: 0; color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px;">📚 유사도 알고리즘 비교</h2>'

            # Jaccard 설명
            '<div style="background: #f0f8ff; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; border-radius: 4px;">'
            '<h3 style="margin-top: 0; color: #1976D2;">🔵 Jaccard (자카드 유사도) - 현재 권장</h3>'
            '<p><strong>📐 계산 방식:</strong> 교집합 / 합집합</p>'
            '<p><strong>📝 수식:</strong> <code>|매칭된 재료| / |전체 재료(사용자 + 레시피 - 중복)|</code></p>'
            '<p><strong>📊 예시:</strong></p>'
            '<ul style="margin: 5px 0; line-height: 1.6;">'
            '<li>사용자 재료: 돼지고기, 배추, 두부 (3개)</li>'
            '<li>레시피 재료: 돼지고기, 배추, 김치, 고춧가루 (4개)</li>'
            '<li>매칭: 돼지고기, 배추 (2개)</li>'
            '<li><strong>→ 유사도: 2 / 5 = 0.4 (40%)</strong></li>'
            '</ul>'
            '<p><strong>✅ 장점:</strong> 직관적이고 이해하기 쉬움. 재료가 얼마나 겹치는지 명확하게 표현</p>'
            '<p><strong>⚠️ 단점:</strong> 레시피 재료가 많을수록 유사도가 낮아지는 경향</p>'
            '<p><strong>💡 권장 상황:</strong> 간단한 레시피 위주 추천, 재료 낭비 최소화, 직관적인 매칭</p>'
            '</div>'

            # Cosine 설명
            '<div style="background: #fff3e0; padding: 15px; border-left: 4px solid #FF9800; margin: 15px 0; border-radius: 4px;">'
            '<h3 style="margin-top: 0; color: #F57C00;">🟠 Cosine (코사인 유사도)</h3>'
            '<p><strong>📐 계산 방식:</strong> 벡터 간 각도 측정 (방향성)</p>'
            '<p><strong>📝 수식:</strong> <code>|매칭된 재료| / (√사용자_재료_수 × √레시피_재료_수)</code></p>'
            '<p><strong>📊 예시:</strong></p>'
            '<ul style="margin: 5px 0; line-height: 1.6;">'
            '<li>사용자 재료: 돼지고기, 배추, 두부 (3개)</li>'
            '<li>레시피 재료: 돼지고기, 배추, 김치, 고춧가루 (4개)</li>'
            '<li>매칭: 돼지고기, 배추 (2개)</li>'
            '<li><strong>→ 유사도: 2 / (√3 × √4) = 2 / 3.46 = 0.577 (57.7%)</strong></li>'
            '</ul>'
            '<p><strong>✅ 장점:</strong> 재료 개수에 덜 민감. 복잡한 레시피도 공평하게 평가</p>'
            '<p><strong>⚠️ 단점:</strong> 수학적으로 다소 복잡함</p>'
            '<p><strong>💡 권장 상황:</strong> 다양한 복잡도의 레시피 균형있게 추천, 공평한 평가</p>'
            '</div>'

            # 비교 표
            '<div style="background: white; padding: 15px; border: 1px solid #ddd; margin: 15px 0; border-radius: 4px;">'
            '<h3 style="margin-top: 0; color: #333;">⚖️ 비교 요약</h3>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<thead>'
            '<tr style="background: #f5f5f5;">'
            '<th style="padding: 10px; border: 1px solid #ddd; text-align: left;">항목</th>'
            '<th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Jaccard</th>'
            '<th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Cosine</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            '<tr>'
            '<td style="padding: 10px; border: 1px solid #ddd;"><strong>직관성</strong></td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐⭐ 매우 높음</td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐ 보통</td>'
            '</tr>'
            '<tr style="background: #fafafa;">'
            '<td style="padding: 10px; border: 1px solid #ddd;"><strong>재료 개수 영향</strong></td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐ 많이 받음</td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐⭐ 적게 받음</td>'
            '</tr>'
            '<tr>'
            '<td style="padding: 10px; border: 1px solid #ddd;"><strong>기본값 권장</strong></td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐⭐ 권장</td>'
            '<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">⭐⭐ 선택 가능</td>'
            '</tr>'
            '</tbody>'
            '</table>'
            '</div>'

            '<p style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-left: 4px solid #1976D2; border-radius: 4px;">'
            '<strong>💬 참고:</strong> 위 드롭다운에서 알고리즘을 선택하면 API 기본값으로 사용됩니다. '
            '사용자가 API 호출 시 직접 알고리즘을 지정할 수도 있습니다.'
            '</p>'
            '</div>'
        )

    get_algorithm_explanation.short_description = '알고리즘 상세 설명'

    def has_add_permission(self, request):
        """추가 불가 (Singleton)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 불가 (Singleton)"""
        return False

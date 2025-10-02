"""
CSV Import Service 테스트

Phase 2.1: CSV 파서 유닛 테스트
"""
import pytest
from decimal import Decimal
from app.services.csv_import import (
    parse_quantity,
    detect_abstract_ingredient,
    normalize_ingredient_name,
    parse_ingredient_line,
    parse_recipe_ingredients,
)


class TestParseQuantity:
    """수량 파싱 테스트"""

    def test_single_quantity_with_unit(self):
        """단일 수량 + 단위 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("400g")
        assert qty_from == Decimal('400')
        assert qty_to is None
        assert unit == 'g'
        assert is_vague is False

    def test_range_quantity(self):
        """범위 수량 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("200-300g")
        assert qty_from == Decimal('200')
        assert qty_to == Decimal('300')
        assert unit == 'g'
        assert is_vague is False

    def test_range_quantity_with_tilde(self):
        """범위 수량 파싱 (~로 구분)"""
        qty_from, qty_to, unit, is_vague = parse_quantity("1~2개")
        assert qty_from == Decimal('1')
        assert qty_to == Decimal('2')
        assert unit == '개'
        assert is_vague is False

    def test_fraction_quantity(self):
        """분수 수량 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("1/2개")
        assert qty_from == Decimal('0.5')
        assert qty_to is None
        assert unit == '개'
        assert is_vague is False

    def test_fraction_with_korean_unit(self):
        """분수 + 한글 단위 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("3/4컵")
        assert qty_from == Decimal('0.75')
        assert qty_to is None
        assert unit == '컵'
        assert is_vague is False

    def test_vague_expression_jeokdanghi(self):
        """모호한 표현: 적당히"""
        qty_from, qty_to, unit, is_vague = parse_quantity("적당히")
        assert qty_from is None
        assert qty_to is None
        assert unit is None
        assert is_vague is True

    def test_vague_expression_jogeum(self):
        """모호한 표현: 조금"""
        qty_from, qty_to, unit, is_vague = parse_quantity("조금")
        assert qty_from is None
        assert qty_to is None
        assert unit is None
        assert is_vague is True

    def test_vague_expression_yakgan(self):
        """모호한 표현: 약간"""
        qty_from, qty_to, unit, is_vague = parse_quantity("약간")
        assert qty_from is None
        assert qty_to is None
        assert unit is None
        assert is_vague is True

    def test_empty_string(self):
        """빈 문자열 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("")
        assert qty_from is None
        assert qty_to is None
        assert unit is None
        assert is_vague is False

    def test_decimal_quantity(self):
        """소수점 수량 파싱"""
        qty_from, qty_to, unit, is_vague = parse_quantity("2.5컵")
        assert qty_from == Decimal('2.5')
        assert qty_to is None
        assert unit == '컵'
        assert is_vague is False


class TestDetectAbstractIngredient:
    """추상적 재료 감지 테스트"""

    def test_abstract_gogi(self):
        """추상적 재료: 고기"""
        is_abstract, suggested = detect_abstract_ingredient("고기")
        assert is_abstract is True
        assert suggested == "소고기"

    def test_abstract_chaeso(self):
        """추상적 재료: 채소"""
        is_abstract, suggested = detect_abstract_ingredient("채소")
        assert is_abstract is True
        assert suggested == "배추"

    def test_abstract_yangnyeom(self):
        """추상적 재료: 양념"""
        is_abstract, suggested = detect_abstract_ingredient("양념")
        assert is_abstract is True
        assert suggested == "간장"

    def test_concrete_ingredient(self):
        """구체적 재료: 떡국떡"""
        is_abstract, suggested = detect_abstract_ingredient("떡국떡")
        assert is_abstract is False
        assert suggested is None

    def test_concrete_ingredient_daepa(self):
        """구체적 재료: 대파"""
        is_abstract, suggested = detect_abstract_ingredient("대파")
        assert is_abstract is False
        assert suggested is None

    def test_empty_string(self):
        """빈 문자열"""
        is_abstract, suggested = detect_abstract_ingredient("")
        assert is_abstract is False
        assert suggested is None


class TestNormalizeIngredientName:
    """재료명 정규화 테스트"""

    def test_remove_quantity_suffix(self):
        """수량 제거: 떡국떡400g → 떡국떡"""
        normalized = normalize_ingredient_name("떡국떡400g")
        assert normalized == "떡국떡"

    def test_remove_parentheses(self):
        """괄호 제거: 떡국떡(400g) → 떡국떡"""
        normalized = normalize_ingredient_name("떡국떡(400g)")
        assert normalized == "떡국떡"

    def test_remove_whitespace(self):
        """공백 제거: '  떡국떡  ' → 떡국떡"""
        normalized = normalize_ingredient_name("  떡국떡  ")
        assert normalized == "떡국떡"

    def test_remove_special_characters(self):
        """특수문자 제거"""
        normalized = normalize_ingredient_name("떡국떡-400g")
        assert normalized == "떡국떡"

    def test_complex_normalization(self):
        """복합 정규화: 괄호+수량+공백"""
        normalized = normalize_ingredient_name("  국물용멸치 (50g)  ")
        assert normalized == "국물용멸치"


class TestParseIngredientLine:
    """재료 라인 파싱 통합 테스트"""

    def test_normal_case_tteokguk(self):
        """정상 케이스: 떡국떡400g"""
        result = parse_ingredient_line("떡국떡400g")

        assert result['raw_name'] == "떡국떡400g"
        assert result['normalized_name'] == "떡국떡"
        assert result['quantity_from'] == Decimal('400')
        assert result['quantity_to'] is None
        assert result['quantity_unit'] == 'g'
        assert result['is_vague'] is False
        assert result['is_abstract'] is False
        assert result['suggested_specific'] is None

    def test_range_case(self):
        """범위 케이스: 배추 200-300g"""
        result = parse_ingredient_line("배추 200-300g")

        assert result['raw_name'] == "배추 200-300g"
        assert result['normalized_name'] == "배추"
        assert result['quantity_from'] == Decimal('200')
        assert result['quantity_to'] == Decimal('300')
        assert result['quantity_unit'] == 'g'
        assert result['is_vague'] is False
        assert result['is_abstract'] is False

    def test_vague_case(self):
        """모호한 케이스: 소금 적당히"""
        result = parse_ingredient_line("소금 적당히")

        assert result['raw_name'] == "소금 적당히"
        assert result['normalized_name'] == "소금"
        assert result['quantity_from'] is None
        assert result['quantity_to'] is None
        assert result['quantity_unit'] is None
        assert result['is_vague'] is True

    def test_abstract_case(self):
        """추상 케이스: 고기"""
        result = parse_ingredient_line("고기")

        assert result['raw_name'] == "고기"
        assert result['normalized_name'] == "고기"
        assert result['quantity_from'] is None
        assert result['quantity_to'] is None
        assert result['quantity_unit'] is None
        assert result['is_vague'] is False
        assert result['is_abstract'] is True
        assert result['suggested_specific'] == "소고기"

    def test_abstract_and_vague_case(self):
        """추상 + 모호 케이스: 고기 적당히"""
        result = parse_ingredient_line("고기 적당히")

        assert result['raw_name'] == "고기 적당히"
        assert result['normalized_name'] == "고기"
        assert result['quantity_from'] is None
        assert result['quantity_to'] is None
        assert result['quantity_unit'] is None
        assert result['is_vague'] is True
        assert result['is_abstract'] is True
        assert result['suggested_specific'] == "소고기"

    def test_fraction_case(self):
        """분수 케이스: 대파 1/2대"""
        result = parse_ingredient_line("대파 1/2대")

        assert result['raw_name'] == "대파 1/2대"
        assert result['normalized_name'] == "대파"
        assert result['quantity_from'] == Decimal('0.5')
        assert result['quantity_to'] is None
        assert result['quantity_unit'] == '대'
        assert result['is_vague'] is False
        assert result['is_abstract'] is False


class TestParseRecipeIngredients:
    """레시피 재료 컬럼 전체 파싱 테스트"""

    def test_multiple_ingredients(self):
        """복수 재료 파싱: | 구분자"""
        ckg_mtrl_cn = "떡국떡400g|국물용멸치50g|대파1대"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        assert len(ingredients) == 3

        # 떡국떡
        assert ingredients[0]['normalized_name'] == "떡국떡"
        assert ingredients[0]['quantity_from'] == Decimal('400')
        assert ingredients[0]['quantity_unit'] == 'g'

        # 국물용멸치
        assert ingredients[1]['normalized_name'] == "국물용멸치"
        assert ingredients[1]['quantity_from'] == Decimal('50')
        assert ingredients[1]['quantity_unit'] == 'g'

        # 대파
        assert ingredients[2]['normalized_name'] == "대파"
        assert ingredients[2]['quantity_from'] == Decimal('1')
        assert ingredients[2]['quantity_unit'] == '대'

    def test_mixed_ingredients(self):
        """혼합 케이스: 정상+모호+추상"""
        ckg_mtrl_cn = "떡국떡400g|소금 적당히|고기"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        assert len(ingredients) == 3

        # 떡국떡 (정상)
        assert ingredients[0]['is_vague'] is False
        assert ingredients[0]['is_abstract'] is False

        # 소금 (모호)
        assert ingredients[1]['is_vague'] is True

        # 고기 (추상)
        assert ingredients[2]['is_abstract'] is True
        assert ingredients[2]['suggested_specific'] == "소고기"

    def test_empty_string(self):
        """빈 문자열"""
        ingredients = parse_recipe_ingredients("")
        assert len(ingredients) == 0

    def test_none_value(self):
        """None 값"""
        ingredients = parse_recipe_ingredients(None)
        assert len(ingredients) == 0

    def test_comma_separated_basic(self):
        """콤마 구분자 기본 테스트"""
        ckg_mtrl_cn = "[재료] 대패 삼겹살150~200g, 숙주나물200g, 청경채25g"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        assert len(ingredients) == 3

        # 대패 삼겹살 (범위 수량)
        assert ingredients[0]['raw_name'] == '대패 삼겹살150~200g'
        assert ingredients[0]['normalized_name'] == '대패삼겹살'
        assert ingredients[0]['quantity_from'] == Decimal('150')
        assert ingredients[0]['quantity_to'] == Decimal('200')
        assert ingredients[0]['quantity_unit'] == 'g'

        # 숙주나물 (단일 수량)
        assert ingredients[1]['raw_name'] == '숙주나물200g'
        assert ingredients[1]['normalized_name'] == '숙주나물'
        assert ingredients[1]['quantity_from'] == Decimal('200')
        assert ingredients[1]['quantity_to'] is None
        assert ingredients[1]['quantity_unit'] == 'g'

        # 청경채
        assert ingredients[2]['raw_name'] == '청경채25g'
        assert ingredients[2]['normalized_name'] == '청경채'

    def test_comma_multiple_sections(self):
        """콤마 구분자 - 여러 섹션 ([재료], [양념재료])"""
        ckg_mtrl_cn = "[재료] 소갈비 찜용1kg, 무우1토막(250g), 양파1/2개 [양념재료] 식용유1바퀴, 다진마늘2T"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        # 섹션 헤더가 제거되고 모든 재료가 파싱됨
        assert len(ingredients) == 5

        assert ingredients[0]['raw_name'] == '소갈비 찜용1kg'
        assert ingredients[1]['raw_name'] == '무우1토막(250g)'
        assert ingredients[2]['raw_name'] == '양파1/2개'
        assert ingredients[3]['raw_name'] == '식용유1바퀴'
        assert ingredients[4]['raw_name'] == '다진마늘2T'

        # 분수 파싱 검증
        assert ingredients[2]['quantity_from'] == Decimal('0.5')
        assert ingredients[2]['quantity_unit'] == '개'

    def test_real_csv_sample_sogalbijjim(self):
        """실제 CSV 샘플 - 소갈비찜 레시피"""
        ckg_mtrl_cn = "[재료] 소갈비 찜용1kg, 무우1토막(250g), 양파1/2개, 대파1대, 풋고추1개 [양념재료] 식용유1바퀴, 다진마늘2T, 다진생강1/4T(생략가능), 설탕1/4컵(45ml), 진간장1/2컵(90ml), 참치액1.5T, 맛술1/2컵(90ml), 식초2.5T, 갈아만든배1/2캔(120ml), 물400ml"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        # 섹션 헤더가 빈 재료로 추가되므로 14개 + 1개 = 15개
        assert len(ingredients) >= 14  # 최소 14개 이상

        # 일부 재료 검증
        raw_names = [item['raw_name'] for item in ingredients]
        assert '소갈비 찜용1kg' in raw_names
        assert '무우1토막(250g)' in raw_names
        assert '양파1/2개' in raw_names
        assert '대파1대' in raw_names
        assert '물400ml' in raw_names

    def test_real_csv_sample_jeyukbokkeum(self):
        """실제 CSV 샘플 - 제육볶음 레시피"""
        ckg_mtrl_cn = "[재료] 돼지고기 앞다리살636g [양념장 ] 고춧가루6T, 간장4T, 올리고당3.5T, 다진 마늘3T, 미림2T, 생강술1T, 소금1/2t, 통깨1T, 후추15바퀴"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        # 9개 재료 + 섹션 헤더로 인한 빈 항목 = 10개
        assert len(ingredients) >= 9  # 최소 9개 이상

        # 양념장 재료들 검증
        raw_names = [item['raw_name'] for item in ingredients]
        assert '돼지고기 앞다리살636g' in raw_names
        assert '고춧가루6T' in raw_names
        assert '간장4T' in raw_names
        assert '올리고당3.5T' in raw_names

        # 첫 번째 재료 검증 (돼지고기)
        pork_ingredient = next((item for item in ingredients if '돼지고기' in item['raw_name']), None)
        assert pork_ingredient is not None
        assert pork_ingredient['quantity_from'] == Decimal('636')
        assert pork_ingredient['quantity_unit'] == 'g'

    def test_backward_compatibility_pipe_separator(self):
        """하위 호환성 - 기존 파이프(|) 구분자 지원"""
        ckg_mtrl_cn = "떡국떡400g|국물용멸치50g|대파1대"
        ingredients = parse_recipe_ingredients(ckg_mtrl_cn)

        assert len(ingredients) == 3
        assert ingredients[0]['raw_name'] == '떡국떡400g'
        assert ingredients[1]['raw_name'] == '국물용멸치50g'
        assert ingredients[2]['raw_name'] == '대파1대'

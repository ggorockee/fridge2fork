"""
한국어 재료 정규화 모듈
레시피의 재료 정보를 구조화된 데이터로 변환
예: "설탕 2스푼" → {"name": "설탕", "quantity": 2.0, "unit": "큰술", "original": "설탕 2스푼"}
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import NORMALIZATION_PATTERNS

# 로깅 설정
logger = logging.getLogger(__name__)

@dataclass
class NormalizedIngredient:
    """정규화된 재료 데이터 클래스"""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    original_text: str = ""
    confidence: float = 1.0  # 정규화 신뢰도 (0-1)

class IngredientNormalizer:
    """한국어 재료 정규화 클래스"""

    def __init__(self):
        self.patterns = NORMALIZATION_PATTERNS['quantity_patterns']
        self.unit_mapping = NORMALIZATION_PATTERNS['unit_mapping']
        self.ingredient_mapping = NORMALIZATION_PATTERNS['ingredient_mapping']
        self.vague_quantities = NORMALIZATION_PATTERNS['vague_quantities']

        # 컴파일된 정규표현식 패턴
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.patterns.items()
        }

        # 모호한 수량 표현 패턴
        vague_pattern = '|'.join(self.vague_quantities.keys())
        self.vague_pattern = re.compile(f'({vague_pattern})', re.IGNORECASE)

    def normalize_ingredient(self, ingredient_text: str) -> NormalizedIngredient:
        """
        개별 재료 텍스트를 정규화합니다.

        Args:
            ingredient_text: 원본 재료 텍스트 (예: "양파 1개", "설탕 2큰술")

        Returns:
            NormalizedIngredient: 정규화된 재료 정보
        """
        if not ingredient_text or not ingredient_text.strip():
            return NormalizedIngredient(
                name="",
                original_text=ingredient_text,
                confidence=0.0
            )

        text = ingredient_text.strip()
        original_text = text

        # 1. 수량과 단위 추출
        quantity, unit, remaining_text = self._extract_quantity_and_unit(text)

        # 2. 재료명 추출 및 정규화
        ingredient_name = self._extract_and_normalize_name(remaining_text)

        # 3. 신뢰도 계산
        confidence = self._calculate_confidence(ingredient_name, quantity, unit)

        return NormalizedIngredient(
            name=ingredient_name,
            quantity=quantity,
            unit=unit,
            original_text=original_text,
            confidence=confidence
        )

    def normalize_ingredient_list(self, ingredients: List[str]) -> List[NormalizedIngredient]:
        """
        재료 리스트를 일괄 정규화합니다.

        Args:
            ingredients: 재료 텍스트 리스트

        Returns:
            List[NormalizedIngredient]: 정규화된 재료 리스트
        """
        normalized_ingredients = []

        for ingredient_text in ingredients:
            try:
                normalized = self.normalize_ingredient(ingredient_text)
                normalized_ingredients.append(normalized)
            except Exception as e:
                logger.warning(f"재료 정규화 실패: {ingredient_text}, 오류: {e}")
                # 실패한 경우에도 원본 텍스트는 보존
                normalized_ingredients.append(NormalizedIngredient(
                    name=ingredient_text,
                    original_text=ingredient_text,
                    confidence=0.1
                ))

        return normalized_ingredients

    def _extract_quantity_and_unit(self, text: str) -> Tuple[Optional[float], Optional[str], str]:
        """
        텍스트에서 수량과 단위를 추출합니다.

        Returns:
            Tuple[quantity, unit, remaining_text]
        """
        # 1. 정확한 수량 패턴 매칭
        for pattern_name, pattern in self.compiled_patterns.items():
            match = pattern.search(text)
            if match:
                quantity_str = match.group(1)
                unit = match.group(2)

                # 수량 변환
                quantity = self._convert_quantity(quantity_str, pattern_name)

                # 단위 표준화
                normalized_unit = self._normalize_unit(unit)

                # 매칭된 부분 제거
                remaining_text = text.replace(match.group(0), '').strip()

                return quantity, normalized_unit, remaining_text

        # 2. 모호한 수량 표현 검사
        vague_match = self.vague_pattern.search(text)
        if vague_match:
            vague_expr = vague_match.group(1)
            quantity = self.vague_quantities.get(vague_expr, 1.0)
            remaining_text = text.replace(vague_match.group(0), '').strip()
            return quantity, None, remaining_text

        # 3. 수량 정보가 없는 경우
        return None, None, text

    def _convert_quantity(self, quantity_str: str, pattern_type: str) -> float:
        """수량 문자열을 숫자로 변환합니다."""
        try:
            if pattern_type == 'fraction':
                # 분수 처리 (예: "1/2")
                parts = quantity_str.split('/')
                return float(parts[0]) / float(parts[1])
            elif pattern_type == 'range':
                # 범위 처리 (예: "2~3") - 평균값 사용
                parts = quantity_str.split('~')
                return (float(parts[0]) + float(parts[1])) / 2
            else:
                # 정수 또는 소수
                return float(quantity_str)
        except (ValueError, ZeroDivisionError):
            logger.warning(f"수량 변환 실패: {quantity_str}")
            return 1.0

    def _normalize_unit(self, unit: str) -> str:
        """단위를 표준화합니다."""
        if not unit:
            return None

        # 단위 매핑 적용
        normalized = self.unit_mapping.get(unit, unit)

        # 리터를 ml로 변환
        if normalized == 'ml' and unit == 'L':
            # 이 경우 수량도 1000배 해야 하는데, 여기서는 단위만 처리
            pass

        return normalized

    def _extract_and_normalize_name(self, text: str) -> str:
        """재료명을 추출하고 정규화합니다."""
        if not text:
            return ""

        # 기본 정리: 공백, 특수문자 정리
        name = text.strip()

        # 괄호 안의 설명 제거 (예: "양파(중간크기)" → "양파")
        name = re.sub(r'\([^)]*\)', '', name).strip()

        # 재료명 매핑 적용
        for original, normalized in self.ingredient_mapping.items():
            if original in name:
                name = name.replace(original, normalized)

        # 추가 정리
        name = re.sub(r'\s+', ' ', name)  # 연속 공백 제거
        name = name.strip('.,()[]{}')  # 끝의 특수문자 제거

        return name

    def _calculate_confidence(self, name: str, quantity: Optional[float], unit: Optional[str]) -> float:
        """정규화 결과의 신뢰도를 계산합니다."""
        confidence = 1.0

        # 재료명이 비어있거나 너무 짧으면 신뢰도 감소
        if not name or len(name) < 2:
            confidence *= 0.3

        # 수량 정보가 없으면 약간 감소
        if quantity is None:
            confidence *= 0.8

        # 단위 정보가 없으면 약간 감소
        if unit is None and quantity is not None:
            confidence *= 0.9

        return max(0.1, confidence)  # 최소 신뢰도 보장

def test_normalizer():
    """정규화 테스트 함수"""
    normalizer = IngredientNormalizer()

    test_cases = [
        "양파 1개",
        "설탕 2큰술",
        "소금 약간",
        "물 500ml",
        "당근(중간크기) 1/2개",
        "대파 2~3대",
        "올리브오일 적당히",
        "닭고기 200g",
        "밀가루"
    ]

    print("=== 한국어 재료 정규화 테스트 ===")
    for test_case in test_cases:
        result = normalizer.normalize_ingredient(test_case)
        print(f"원본: {test_case}")
        print(f"정규화: 이름={result.name}, 수량={result.quantity}, 단위={result.unit}, 신뢰도={result.confidence:.2f}")
        print("-" * 50)

if __name__ == "__main__":
    test_normalizer()
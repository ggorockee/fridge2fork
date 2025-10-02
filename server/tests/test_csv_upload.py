"""
CSV 업로드 통합 테스트

RFC 4180 표준 CSV 파싱이 올바르게 동작하는지 검증
"""
import csv
import io


def test_csv_parsing_with_comma_in_field():
    """CSV 필드 내부에 콤마가 있는 경우 올바르게 파싱되는지 테스트"""

    # 실제 CSV 데이터 예시
    csv_data = '''RCP_SNO,RCP_TTL,CKG_MTRL_CN
7039921,대패삼겹살숙주볶음,"[재료] 대패 삼겹살150~200g, 숙주나물200g, 청경채25g"
7022417,제육볶음,"[재료] 돼지고기 앞다리살636g [양념장 ] 고춧가루6T, 간장4T"'''

    # csv.DictReader로 파싱
    csv_file = io.StringIO(csv_data)
    reader = csv.DictReader(csv_file)
    rows = list(reader)

    # 검증
    assert len(rows) == 2

    # 첫 번째 행
    row1 = rows[0]
    assert row1['RCP_SNO'] == '7039921'
    assert row1['RCP_TTL'] == '대패삼겹살숙주볶음'
    # 핵심: 콤마가 포함된 필드가 하나의 값으로 파싱됨
    assert row1['CKG_MTRL_CN'] == '[재료] 대패 삼겹살150~200g, 숙주나물200g, 청경채25g'

    # 두 번째 행
    row2 = rows[1]
    assert row2['RCP_SNO'] == '7022417'
    assert row2['RCP_TTL'] == '제육볶음'
    assert row2['CKG_MTRL_CN'] == '[재료] 돼지고기 앞다리살636g [양념장 ] 고춧가루6T, 간장4T'


def test_csv_parsing_integration():
    """전체 CSV 파싱 통합 테스트"""

    # 실제 CSV 샘플
    csv_data = '''RCP_SNO,RCP_TTL,CKG_NM,CKG_MTRL_CN
7034388,소갈비찜,소갈비찜,"[재료] 소갈비 찜용1kg, 무우1토막(250g), 양파1/2개, 대파1대, 풋고추1개 [양념재료] 식용유1바퀴, 다진마늘2T"
7022417,제육볶음,제육볶음,"[재료] 돼지고기 앞다리살636g [양념장 ] 고춧가루6T, 간장4T, 올리고당3.5T"'''

    csv_file = io.StringIO(csv_data)
    reader = csv.DictReader(csv_file)
    rows = list(reader)

    assert len(rows) == 2

    # 소갈비찜 레시피
    recipe1 = rows[0]
    assert recipe1['RCP_SNO'] == '7034388'
    assert recipe1['RCP_TTL'] == '소갈비찜'
    assert recipe1['CKG_NM'] == '소갈비찜'

    # CKG_MTRL_CN 필드가 올바르게 파싱됨
    ingredients_text = recipe1['CKG_MTRL_CN']
    assert '[재료]' in ingredients_text
    assert '소갈비 찜용1kg' in ingredients_text
    assert '[양념재료]' in ingredients_text
    assert '다진마늘2T' in ingredients_text

    # 제육볶음 레시피
    recipe2 = rows[1]
    assert recipe2['RCP_SNO'] == '7022417'
    assert recipe2['CKG_MTRL_CN'].startswith('[재료] 돼지고기')


def test_csv_dict_reader_case_insensitive():
    """대소문자 무시 테스트"""

    csv_data = '''rcp_sno,Rcp_Ttl,CKG_MTRL_CN
123,테스트레시피,"재료1, 재료2"'''

    csv_file = io.StringIO(csv_data)
    reader = csv.DictReader(csv_file)
    rows = list(reader)

    row = rows[0]

    # 헤더를 소문자로 정규화
    normalized_row = {key.strip().lower(): value.strip() for key, value in row.items()}

    assert normalized_row['rcp_sno'] == '123'
    assert normalized_row['rcp_ttl'] == '테스트레시피'
    assert normalized_row['ckg_mtrl_cn'] == '재료1, 재료2'

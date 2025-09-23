# 만개의레시피 API 분석 결과

만개의레시피 웹사이트의 API 구조 분석 결과를 정리한 문서입니다.

## 🔍 API 탐색 결과

### ❌ JSON API 없음
만개의레시피는 **공개 JSON API를 제공하지 않습니다**.

### 테스트 결과 요약
총 15개의 다양한 API 엔드포인트를 테스트한 결과:
- **성공한 API**: 1개 (댓글 API)
- **실패한 API**: 14개 (모두 빈 응답)

## 📊 API 테스트 상세 결과

### ✅ 작동하는 API (1개)

#### 댓글 API
```
URL: https://www.10000recipe.com/recipe/ajax.html?q_mode=getListComment&seq=7062829&page=1
응답: HTML 형태 (574 characters)
내용: 댓글 목록을 HTML 조각으로 반환
```

**응답 예시**:
```html
<div class="media reply_list">
  <div class="media-left">
    <a href="/profile/recipe_comment.html?uid=58687018">
      <img class="media-object" src="https://recipe1.ezmember.co.kr/img/df/pf_100_100.png">
    </a>
  </div>
  <div class="media-body">
    <h4 class="media-heading">
      <b class="info_name_f">이형규</b>2025-09-18 09:33
      <span>|</span><a href="javascript:void(0);">답글</a>
      <span>|</span><a href="javascript:problem_open('rc','39720906');">신고</a>
    </h4>
    아주좋아요^^
  </div>
</div>
```

### ❌ 작동하지 않는 API (14개)

모든 API 엔드포인트에서 **Status 200**이지만 **응답 길이 0** (빈 응답):

1. `q_mode=list` - 레시피 목록
2. `q_mode=getList` - 레시피 목록 가져오기  
3. `q_mode=recipe_list` - 레시피 리스트
4. `q_mode=search` - 레시피 검색
5. `q_mode=read&seq=7062829` - 레시피 상세 (기본)
6. `q_mode=view&seq=7062829` - 레시피 뷰
7. `q_mode=detail&seq=7062829` - 레시피 디테일
8. `q_mode=recipe&seq=7062829` - 레시피 데이터
9. `q_mode=category` - 카테고리 목록
10. `q_mode=getCate` - 카테고리 가져오기
11. `q_mode=list&page=1` - 페이지별 목록
12. `q_mode=getList&page=1&limit=20` - 제한된 목록
13. `q_mode=popular` - 인기 레시피
14. `q_mode=recent` - 최근 레시피
15. `q_mode=ranking` - 랭킹

## 🌐 HTML 페이지 접근

### ✅ 레시피 상세 페이지 성공
```
URL: https://www.10000recipe.com/recipe/7062829
Status: 200
Content-Type: text/html; charset=UTF-8
Response Length: 204,501 characters
```

**결론**: 레시피 데이터는 HTML 페이지에 포함되어 있어 **스크래핑으로 추출 가능**

## 🎯 권장 데이터 수집 방법

### 1. HTML 스크래핑 방식
```python
# 레시피 목록 페이지 스크래핑
list_url = "https://www.10000recipe.com/recipe/list.html"

# 각 레시피 상세 페이지 스크래핑
recipe_url = "https://www.10000recipe.com/recipe/{recipe_id}"
```

### 2. 필요한 도구
- **BeautifulSoup4**: HTML 파싱
- **Requests**: HTTP 요청
- **Selenium**: JavaScript 렌더링 (필요시)

### 3. 수집 가능한 데이터
- ✅ 레시피 제목, 설명
- ✅ 재료 목록 (정규화 대상)
- ✅ 조리 단계
- ✅ 이미지 URL
- ✅ 카테고리 정보
- ✅ 댓글 (별도 API 호출)

## 🚨 주의사항

### 1. 서버 부하 고려
- 요청 간 지연시간 설정 (1초 이상)
- 동시 요청 수 제한 (5개 이하)
- User-Agent 로테이션

### 2. 데이터 품질
- HTML 구조 변경 가능성
- 누락된 데이터 처리
- 이미지 링크 유효성 검증

### 3. 법적 고려사항
- robots.txt 준수
- 이용약관 확인
- 데이터 사용 목적 명시

## 🔄 스크래핑 플로우

```
1. 레시피 목록 페이지 접근
   └─ 레시피 ID 목록 추출

2. 각 레시피 상세 페이지 스크래핑
   ├─ 기본 정보 추출
   ├─ 재료 목록 추출 → 정규화
   ├─ 조리 단계 추출
   └─ 이미지 URL 추출

3. 댓글 API 호출 (선택사항)
   └─ 댓글 데이터 추가 수집

4. 데이터베이스 저장
   └─ 정규화된 형태로 저장
```

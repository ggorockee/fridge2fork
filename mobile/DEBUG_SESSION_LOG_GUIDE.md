# 🔬 세션 ID 디버그 로그 분석 가이드

## 📋 목적

재료 추가 전/후 세션 ID를 추적하여 서버가 다른 냉장고를 반환하는지 확인

## 🔍 디버그 로그 읽는 방법

### 정상적인 흐름 (재료가 표시되어야 함)

```
1. 앱 시작 시:
🔍 [DEBUG] Session BEFORE getFridge: null
🌐 GET /fridge
🔍 [DEBUG] Request Header X-Session-ID: null (서버가 생성 예정)
📥 Response 200: {"id": 1, "ingredients": [], ...}
🔍 [DEBUG] Response Header X-Session-ID: abc123...
🔐 New session ID received from server, saving to SharedPreferences
🔍 [DEBUG] ✅ First session ID saved: abc123...
🔍 [DEBUG] Session AFTER getFridge: abc123...
🔍 [DEBUG] Fridge ID from GET: 1
🔍 [DEBUG] Total ingredients: 0

2. 재료 추가 시:
🥬 [FridgeProvider] Adding ingredient: 양파
🔍 [DEBUG] Session BEFORE add: abc123...
🌐 POST /fridge/ingredients
🔍 [DEBUG] Request Header X-Session-ID: abc123...
📤 Request Body: {"ingredient_name":"양파"}
📥 Response 200: {"id": 1, "ingredients": [{"name": "양파", ...}], ...}
🔍 [DEBUG] Response Header X-Session-ID: null (기존 세션 유지)
🔍 [DEBUG] Session AFTER add: abc123...
🔍 [DEBUG] Fridge ID in response: 1
🔍 [DEBUG] Ingredients in response: 양파
🥬 [FridgeProvider] Fridge after add: 1 ingredients
✅ [FridgeProvider] State updated with 1 ingredients

✅ 성공 기준:
- Session BEFORE add == Session AFTER add (abc123...)
- Fridge ID 동일 (1)
- State updated with ingredients
```

### 비정상적인 흐름 (문제 발생 - 세션 ID가 변경됨)

```
1. 앱 시작 시:
🔍 [DEBUG] Session BEFORE getFridge: null
🌐 GET /fridge
🔍 [DEBUG] Response Header X-Session-ID: abc123...
🔍 [DEBUG] ✅ First session ID saved: abc123...
🔍 [DEBUG] Session AFTER getFridge: abc123...
🔍 [DEBUG] Fridge ID from GET: 1
🔍 [DEBUG] Total ingredients: 0

2. 재료 추가 시:
🥬 [FridgeProvider] Adding ingredient: 양파
🔍 [DEBUG] Session BEFORE add: abc123...
🌐 POST /fridge/ingredients
🔍 [DEBUG] Request Header X-Session-ID: abc123...
📥 Response 200: {"id": 2, "ingredients": [{"name": "양파", ...}], ...}
🔍 [DEBUG] Response Header X-Session-ID: xyz789...  ⚠️ 세션 ID 변경!
🔐 New session ID received from server, saving to SharedPreferences
🔍 [DEBUG] ⚠️ Session ID CHANGED!
🔍 [DEBUG] Old: abc123...
🔍 [DEBUG] New: xyz789...
🔍 [DEBUG] Session AFTER add: xyz789...
🔍 [DEBUG] Fridge ID in response: 2  ⚠️ 다른 냉장고 ID!
🔍 [DEBUG] Ingredients in response: 양파
✅ [FridgeProvider] State updated with 1 ingredients

3. 다시 냉장고 조회 시 (홈 화면 새로고침 또는 탭 전환):
🔍 [DEBUG] Session BEFORE getFridge: xyz789...
🌐 GET /fridge
🔍 [DEBUG] Request Header X-Session-ID: xyz789...
📥 Response 200: {"id": 2, "ingredients": [{"name": "양파", ...}], ...}
🔍 [DEBUG] Fridge ID from GET: 2
🔍 [DEBUG] Total ingredients: 1

❌ 문제:
- Session ID가 abc123 → xyz789로 변경됨
- Fridge ID가 1 → 2로 변경됨
- 초기 냉장고(ID:1)는 여전히 비어있고, 새 냉장고(ID:2)에만 재료가 있음
- 서버가 POST 요청 시 새 세션을 생성하고 있음
```

## 🐛 문제 유형별 진단

### A. 세션 ID가 계속 null로 유지

```
🔍 [DEBUG] Session BEFORE getFridge: null
🔍 [DEBUG] Response Header X-Session-ID: abc123...
🔍 [DEBUG] Session AFTER getFridge: null  ❌ 저장 실패!
```

**원인**: SharedPreferences 저장 실패 또는 SessionService 초기화 오류

**해결**:
1. 앱 완전 삭제 후 재설치
2. SessionService.initialize() 호출 확인
3. SharedPreferences 권한 확인

---

### B. 세션 ID가 매 요청마다 변경

```
🔍 [DEBUG] Response Header X-Session-ID: abc123...
... 다음 요청 ...
🔍 [DEBUG] Response Header X-Session-ID: xyz789...  ❌ 매번 변경!
```

**원인**: 서버가 매번 새 세션을 생성하고 있음

**서버 로그 확인** (터미널):
```bash
cd server
tail -f server.log | grep "session"
```

예상 출력:
```
INFO: Adding ingredient '양파' to fridge 1 (session: abc123...)
```

만약 다른 세션 ID가 보인다면 서버 코드 문제

---

### C. POST는 성공하지만 GET에서 빈 냉장고

```
POST 후:
🔍 [DEBUG] Fridge ID in response: 1
🔍 [DEBUG] Ingredients in response: 양파

GET 요청:
🔍 [DEBUG] Fridge ID from GET: 1
🔍 [DEBUG] Total ingredients: 0  ❌ 사라짐!
```

**원인**: POST와 GET이 다른 냉장고를 조회하고 있거나, DB 저장 실패

**서버 직접 테스트**:
```bash
# 세션 ID를 로그에서 복사 (예: abc123...)
curl -H "X-Session-ID: abc123..." http://127.0.0.1:8000/fridge2fork/v1/recipes/fridge
```

만약 재료가 있다면: Flutter 문제
만약 재료가 없다면: 서버 DB 저장 문제

---

### D. 요청 헤더에 세션 ID가 안 들어감

```
🔍 [DEBUG] Session BEFORE add: abc123...
🔍 [DEBUG] Request Header X-Session-ID: null (서버가 생성 예정)  ❌ 헤더 누락!
```

**원인**: SessionService.getSessionId()가 null 반환

**해결**: SharedPreferences에서 세션 ID 읽기 실패 → 앱 재설치

## 📊 디버그 로그 수집 방법

### 1단계: 앱 완전 재시작

```bash
# 시뮬레이터에서 앱 삭제
flutter clean
flutter pub get
flutter run
```

### 2단계: 로그 수집 시작

앱이 실행되면 터미널의 **모든 로그를 복사**하세요.

### 3단계: 재료 추가 테스트

1. [+] 버튼 클릭
2. "양파" 입력하여 추가
3. 스낵바 확인
4. 홈 화면 확인
5. "나의 냉장고" 탭 확인

### 4단계: 로그 필터링

복사한 로그에서 다음 부분만 추출:

```bash
# 🔍로 시작하는 모든 DEBUG 라인
# 🥬로 시작하는 모든 FridgeProvider 라인
# 🌐로 시작하는 모든 API 요청 라인
# 📥로 시작하는 모든 API 응답 라인
```

## 📝 로그 분석 체크리스트

디버그 로그를 받았을 때 다음을 확인하세요:

- [ ] **초기 GET 요청**: 세션 ID가 생성되고 저장되었는가?
- [ ] **POST 요청 전**: Session BEFORE add가 존재하는가?
- [ ] **POST 요청 헤더**: X-Session-ID가 포함되었는가?
- [ ] **POST 응답**: 응답에 재료가 포함되어 있는가?
- [ ] **POST 응답 헤더**: 새 세션 ID가 반환되었는가? (null이어야 정상)
- [ ] **POST 응답 후**: Session AFTER add가 BEFORE와 동일한가?
- [ ] **Fridge ID**: POST 응답의 Fridge ID가 초기 GET과 동일한가?
- [ ] **State 업데이트**: "State updated with X ingredients" 메시지가 있는가?

## 🎯 예상 결과

### ✅ 정상 시나리오

```
앱 시작:
- Session: null → abc123
- Fridge ID: 1
- Ingredients: 0

재료 추가:
- Session: abc123 → abc123 (변화 없음)
- Fridge ID: 1 (동일)
- Ingredients: 0 → 1

결과: 홈/냉장고 화면에 재료 표시됨
```

### ❌ 문제 시나리오

```
앱 시작:
- Session: null → abc123
- Fridge ID: 1
- Ingredients: 0

재료 추가:
- Session: abc123 → xyz789 (변경됨!)
- Fridge ID: 1 → 2 (변경됨!)
- Ingredients: 0 → 1

결과: 빈 냉장고 표시 (초기 냉장고 ID:1은 여전히 비어있음)
```

## 🚨 긴급 대응

로그를 분석한 결과 세션 ID가 변경되고 있다면:

1. **서버 코드 재확인**: `server/app/recipes/api.py`의 `add_ingredient_to_fridge` 함수
2. **서버 재시작**: 최신 코드로 재시작되었는지 확인
3. **서버 직접 테스트**: curl로 POST → GET 순서 테스트
4. **앱 완전 재설치**: SharedPreferences 초기화

---

**다음 단계**: 위의 방법으로 로그를 수집하고 분석하세요. 문제가 발견되면 해당 섹션의 해결 방법을 따르세요.

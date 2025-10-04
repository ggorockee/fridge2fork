# 냉장고 상태 연동 테스트 가이드

## 📋 테스트 목적

홈 화면과 나의 냉장고 화면이 같은 세션으로 연동되는지 확인

## 🔍 사전 확인사항

### 1. 서버 실행 상태
```bash
cd server
python main.py

# 확인: http://localhost:8000/fridge2fork/v1/system/health
```

### 2. 앱 완전 재빌드
```bash
flutter clean
flutter pub get
flutter run
```

### 3. 디버그 로그 활성화

`lib/config/app_config.dart`에서:
```dart
static const bool enableNetworkLogging = true;  // 디버그 로그 활성화
```

## 🧪 테스트 시나리오

### 시나리오 1: 홈 화면에서 재료 추가

1. **앱 첫 실행**
   - 예상: 빈 냉장고 화면 표시
   - 로그: `🔐 No session found, server will create one`

2. **[+] 버튼 클릭 → "양파" 추가**
   - 예상: 스낵바 "1개의 식재료가 추가되었습니다!"
   - 로그 확인:
     ```
     🥬 [FridgeProvider] Adding ingredient: 양파
     🔐 New session ID received from server: xxxxxxxx-...
     🥬 [FridgeProvider] Response: success=true, hasData=true
     🥬 [FridgeProvider] Fridge after add: 1 ingredients
     ✅ [FridgeProvider] State updated with 1 ingredients
     ```

3. **홈 화면 상태 확인**
   - 예상: "현재 냉장고 재료 (1)" 표시
   - 예상: "양파" 재료 카드 표시

4. **하단 네비게이션 → "나의 냉장고" 탭**
   - ✅ 예상: **"양파"가 표시되어야 함**
   - ❌ 만약 비어있다면: **세션 연동 실패**

### 시나리오 2: 나의 냉장고에서 재료 추가

1. **"나의 냉장고" 탭에서 [+] 버튼 → "대파" 추가**
   - 로그 확인:
     ```
     🥬 [FridgeProvider] Adding ingredient: 대파
     🥬 [FridgeProvider] Fridge after add: 2 ingredients
     ```

2. **하단 네비게이션 → "홈" 탭**
   - ✅ 예상: **"양파", "대파" 둘 다 표시되어야 함**
   - ❌ 만약 "대파"만 있거나 비어있다면: **상태 동기화 실패**

### 시나리오 3: 앱 재시작 후 세션 유지

1. **앱 완전 종료 (백그라운드에서도 제거)**

2. **앱 재실행**
   - 로그 확인:
     ```
     🔐 Using existing session: xxxxxxxx-...
     🥬 냉장고 조회 성공: 2개 재료
     ```

3. **홈 화면 확인**
   - ✅ 예상: **"양파", "대파" 그대로 표시**
   - ❌ 만약 비어있다면: **세션 영속성 실패**

## 🐛 문제 발생 시 디버깅

### A. 재료 추가 후 홈/냉장고에 표시 안됨

**원인**: 서버 API 문제 또는 응답 파싱 실패

**확인 방법**:
```bash
# 터미널에서 서버 API 직접 테스트
curl -X POST http://localhost:8000/fridge2fork/v1/recipes/fridge/ingredients \
  -H "Content-Type: application/json" \
  -d '{"ingredient_name": "양파"}'
```

**예상 응답**:
```json
{
  "id": 1,
  "ingredients": [
    {"id": 1, "name": "양파", "category": "채소류", "added_at": "..."}
  ],
  "updated_at": "..."
}
```

**해결**: 위 응답이 나오지 않으면 서버 재시작

---

### B. 홈과 냉장고 화면 간 동기화 안됨

**원인**: 다른 세션 ID 사용

**확인 방법**:

앱 로그에서 세션 ID 추출:
```
🔐 Using existing session: abc123...
```

서버 로그에서 냉장고 ID와 세션 확인:
```
INFO: Adding ingredient '양파' to fridge 5 (session: abc123...)
```

**해결**:
- 앱 삭제 후 재설치 (SharedPreferences 초기화)
- 또는 아래 코드 임시 추가:

```dart
// lib/main.dart의 main() 함수에 추가 (디버그용)
if (kDebugMode) {
  final prefs = await SharedPreferences.getInstance();
  await prefs.clear();  // ⚠️ 임시: 세션 강제 초기화
}
```

---

### C. 앱 재시작 후 세션 유실

**원인**: SharedPreferences 저장 실패

**확인 방법**:

```dart
// SessionService 테스트 코드 추가
final sessionInfo = await SessionService.instance.getSessionInfo();
debugPrint('📊 Session Info: $sessionInfo');
```

**예상 출력**:
```
📊 Session Info: {
  session_id: abc123...,
  created_at: 2025-10-04T...,
  expires_at: 2025-10-05T...,
  is_expired: false,
  remaining_hours: 23
}
```

**해결**: null이면 SharedPreferences 권한 문제 → 앱 재설치

## ✅ 성공 기준

- [x] 홈 화면에서 재료 추가 → 나의 냉장고에 표시
- [x] 나의 냉장고에서 재료 추가 → 홈 화면에 표시
- [x] 앱 재시작 후에도 재료 유지
- [x] 디버그 로그에 같은 세션 ID 사용

## 📝 결과 보고

테스트 후 결과를 체크하세요:

**✅ 성공 케이스**:
- 홈 ↔ 냉장고 실시간 동기화
- 앱 재시작 후 세션 유지
- 로그에 명확한 세션 ID 추적

**❌ 실패 케이스**:
- 재료 추가 후 표시 안됨 → 서버 API 문제
- 화면 간 동기화 안됨 → 세션 ID 불일치
- 앱 재시작 후 초기화 → SharedPreferences 실패

## 🔧 긴급 수정 필요 시

위 테스트 결과를 캡처 또는 복사해서 공유해주시면 추가 수정 진행하겠습니다.

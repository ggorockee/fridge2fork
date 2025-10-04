# 의견보내기(Feedback) 기능 개발 체크리스트

## 개요
사용자가 앱에 대한 의견, 버그 리포트, 기능 제안을 보낼 수 있는 피드백 시스템 구현

## 서버 개발 체크리스트

### 1. 모델 설계
- [ ] Feedback 모델 생성 (system/models.py)
  - [ ] 필드: user (nullable), session_key (nullable), feedback_type, title, content, contact_email (optional), created_at
  - [ ] feedback_type: BUG, FEATURE, IMPROVEMENT, OTHER
  - [ ] 인덱스: created_at, feedback_type

### 2. Schema 정의
- [ ] FeedbackSchema (system/schemas.py)
  - [ ] FeedbackCreateSchema: 피드백 생성 요청
  - [ ] FeedbackResponseSchema: 피드백 응답

### 3. API 엔드포인트
- [ ] POST /fridge2fork/v1/system/feedback
  - [ ] 회원/비회원 모두 가능
  - [ ] 세션 ID로 비회원 구분
  - [ ] 이메일 선택적 제공

### 4. 테스트
- [ ] 회원 피드백 생성 테스트
- [ ] 비회원 피드백 생성 테스트
- [ ] 필수 필드 검증 테스트
- [ ] 이메일 형식 검증 테스트

### 5. 문서화
- [ ] API 문서 작성 (claudedocs/feedback_api.md)
- [ ] 예제 요청/응답 추가

### 6. 마이그레이션
- [ ] makemigrations 실행
- [ ] migrate 실행
- [ ] 서버 재시작

## 모바일 개발 체크리스트

### 1. 모델 및 서비스
- [ ] Feedback 모델 생성 (models/feedback.dart)
- [ ] FeedbackApiService 생성 (services/api/feedback_api_service.dart)

### 2. UI 구현
- [ ] FeedbackScreen 생성 (screens/feedback_screen.dart)
  - [ ] 피드백 타입 선택 (버그, 기능 제안, 개선, 기타)
  - [ ] 제목 입력
  - [ ] 내용 입력 (멀티라인)
  - [ ] 이메일 입력 (선택)
  - [ ] 전송 버튼

### 3. 상태 관리
- [ ] FeedbackProvider 생성 (providers/feedback_provider.dart)
- [ ] 전송 중/성공/실패 상태 관리

### 4. 네비게이션
- [ ] 홈 화면 또는 설정에서 의견보내기 접근

### 5. 검증
- [ ] 제목 필수 입력 검증
- [ ] 내용 필수 입력 검증
- [ ] 이메일 형식 검증 (입력 시)
- [ ] 전송 완료 후 성공 메시지

## 완료 기준
- [ ] 서버 API 테스트 통과
- [ ] 모바일에서 피드백 전송 성공
- [ ] DB에 피드백 저장 확인
- [ ] Git commit 및 push 완료

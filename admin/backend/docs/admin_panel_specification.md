# 🖥️ 관리 패널 상세 개발 명세서

## 📋 개요

Fridge2Fork Admin Backend의 웹 기반 관리 패널을 개발하여 개발자가 직관적으로 데이터베이스를 관리하고 작업 진행상황을 체크박스로 추적할 수 있는 인터페이스를 제공합니다.

## 🎯 핵심 목표

**✅ 체크박스 기반 작업 추적**: 개발자가 완료된 작업을 체크박스로 확인할 수 있는 시스템
**📊 데이터베이스 관리**: 테이블별 레코드 관리 및 정규화 작업 인터페이스
**🔍 실시간 모니터링**: 시스템 상태 및 데이터베이스 현황 대시보드

---

## 🏗️ 아키텍처 설계

### 디렉토리 구조
```
apps/
├── static/                    # 정적 파일
│   ├── css/
│   │   ├── admin.css         # 관리 패널 스타일
│   │   └── checklist.css     # 체크리스트 전용 스타일
│   ├── js/
│   │   ├── admin.js          # 메인 JavaScript
│   │   ├── checklist.js      # 체크리스트 기능
│   │   └── dashboard.js      # 대시보드 기능
│   └── images/               # 이미지 파일
├── templates/                # HTML 템플릿
│   ├── base.html            # 기본 레이아웃
│   ├── dashboard.html       # 대시보드
│   ├── checklist.html       # 체크리스트 페이지
│   ├── tables.html          # 테이블 관리
│   └── normalization.html   # 정규화 관리
└── routers/
    └── admin.py             # 관리 패널 라우터
```

### 기술 스택
- **백엔드**: FastAPI + Jinja2 Templates
- **프론트엔드**: HTML5 + CSS3 + Vanilla JavaScript
- **스타일링**: Bootstrap 5 (CDN)
- **상태 관리**: localStorage (체크리스트 상태)
- **아이콘**: Font Awesome (CDN)

---

## 📄 페이지별 상세 명세

### 1. 🏠 메인 대시보드 (`/fridge2fork/admin`)

#### 기능 요구사항
- [ ] 시스템 전체 상태 한눈에 보기
- [ ] 각 테이블별 레코드 수 실시간 표시
- [ ] 데이터베이스 연결 상태 모니터링
- [ ] 최근 활동 로그 표시
- [ ] 체크리스트 진행률 표시

#### UI 레이아웃
```html
┌─────────────────────────────────────────┐
│           🚀 Fridge2Fork Admin          │
├─────────────────────────────────────────┤
│ 📊 시스템 현황              🔗 DB 상태 │
│ ┌───────────┐ ┌───────────┐             │
│ │recipes    │ │ingredients│             │
│ │1,250 건   │ │890 건     │             │
│ └───────────┘ └───────────┘             │
│                                         │
│ ✅ 작업 진행률: 75%                    │
│ 📝 최근 활동                           │
│ • 정규화 작업 5건 완료                 │
│ • 레시피 10건 추가                     │
└─────────────────────────────────────────┘
```

#### 데이터 소스
- `GET /fridge2fork/v1/system/info` - 시스템 정보
- `GET /fridge2fork/v1/system/database/tables` - 테이블 정보
- `GET /fridge2fork/v1/system/activities` - 최근 활동

### 2. ✅ 체크리스트 페이지 (`/fridge2fork/admin/checklist`)

#### 핵심 기능 ⭐
- [ ] Phase별 작업 목록 표시
- [ ] 체크박스 상태 실시간 저장
- [ ] 진행률 시각적 표시
- [ ] 완료된 작업 자동 정렬
- [ ] 작업 완료 시간 기록

#### UI 레이아웃
```html
┌─────────────────────────────────────────┐
│        ✅ 개발 체크리스트              │
├─────────────────────────────────────────┤
│ 📊 전체 진행률: ████████░░ 80%         │
│                                         │
│ 🔴 Phase 1: 관리 패널 개발             │
│ ☑️ 기본 구조 생성                      │
│ ☑️ 대시보드 구현                       │
│ ☐ 체크리스트 기능 구현                 │
│ ☐ 테이블 관리 UI                       │
│                                         │
│ 🟡 Phase 2: 배포 설정                 │
│ ☐ Docker 설정 점검                     │
│ ☐ K8s 배포 설정                        │
│                                         │
│ [새 작업 추가] [진행률 리셋]           │
└─────────────────────────────────────────┘
```

#### 데이터 저장 구조 (localStorage)
```javascript
const checklistData = {
  "phase1_basic_structure": {
    "completed": true,
    "completedAt": "2025-09-29T10:30:00Z",
    "notes": "정적 파일 디렉토리 생성 완료"
  },
  "phase1_dashboard": {
    "completed": true,
    "completedAt": "2025-09-29T11:00:00Z",
    "notes": ""
  },
  "phase1_checklist": {
    "completed": false,
    "completedAt": null,
    "notes": "현재 작업 중"
  }
  // ...
}
```

### 3. 📊 테이블 관리 페이지 (`/fridge2fork/admin/tables`)

#### 기능 요구사항
- [ ] 전체 테이블 목록 및 상태 표시
- [ ] 테이블별 상세 정보 (레코드 수, 크기, 인덱스)
- [ ] 레코드 추가/삭제 인터페이스
- [ ] 검색 및 필터링 기능
- [ ] 페이지네이션

#### UI 레이아웃
```html
┌─────────────────────────────────────────┐
│           📊 테이블 관리               │
├─────────────────────────────────────────┤
│ 🔍 [검색창    ] [필터▼] [새로고침]     │
│                                         │
│ ┌───────────────────────────────────────┤
│ │테이블명     │레코드수│크기  │상태   │
│ ├───────────────────────────────────────┤
│ │recipes      │1,250   │45MB  │정상   │
│ │ingredients  │890     │23MB  │정상   │
│ │recipe_ingr..│3,420   │12MB  │정상   │
│ └───────────────────────────────────────┘
│                                         │
│ [레코드 추가] [일괄 삭제] [내보내기]   │
└─────────────────────────────────────────┘
```

### 4. 🔧 정규화 관리 페이지 (`/fridge2fork/admin/normalization`)

#### 기능 요구사항
- [ ] 정규화 대기 목록 표시
- [ ] AI 제안 승인/거부 인터페이스
- [ ] 일괄 정규화 처리
- [ ] 중복 병합 작업
- [ ] 정규화 히스토리

#### UI 레이아웃
```html
┌─────────────────────────────────────────┐
│          🔧 정규화 관리                │
├─────────────────────────────────────────┤
│ 📊 대기: 150건 │ 완료: 1,200건        │
│                                         │
│ 🤖 AI 제안 목록                        │
│ ┌───────────────────────────────────────┤
│ │원본명        │제안명     │신뢰도│액션 │
│ ├───────────────────────────────────────┤
│ │오징어 두마리 │오징어     │85%  │✓ ✗ │
│ │닭 1.2kg     │닭고기     │92%  │✓ ✗ │
│ └───────────────────────────────────────┘
│                                         │
│ [일괄 승인] [일괄 거부] [수동 추가]    │
└─────────────────────────────────────────┘
```

---

## 🧩 핵심 컴포넌트 상세 설계

### 체크리스트 컴포넌트

#### JavaScript 클래스 설계
```javascript
class ChecklistManager {
  constructor() {
    this.storageKey = 'fridge2fork_checklist';
    this.data = this.loadFromStorage();
    this.phases = this.loadPhaseDefinitions();
  }

  // 체크박스 상태 토글
  toggleTask(taskId) {
    const task = this.data[taskId];
    task.completed = !task.completed;
    task.completedAt = task.completed ? new Date().toISOString() : null;
    this.saveToStorage();
    this.updateUI();
  }

  // 진행률 계산
  calculateProgress() {
    const total = Object.keys(this.data).length;
    const completed = Object.values(this.data)
      .filter(task => task.completed).length;
    return Math.round((completed / total) * 100);
  }

  // 로컬 스토리지 저장
  saveToStorage() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.data));
  }

  // UI 업데이트
  updateUI() {
    this.updateProgressBar();
    this.updateTaskList();
    this.updateDashboardProgress();
  }
}
```

#### CSS 스타일 (체크리스트 전용)
```css
.checklist-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.progress-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 30px;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: rgba(255,255,255,0.3);
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #4caf50;
  transition: width 0.3s ease;
}

.phase-section {
  background: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.task-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.task-checkbox {
  width: 20px;
  height: 20px;
  margin-right: 15px;
  cursor: pointer;
}

.task-completed {
  text-decoration: line-through;
  color: #888;
}

.task-timestamp {
  font-size: 0.8em;
  color: #666;
  margin-left: auto;
}
```

### 대시보드 위젯 시스템

#### 위젯 기본 구조
```javascript
class DashboardWidget {
  constructor(containerId, title, apiEndpoint) {
    this.container = document.getElementById(containerId);
    this.title = title;
    this.apiEndpoint = apiEndpoint;
    this.refreshInterval = 30000; // 30초
  }

  async fetchData() {
    try {
      const response = await fetch(this.apiEndpoint);
      return await response.json();
    } catch (error) {
      console.error(`위젯 데이터 로드 실패: ${this.title}`, error);
      return null;
    }
  }

  render(data) {
    // 각 위젯별로 오버라이드
  }

  startAutoRefresh() {
    setInterval(() => {
      this.fetchData().then(data => this.render(data));
    }, this.refreshInterval);
  }
}

// 테이블 정보 위젯
class TableInfoWidget extends DashboardWidget {
  constructor() {
    super('table-info-widget', '테이블 정보', '/fridge2fork/v1/system/database/tables');
  }

  render(data) {
    if (!data || !data.tables) return;

    const html = data.tables.map(table => `
      <div class="table-card">
        <h6>${table.name}</h6>
        <p>${table.row_count.toLocaleString()}건</p>
        <small>${table.size}</small>
      </div>
    `).join('');

    this.container.innerHTML = html;
  }
}
```

---

## 🔗 API 연동 명세

### 관리 패널 전용 엔드포인트

#### 1. 대시보드 데이터 API
```python
@router.get("/admin/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """대시보드에 필요한 모든 데이터를 한번에 반환"""
    return {
        "system_info": await get_system_info(db=db),
        "table_stats": await get_database_tables(db=db),
        "recent_activities": await get_system_activities(limit=5),
        "normalization_stats": await get_normalization_statistics(db=db)
    }
```

#### 2. 체크리스트 상태 동기화 API (선택적)
```python
@router.post("/admin/checklist/sync")
async def sync_checklist(data: dict):
    """체크리스트 상태를 서버와 동기화 (선택적 기능)"""
    # 팀 작업시 체크리스트 상태 공유용
    pass

@router.get("/admin/checklist/status")
async def get_checklist_status():
    """전체 체크리스트 상태 조회"""
    pass
```

### 기존 API 활용
- `GET /fridge2fork/v1/system/*` - 시스템 정보
- `GET /fridge2fork/v1/ingredients/*` - 식재료 관리
- `GET /fridge2fork/v1/recipes/*` - 레시피 관리
- `GET /fridge2fork/v1/ingredients/normalization/*` - 정규화 관리

---

## 🎨 UI/UX 디자인 가이드라인

### 컬러 스킴
- **Primary**: #667eea (보라-파랑 그라데이션)
- **Success**: #4caf50 (완료된 작업)
- **Warning**: #ff9800 (주의사항)
- **Danger**: #f44336 (오류/위험)
- **Info**: #2196f3 (정보)

### 타이포그래피
- **제목**: 'Noto Sans KR', sans-serif
- **본문**: 'Roboto', 'Noto Sans KR', sans-serif
- **코드**: 'Fira Code', monospace

### 아이콘 시스템
- Font Awesome 6 (무료 버전)
- 이모지 활용 (기존 로깅 시스템과 일관성)

### 반응형 디자인
- **Desktop**: 1200px 이상
- **Tablet**: 768px - 1199px
- **Mobile**: 767px 이하

---

## 🔐 보안 고려사항

### 접근 제어
- [ ] 기본 HTTP 인증 또는 세션 기반 인증 (추후 추가)
- [ ] CORS 설정 확인
- [ ] XSS 방지 (HTML 이스케이핑)
- [ ] CSRF 방지 (토큰 기반)

### 데이터 보호
- [ ] 민감한 정보 마스킹
- [ ] 로그에 개인정보 기록 금지
- [ ] 입력 데이터 검증

---

## 📈 성능 최적화

### 프론트엔드 최적화
- [ ] CSS/JS 파일 최소화
- [ ] 이미지 최적화
- [ ] 브라우저 캐싱 활용
- [ ] 지연 로딩 구현

### 백엔드 최적화
- [ ] 정적 파일 캐싱
- [ ] API 응답 캐싱
- [ ] 데이터베이스 쿼리 최적화

---

## 🧪 테스트 계획

### 단위 테스트
- [ ] JavaScript 함수 테스트
- [ ] API 엔드포인트 테스트
- [ ] 데이터 저장/로드 테스트

### 통합 테스트
- [ ] 전체 워크플로우 테스트
- [ ] 브라우저 호환성 테스트
- [ ] 모바일 반응형 테스트

### 사용자 테스트
- [ ] 체크리스트 기능 사용성 테스트
- [ ] 관리 작업 워크플로우 테스트

---

## 📅 구현 우선순위

### 🔴 최우선 (Phase 1-A)
1. **기본 라우터 및 템플릿 설정**
2. **체크리스트 기능 구현** ⭐
3. **대시보드 기본 구조**

### 🟡 중요 (Phase 1-B)
4. **테이블 관리 인터페이스**
5. **정규화 관리 인터페이스**
6. **실시간 데이터 연동**

### 🟢 선택적 (Phase 1-C)
7. **고급 필터링 기능**
8. **데이터 내보내기**
9. **팀 협업 기능**

---

**📝 문서 버전**: 1.0
**📝 최종 수정**: 2025-09-29
**📝 다음 단계**: Phase 1-A 구현 시작
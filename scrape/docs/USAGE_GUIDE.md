# 사용 가이드

plan.md 구현을 위한 Python 파일들과 pandas 분석 도구 사용 방법입니다.

## 🗂️ 생성된 파일 구조

```
fridge2fork/scrape/
├── docs/                           # 📚 프로젝트 문서
│   ├── README.md                   # 프로젝트 개요
│   ├── API_ANALYSIS.md             # API 분석 결과
│   ├── DATABASE_SCHEMA.md          # 데이터베이스 스키마
│   ├── DEPLOYMENT_GUIDE.md         # Kubernetes 배포 가이드
│   └── USAGE_GUIDE.md              # 이 파일
├── scraper/                        # 🕷️ 스크래핑 코드
│   └── recipe_scraper.py           # 메인 스크래퍼
├── analysis/                       # 📊 데이터 분석 코드
│   └── data_explorer.py            # 자동화된 분석 도구
├── helm-charts/                    # ☸️ Kubernetes 배포용
│   ├── postgresql/                 # 데이터베이스 차트
│   ├── recipe-scraper/             # 스크래핑 크론잡 차트
│   └── recipe-api/                 # FastAPI 백엔드 차트
├── data_analysis_notebook.ipynb    # 📓 Jupyter 노트북
├── requirements.txt                # 📦 패키지 의존성
└── data/                          # 💾 수집된 데이터 (생성됨)
    ├── recipes.csv                # 레시피 메인 데이터
    ├── ingredients.csv            # 재료 데이터 (정규화됨)
    └── recipe_steps.csv           # 조리 단계 데이터
```

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# 또는 Anaconda 환경에서
conda install pandas numpy matplotlib seaborn beautifulsoup4 requests
```

### 2. 데이터 수집 (plan.md 구현)
```bash
# 레시피 스크래핑 실행
python scraper/recipe_scraper.py
```

**실행 결과**:
- `data/recipes.csv`: 레시피 기본 정보
- `data/ingredients.csv`: 재료 데이터 (정규화 포함)  
- `data/recipe_steps.csv`: 조리 단계 데이터

### 3. 데이터 분석
```bash
# 자동화된 전체 분석 실행
python analysis/data_explorer.py
```

**생성되는 파일**:
- `visualizations/*.png`: 차트들
- `reports/data_analysis_report.md`: 분석 리포트

### 4. Jupyter 노트북으로 대화형 분석
```bash
# Jupyter 노트북 실행
jupyter notebook data_analysis_notebook.ipynb
```

## 📊 데이터 분석 예시

### plan.md의 핵심: 재료 정규화

**목표**: `"고추장2스푼"` → `재료: "고추장"`, `수량: 2`, `단위: "스푼"`

```python
import pandas as pd

# 데이터 로드
ingredients_df = pd.read_csv('data/ingredients.csv')

# 정규화 결과 확인
normalized = ingredients_df[ingredients_df['is_normalized'] == 'true']
print(f"정규화 성공률: {len(normalized) / len(ingredients_df) * 100:.1f}%")

# 정규화 예시 출력
for _, row in normalized.head().iterrows():
    print(f"'{row['raw_text']}' → {row['ingredient']} {row['amount']} {row['unit']}")
```

### 기본 통계 분석

```python
# 레시피 데이터 로드
recipes_df = pd.read_csv('data/recipes.csv')

# 기본 통계
print(f"수집된 레시피: {len(recipes_df):,}개")
print(f"평균 조리시간: {recipes_df['cooking_time'].mean():.1f}분")
print(f"평균 재료 수: {recipes_df['ingredient_count'].mean():.1f}개")

# 인기 재료 Top 10
top_ingredients = ingredients_df['ingredient'].value_counts().head(10)
print("가장 많이 사용되는 재료:")
for ingredient, count in top_ingredients.items():
    print(f"  {ingredient}: {count}회")
```

### 시각화

```python
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']

# 조리시간 분포
plt.figure(figsize=(10, 6))
plt.hist(recipes_df['cooking_time'].dropna(), bins=30)
plt.title('레시피 조리시간 분포')
plt.xlabel('시간 (분)')
plt.ylabel('레시피 수')
plt.show()

# 인기 재료 차트
plt.figure(figsize=(12, 8))
top_ingredients.plot(kind='barh')
plt.title('가장 많이 사용되는 재료 Top 10')
plt.xlabel('사용 횟수')
plt.show()
```

## 🔧 주요 기능

### 1. recipe_scraper.py
- **목적**: plan.md 구현 - 레시피 이미지 클릭 시 데이터 수집
- **기능**:
  - 만개의레시피 HTML 스크래핑
  - 재료 텍스트 정규화 (`"고추장2스푼"` → `2`, `"스푼"`)
  - CSV 파일로 저장

**사용법**:
```python
from scraper.recipe_scraper import Recipe10000Scraper

scraper = Recipe10000Scraper()

# 레시피 ID 목록 수집
recipe_ids = scraper.get_recipe_list_ids(max_pages=5)

# 상세 데이터 스크래핑
recipes_df = scraper.scrape_multiple_recipes(recipe_ids[:50])

# 파일 저장
scraper.save_to_files()
```

### 2. data_explorer.py
- **목적**: 수집된 데이터의 자동화된 분석 및 시각화
- **기능**:
  - 기본 통계 분석
  - 정규화 성공률 분석
  - 시각화 차트 생성
  - 분석 리포트 생성

**사용법**:
```python
from analysis.data_explorer import RecipeDataExplorer

explorer = RecipeDataExplorer()
explorer.explore_all()  # 전체 분석 실행
```

### 3. data_analysis_notebook.ipynb
- **목적**: 대화형 데이터 분석 및 탐색
- **기능**:
  - pandas를 활용한 데이터 탐색
  - matplotlib/seaborn 시각화
  - 단계별 분석 과정

## 📈 분석 결과 해석

### 정규화 성공률
- **목표**: 80% 이상
- **측정**: `ingredients.csv`의 `is_normalized` 컬럼
- **예시**: `"고추장2스푼"` → `is_normalized: true`

### 주요 메트릭
1. **수집 효율성**: 성공적으로 스크래핑된 레시피 비율
2. **데이터 품질**: 필수 필드(제목, 재료) 완성도
3. **정규화 정확도**: 재료 텍스트 파싱 성공률

## ⚡ 성능 최적화

### 스크래핑 최적화
```python
# 배치 처리
scraper.scrape_multiple_recipes(recipe_ids, batch_size=50)

# 요청 간 지연
time.sleep(random.uniform(1, 3))

# 동시 요청 제한
concurrent_requests = 5
```

### 메모리 최적화
```python
# 청크 단위로 CSV 읽기
df = pd.read_csv('data/recipes.csv', chunksize=1000)

# 데이터 타입 최적화
df['recipe_id'] = df['recipe_id'].astype('category')
df['cooking_time'] = pd.to_numeric(df['cooking_time'], downcast='integer')
```

## 🐛 문제 해결

### 1. 스크래핑 오류
```bash
# 에러: HTTP 403 (차단)
→ User-Agent 변경, 요청 지연 시간 증가

# 에러: HTML 파싱 실패  
→ BeautifulSoup 선택자 업데이트

# 에러: 타임아웃
→ timeout 값 증가, 재시도 로직 추가
```

### 2. 정규화 실패
```python
# 실패 케이스 분석
failed = ingredients_df[ingredients_df['is_normalized'] == 'false']
print(failed['raw_text'].value_counts().head())

# 패턴 개선
import re
pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([가-힣a-zA-Z]+)')
```

### 3. 메모리 부족
```python
# 메모리 사용량 확인
df.memory_usage(deep=True).sum() / 1024**2  # MB 단위

# 데이터 타입 최적화
df = df.astype({
    'recipe_id': 'category',
    'cooking_time': 'int16',
    'serving_size': 'int8'
})
```

## 🔄 다음 단계

### 1. 대용량 데이터 처리 (목표: 20만개 레시피)
```bash
# 크론잡으로 정기 수집
python scraper/recipe_scraper.py --mode full --batch-size 1000

# Kubernetes 배포
helm install recipe-scraper ./helm-charts/recipe-scraper/
```

### 2. 데이터베이스 저장
```python
# PostgreSQL 연결
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/recipe_db')
df.to_sql('recipes', engine, if_exists='append', index=False)
```

### 3. API 서버 구축
```bash
# FastAPI 서버 실행  
helm install recipe-api ./helm-charts/recipe-api/
```

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우:

1. **로그 확인**: 각 스크립트는 상세한 로그를 출력합니다
2. **데이터 검증**: `data/` 폴더의 CSV 파일들을 직접 확인
3. **시각화 활용**: `visualizations/` 폴더의 차트들로 데이터 패턴 파악
4. **노트북 활용**: Jupyter 노트북으로 단계별 디버깅

# PostgreSQL 데이터 삽입 전략 계획

이 문서는 `crawler.py`를 통해 수집된 레시피 데이터를 PostgreSQL 데이터베이스에 안정적으로 삽입하기 위한 전략과 실행 계획을 정의합니다. 최우선 목표는 서버와 데이터베이스에 과도한 부하를 주지 않고, 데이터의 정합성을 보장하며, 중복 삽입을 방지하는 것입니다.

---

## 1. 핵심 원칙

1.  **안정성 최우선 (Stability First)**
    -   개별 레시피의 삽입 과정을 하나의 **트랜잭션(Transaction)** 단위로 묶어 처리합니다. 레시피 정보, 재료 정보, 또는 둘의 관계 정보 중 하나라도 삽입에 실패할 경우, 해당 레시피와 관련된 모든 변경사항을 롤백(Rollback)하여 데이터베이스의 일관성을 유지합니다.

2.  **점진적 데이터 처리 (Incremental Processing)**
    -   수천 개의 레시피를 한 번에 삽입하는 대신, 레시피를 하나씩 또는 작은 배치(batch) 단위로 처리합니다. 이는 DB 커넥션과 서버 리소스를 독점하지 않아 시스템 전체의 부하를 최소화합니다.

3.  **멱등성 확보 및 데이터 최신성 유지 (Idempotency & Data Freshness)**
    -   동일한 데이터가 반복적으로 유입되더라도 항상 예측 가능한 상태를 유지하도록 설계합니다. 이를 위해 PostgreSQL의 `ON CONFLICT` 절을 적극 활용하며, 두 가지 전략을 구분하여 사용합니다.
        -   **Upsert (Insert or Update)**: `ON CONFLICT ... DO UPDATE`를 사용하여, 데이터가 이미 존재할 경우 최신 정보로 **갱신**합니다. 크롤링을 통해 레시피 내용(설명, 이미지 등)이 변경되었을 수 있으므로, 이 방식을 기본 전략으로 채택하여 데이터의 최신성을 보장합니다.
        -   **Insert or Ignore**: `ON CONFLICT ... DO NOTHING`을 사용하여, 데이터가 이미 존재할 경우 **무시**합니다. 이 방식은 거의 변경되지 않는 마스터 데이터(예: 재료 이름)에 적합합니다.

4.  **효율적인 ID 관리 (Efficient ID Management)**
    -   데이터 삽입 또는 업데이트 후 별도의 `SELECT` 쿼리 없이 `RETURNING id` 구문을 사용하여 `id`를 즉시 반환받습니다. 이는 `DO UPDATE` 전략과 함께 사용할 때 항상 `id`를 반환하므로 코드를 매우 간결하고 효율적으로 만듭니다.

---

## 2. 세부 실행 계획 (Upsert 전략 중심)

크롤링된 개별 레시피 데이터(JSON 또는 Dict 형태)를 처리하는 함수를 기준으로 설명합니다.

```python
# 처리할 데이터의 예상 구조
recipe_data = {
    "url": "http://example.com/recipe/123",
    "title": "더 맛있는 김치찌개",
    "description": "업그레이드된 한국인의 소울푸드",
    "image_url": "http://example.com/images/new_kimchi.jpg",
    "ingredients": [
        {"name": "돼지고기", "quantity_from": 350, "quantity_to": None, "unit": "g"},
        {"name": "묵은지", "quantity_from": 500, "quantity_to": None, "unit": "g"},
        {"name": "두부", "quantity_from": 1, "quantity_to": None, "unit": "모"}
    ]
}
```

### **데이터 삽입 절차 (단일 레시피 기준)**

1.  **DB 커넥션 풀(Connection Pool)에서 커넥션 획득**
    -   애플리케이션 시작 시점에 커넥션 풀을 생성하고, 데이터 삽입 시 풀에서 커넥션을 가져와 사용합니다. 작업이 끝나면 커넥션을 풀에 반환하여 재사용합니다.

2.  **트랜잭션 시작 (`BEGIN`)**
    -   데이터 정합성을 위해 모든 SQL 작업을 하나의 트랜잭션으로 묶습니다.

3.  **`recipes` 테이블에 데이터 Upsert**
    -   SQL: 
      ```sql
      INSERT INTO recipes (url, title, description, image_url) 
      VALUES (%s, %s, %s, %s) 
      ON CONFLICT (url) DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        image_url = EXCLUDED.image_url
      RETURNING recipe_id;
      ```
    -   `ON CONFLICT (url) DO UPDATE ...`: 동일한 `url`의 레시피가 존재하면 `title`, `description`, `image_url`을 새로 들어온 값(`EXCLUDED`.*)으로 업데이트합니다.
    -   `RETURNING recipe_id`: 삽입되거나 업데이트된 행의 `recipe_id`를 항상 반환하므로, 추가적인 `SELECT`가 필요 없어 코드가 간결해집니다.

4.  **`ingredients` 및 `recipe_ingredients` 테이블 처리 (재료 목록 순회)**
    -   반환받은 `recipe_id`를 사용하여 각 재료를 처리합니다.
    -   **For each `ingredient` in `recipe_data['ingredients']`:**
        a. **`ingredients` 테이블에 재료 Upsert (Insert or Ignore 방식 사용)**
            -   재료 이름은 거의 변경되지 않는 마스터 데이터이므로, `DO NOTHING` 전략이 더 적합하고 효율적입니다.
            -   SQL: `INSERT INTO ingredients (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING ingredient_id;`
            -   `RETURNING ingredient_id`가 값을 반환하지 않으면(기존에 재료가 있었던 경우), `SELECT ingredient_id FROM ingredients WHERE name = %s;`로 `id`를 조회합니다.

        b. **`recipe_ingredients` 테이블에 관계 Upsert**
            -   레시피에 사용되는 재료의 양은 변경될 수 있으므로 `DO UPDATE` 전략을 사용합니다.
            -   SQL: 
              ```sql
              INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity_from, quantity_to, unit) 
              VALUES (%s, %s, %s, %s, %s) 
              ON CONFLICT (recipe_id, ingredient_id) DO UPDATE SET
                quantity_from = EXCLUDED.quantity_from,
                quantity_to = EXCLUDED.quantity_to,
                unit = EXCLUDED.unit;
              ```

5.  **트랜잭션 종료 (`COMMIT`)**
    -   모든 SQL 작업이 성공적으로 완료되면 변경사항을 데이터베이스에 최종 반영합니다.

6.  **예외 처리**
    -   `try...except` 블록을 사용하여 2~5번 과정에서 오류 발생 시, `ROLLBACK`을 호출하여 트랜잭션 시작 이전 상태로 되돌립니다.
    -   오류가 발생한 레시피 정보는 별도의 로그 파일에 기록하여 추후 원인 분석 및 재처리를 용이하게 합니다.

---

## 3. 다음 단계

-   위 계획에 따라 `crawler.py` 파일에 `psycopg2` 라이브러리를 사용하여 실제 데이터베이스 삽입 로직을 구현합니다.
-   DB 접속 정보는 환경 변수 또는 별도의 설정 파일을 통해 안전하게 관리합니다.

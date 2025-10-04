1. \x07 제어문자 포함 재료명 찾기

SELECT COUNT(*) as total_count FROM ingredients WHERE name LIKE '%\x07%';
 total_count 
-------------
           0
(1 row)


fridge2fork=> SELECT id, name, original_name
fridge2fork-> FROM ingredients
fridge2fork-> WHERE name LIKE '%\x07%'
fridge2fork-> LIMIT 15;
 id | name | original_name 
----+------+---------------
(0 rows)


2. 대괄호 설명 포함 재료명 찾기

SELECT COUNT(*) as bracket_count FROM ingredients WHERE name LIKE '%[%]%';
 bracket_count 
---------------
         12789
(1 row)

SELECT id, name, original_name
FROM ingredients
WHERE name LIKE '%[%]%'
LIMIT 15;
  id  |               name                |           original_name           
------+-----------------------------------+-----------------------------------
 7336 | [아삭아삭 연근조림 재료] 간장\x07 | [아삭아삭 연근조림 재료] 간장\x07
 2785 | [녹차라떼 재료] 우유\x07          | [녹차라떼 재료] 우유\x07
 7338 | [재료] 얼갈이 데친 것\x07         | [재료] 얼갈이 데친 것\x07
    8 | [재료] 돼지고기 수육용삼겹살\x07  | [재료] 돼지고기 수육용삼겹살\x07
  723 | [딸기 샐러드 재료] 양상추\x07\x07 | [딸기 샐러드 재료] 양상추\x07\x07
 7341 | [알밥 재료] 크래미\x07            | [알밥 재료] 크래미\x07
 5024 | [재료] 크로와상생지\x07\x07\x07   | [재료] 크로와상생지\x07\x07\x07
 5028 | [재료] 고구마 작은 거\x07         | [재료] 고구마 작은 거\x07
 5683 | [재료] 돼지등뼈\x07               | [재료] 돼지등뼈\x07
 3571 | [재료] 더덕\x07\x07\x07           | [재료] 더덕\x07\x07\x07
 5033 | [재료] 아메리카노 커피 스틱\x07   | [재료] 아메리카노 커피 스틱\x07
   39 | [재료] 참치                       | [재료] 참치
 2809 | [재료] 마\x07\x07\x07             | [재료] 마\x07\x07\x07
   52 | [재료] 돼지고기\x07               | [재료] 돼지고기\x07
  748 | [재료] 연유\x07                   | [재료] 연유\x07
(15 rows)

3. "맛" 키워드 포함 브랜드명 찾기

SELECT COUNT(*) as brand_count FROM ingredients WHERE name LIKE '%맛%';
 brand_count 
-------------
         279
(1 row)

SELECT id, name, original_name
FROM ingredients
WHERE name LIKE '%맛%'
LIMIT 15;
  id  |                   name                    |               original_name               
------+-------------------------------------------+-------------------------------------------
 4371 | 투게더맛 우유\x07                         | 투게더맛 우유\x07
   98 | 오양 맛살\x07                             | 오양 맛살\x07
 5712 | 맛술\x07                                  | 맛술\x07
  402 | 맛소금\x07                                | 맛소금\x07
  440 | [재료] 게맛살\x07\x07\x07                 | [재료] 게맛살\x07\x07\x07
 5800 | 게맛살\x07                                | 게맛살\x07
 5801 | 맛살\x07                                  | 맛살\x07
 3742 | 맛소금\x07\x07                            | 맛소금\x07\x07
 9193 | 식용유\x07\x07\x07 [양념 재료] 맛간장\x07 | 식용유\x07\x07\x07 [양념 재료] 맛간장\x07
  551 | 저염 맛간장\x07                           | 저염 맛간장\x07
 4563 | 맛살전\x07\x07\x07                        | 맛살전\x07\x07\x07
 2191 | 허브맛 솔트\x07\x07                       | 허브맛 솔트\x07\x07
 2248 | 바나나맛 우유\x07                         | 바나나맛 우유\x07
 1500 | 맛술\x07\x07\x07                          | 맛술\x07\x07\x07
 6184 | 꽃게맛 간장\x07                           | 꽃게맛 간장\x07
(15 rows)

4. recipe_ingredients 테이블의 \x07 문제

SELECT COUNT(*) as qty_x07_count FROM recipe_ingredients WHERE quantity_text LIKE '%\x07%';
 qty_x07_count 
---------------
             0
(1 row)

SELECT id, quantity_text, unit, quantity_from, quantity_to
FROM recipe_ingredients
WHERE quantity_text LIKE '%\x07%'
LIMIT 10;
 id | quantity_text | unit | quantity_from | quantity_to 
----+---------------+------+---------------+-------------
(0 rows)
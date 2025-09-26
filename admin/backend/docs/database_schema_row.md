fridge2fork=> \dt public.*
                 List of relations
 Schema |        Name        | Type  |    Owner    
--------+--------------------+-------+-------------
 public | ingredients        | table | fridge2fork
 public | recipe_ingredients | table | fridge2fork
 public | recipes            | table | fridge2fork
(3 rows)

fridge2fork=> 


\d ingredients
                                               Table "public.ingredients"
      Column       |          Type          | Collation | Nullable |                      Default                       
-------------------+------------------------+-----------+----------+----------------------------------------------------
 ingredient_id     | integer                |           | not null | nextval('ingredients_ingredient_id_seq'::regclass)
 name              | character varying(100) |           | not null | 
 is_vague          | boolean                |           |          | false
 vague_description | character varying(20)  |           |          | 
Indexes:
    "ingredients_pkey" PRIMARY KEY, btree (ingredient_id)
    "idx_ingredients_is_vague" btree (is_vague)
    "idx_ingredients_name" btree (name)
    "ingredients_name_key" UNIQUE CONSTRAINT, btree (name)
Referenced by:
    TABLE "recipe_ingredients" CONSTRAINT "recipe_ingredients_ingredient_id_fkey" FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE

fridge2fork=> 

\d recipe_ingredients
                               Table "public.recipe_ingredients"
    Column     |         Type          | Collation | Nullable |            Default             
---------------+-----------------------+-----------+----------+--------------------------------
 recipe_id     | integer               |           | not null | 
 ingredient_id | integer               |           | not null | 
 quantity_from | numeric(10,2)         |           |          | 
 quantity_to   | numeric(10,2)         |           |          | 
 unit          | character varying(50) |           |          | 
 importance    | character varying(20) |           |          | 'essential'::character varying
Indexes:
    "recipe_ingredients_pkey" PRIMARY KEY, btree (recipe_id, ingredient_id)
    "idx_recipe_ingredients_importance" btree (importance)
    "idx_recipe_ingredients_ingredient_id" btree (ingredient_id)
    "idx_recipe_ingredients_recipe_id" btree (recipe_id)
Foreign-key constraints:
    "recipe_ingredients_ingredient_id_fkey" FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE
    "recipe_ingredients_recipe_id_fkey" FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE

fridge2fork=> 

fridge2fork=> \d recipes
                                           Table "public.recipes"
   Column    |           Type           | Collation | Nullable |                  Default                   
-------------+--------------------------+-----------+----------+--------------------------------------------
 recipe_id   | integer                  |           | not null | nextval('recipes_recipe_id_seq'::regclass)
 url         | character varying(255)   |           | not null | 
 title       | character varying(255)   |           | not null | 
 description | text                     |           |          | 
 image_url   | character varying(255)   |           |          | 
 created_at  | timestamp with time zone |           |          | CURRENT_TIMESTAMP
Indexes:
    "recipes_pkey" PRIMARY KEY, btree (recipe_id)
    "recipes_url_key" UNIQUE CONSTRAINT, btree (url)
Referenced by:
    TABLE "recipe_ingredients" CONSTRAINT "recipe_ingredients_recipe_id_fkey" FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE

fridge2fork=> 

\d+ public.*
             Index "public.idx_ingredients_is_vague"
  Column  |  Type   | Key? | Definition | Storage | Stats target 
----------+---------+------+------------+---------+--------------
 is_vague | boolean | yes  | is_vague   | plain   | 
btree, for table "public.ingredients"

                      Index "public.idx_ingredients_name"
 Column |          Type          | Key? | Definition | Storage  | Stats target 
--------+------------------------+------+------------+----------+--------------
 name   | character varying(100) | yes  | name       | extended | 
btree, for table "public.ingredients"

                 Index "public.idx_recipe_ingredients_importance"
   Column   |         Type          | Key? | Definition | Storage  | Stats target 
------------+-----------------------+------+------------+----------+--------------
 importance | character varying(20) | yes  | importance | extended | 
btree, for table "public.recipe_ingredients"

           Index "public.idx_recipe_ingredients_ingredient_id"
    Column     |  Type   | Key? |  Definition   | Storage | Stats target 
---------------+---------+------+---------------+---------+--------------
 ingredient_id | integer | yes  | ingredient_id | plain   | 
btree, for table "public.recipe_ingredients"

         Index "public.idx_recipe_ingredients_recipe_id"
  Column   |  Type   | Key? | Definition | Storage | Stats target 
-----------+---------+------+------------+---------+--------------
 recipe_id | integer | yes  | recipe_id  | plain   | 
btree, for table "public.recipe_ingredients"

                                                                                  Table "public.ingredients"
      Column       |          Type          | Collation | Nullable |                      Default                       | Storage  | Compression | Stats target |         Description         
-------------------+------------------------+-----------+----------+----------------------------------------------------+----------+-------------+--------------+-----------------------------
 ingredient_id     | integer                |           | not null | nextval('ingredients_ingredient_id_seq'::regclass) | plain    |             |              | 
 name              | character varying(100) |           | not null |                                                    | extended |             |              | 정규화된 재료 이름 (고유값)
 is_vague          | boolean                |           |          | false                                              | plain    |             |              | 
 vague_description | character varying(20)  |           |          |                                                    | extended |             |              | 
Indexes:
    "ingredients_pkey" PRIMARY KEY, btree (ingredient_id)
    "idx_ingredients_is_vague" btree (is_vague)
    "idx_ingredients_name" btree (name)
    "ingredients_name_key" UNIQUE CONSTRAINT, btree (name)
Referenced by:
    TABLE "recipe_ingredients" CONSTRAINT "recipe_ingredients_ingredient_id_fkey" FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE
Access method: heap

           Sequence "public.ingredients_ingredient_id_seq"
  Type   | Start | Minimum |  Maximum   | Increment | Cycles? | Cache 
---------+-------+---------+------------+-----------+---------+-------
 integer |     1 |       1 | 2147483647 |         1 | no      |     1
Owned by: public.ingredients.ingredient_id

                      Index "public.ingredients_name_key"
 Column |          Type          | Key? | Definition | Storage  | Stats target 
--------+------------------------+------+------------+----------+--------------
 name   | character varying(100) | yes  | name       | extended | 
unique, btree, for table "public.ingredients"

                     Index "public.ingredients_pkey"
    Column     |  Type   | Key? |  Definition   | Storage | Stats target 
---------------+---------+------+---------------+---------+--------------
 ingredient_id | integer | yes  | ingredient_id | plain   | 
primary key, btree, for table "public.ingredients"

                                                                        Table "public.recipe_ingredients"
    Column     |         Type          | Collation | Nullable |            Default             | Storage  | Compression | Stats target |               Description               
---------------+-----------------------+-----------+----------+--------------------------------+----------+-------------+--------------+-----------------------------------------
 recipe_id     | integer               |           | not null |                                | plain    |             |              | 
 ingredient_id | integer               |           | not null |                                | plain    |             |              | 
 quantity_from | numeric(10,2)         |           |          |                                | main     |             |              | 수량 (시작 범위 또는 단일 값)
 quantity_to   | numeric(10,2)         |           |          |                                | main     |             |              | 수량 (종료 범위, 범위가 아닐 경우 NULL)
 unit          | character varying(50) |           |          |                                | extended |             |              | 수량 단위 (예: g, 개, 큰술)
 importance    | character varying(20) |           |          | 'essential'::character varying | extended |             |              | 
Indexes:
    "recipe_ingredients_pkey" PRIMARY KEY, btree (recipe_id, ingredient_id)
    "idx_recipe_ingredients_importance" btree (importance)
    "idx_recipe_ingredients_ingredient_id" btree (ingredient_id)
    "idx_recipe_ingredients_recipe_id" btree (recipe_id)
Foreign-key constraints:
    "recipe_ingredients_ingredient_id_fkey" FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id) ON DELETE CASCADE
                 Index "public.recipe_ingredients_pkey"
    Column     |  Type   | Key? |  Definition   | Storage | Stats target 
---------------+---------+------+---------------+---------+--------------
 recipe_id     | integer | yes  | recipe_id     | plain   | 
 ingredient_id | integer | yes  | ingredient_id | plain   | 
primary key, btree, for table "public.recipe_ingredients"

                                                                             Table "public.recipes"
   Column    |           Type           | Collation | Nullable |                  Default                   | Storage  | Compression | Stats target |        Description         
-------------+--------------------------+-----------+----------+--------------------------------------------+----------+-------------+--------------+----------------------------
 recipe_id   | integer                  |           | not null | nextval('recipes_recipe_id_seq'::regclass) | plain    |             |              | 레시피 고유 ID (자동 증가)
 url         | character varying(255)   |           | not null |                                            | extended |             |              | 레시피 원본 URL (고유값)
 title       | character varying(255)   |           | not null |                                            | extended |             |              | 
 description | text                     |           |          |                                            | extended |             |              | 
 image_url   | character varying(255)   |           |          |                                            | extended |             |              | 
 created_at  | timestamp with time zone |           |          | CURRENT_TIMESTAMP                          | plain    |             |              | 
Indexes:
    "recipes_pkey" PRIMARY KEY, btree (recipe_id)
    "recipes_url_key" UNIQUE CONSTRAINT, btree (url)
Referenced by:
    TABLE "recipe_ingredients" CONSTRAINT "recipe_ingredients_recipe_id_fkey" FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
Access method: heap

                   Index "public.recipes_pkey"
  Column   |  Type   | Key? | Definition | Storage | Stats target 
-----------+---------+------+------------+---------+--------------
 recipe_id | integer | yes  | recipe_id  | plain   | 
primary key, btree, for table "public.recipes"

               Sequence "public.recipes_recipe_id_seq"
  Type   | Start | Minimum |  Maximum   | Increment | Cycles? | Cache 
---------+-------+---------+------------+-----------+---------+-------
 integer |     1 |       1 | 2147483647 |         1 | no      |     1
Owned by: public.recipes.recipe_id

                        Index "public.recipes_url_key"
 Column |          Type          | Key? | Definition | Storage  | Stats target 
--------+------------------------+------+------------+----------+--------------
 url    | character varying(255) | yes  | url        | extended | 
unique, btree, for table "public.recipes"
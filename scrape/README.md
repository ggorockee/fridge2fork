# 만개의 레시피 크롤러 (10000 Recipe Crawler)

이 프로젝트는 [만개의 레시피](https://www.10000recipe.com/recipe/list.html) 웹사이트에서 레시피 정보를 수집하는 Python 스크립트입니다.

## 주요 기능

-   레시피 목록을 순회하며 각 레시피의 상세 정보를 추출합니다.
-   추출하는 정보: 레시피 제목, 이미지 주소, 상세 내용, 재료.
-   (추후 기능 추가: 수집된 데이터를 CSV 또는 JSON 파일로 저장)

## 설치 방법

1.  이 저장소를 복제(clone)합니다.
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  필요한 Python 라이브러리를 설치합니다.
    ```bash
    pip install requests beautifulsoup4
    ```

## 기본 사용법

터미널에서 다음 명령어를 실행하여 크롤러를 시작합니다.

```bash
python crawler.py
```

스크립트 실행이 완료되면, (추후 구현) `recipes.csv` 파일에 수집된 레시피 정보가 저장됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

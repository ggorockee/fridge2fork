# 기술 사양

이 문서는 `crawler.py` 스크립트의 기술적인 아키텍처, 주요 컴포넌트, 데이터 구조 및 향후 확장 방안을 설명합니다. 이 문서는 스크립트를 수정하거나 확장하려는 개발자를 대상으로 합니다.

## 아키텍처 개요

스크립트는 모듈식으로 구성되어 있으며, 각 함수가 명확히 정의된 단일 책임을 갖습니다. 실행 흐름은 다음과 같습니다.

1.  `if __name__ == "__main__"`: 스크립트의 진입점.
2.  `main()`: 전체 프로세스를 조율하는 메인 함수.
    -   HTTP 요청을 보내 레시피 목록 페이지를 가져옵니다.
    -   `get_recipe_links()`를 호출하여 상세 페이지 URL 목록을 얻습니다.
    -   URL 목록을 순회하며 각 URL에 대해 `scrape_recipe_details()`를 호출합니다.
    -   반환된 상세 정보를 콘솔에 출력합니다.

## 주요 컴포넌트 (함수)

-   `get_recipe_links(soup)`
    -   **역할**: BeautifulSoup 객체를 입력받아 레시피 상세 페이지의 URL 목록을 반환합니다.
    -   **특징**: 사이트 구조 변경에 대한 1차적인 대응을 위해 기본 선택자와 대체 선택자, 두 가지를 사용합니다.
    -   **반환**: URL 문자열을 담은 리스트(list).

-   `scrape_recipe_details(url, headers)`
    -   **역할**: 단일 레시피 URL을 입력받아 해당 페이지의 모든 유의미한 정보를 스크랩합니다.
    -   **특징**: 제목, 재료, 조리 순서를 각각 다른 CSS 선택자를 사용하여 추출합니다. 재료의 경우 두 가지 다른 HTML 구조에 대응할 수 있습니다.
    -   **반환**: 스크랩된 정보를 담은 딕셔너리(dict). 실패 시 `None`.

-   `main()`
    -   **역할**: 스크립트의 전체 실행 흐름을 관리합니다.
    -   **특징**: 에러 핸들링(try-except)을 통해 HTTP 요청 실패나 기타 예외 발생 시 프로그램이 비정상적으로 종료되는 것을 방지합니다.

## 데이터 구조

`scrape_recipe_details` 함수는 다음 구조를 가진 딕셔너리를 반환합니다.

```json
{
  "title": "string",
  "ingredients": ["string", "string", ...],
  "steps": ["string", "string", ...]
}
```

## CSS 선택자 목록

스크립트가 의존하는 주요 CSS 선택자 목록입니다. 웹사이트 구조 변경 시 이 부분을 가장 먼저 확인해야 합니다.

| 대상 | 함수 | 선택자 |
| --- | --- | --- |
| 레시피 링크 (기본) | `get_recipe_links` | `li.common_sp_list_li a.common_sp_link` |
| 레시피 링크 (대체) | `get_recipe_links` | `div.common_sp_thumb a` |
| 제목 | `scrape_recipe_details` | `div.view2_summary h3` |
| 재료 컨테이너 | `scrape_recipe_details` | `#divConfirmedMaterialArea` |
| 재료 항목 | `scrape_recipe_details` | `li` |
| 재료 양 | `scrape_recipe_details` | `span.ingre_unit` |
| 재료 항목 (대체) | `scrape_recipe_details` | `div.ready_ingre3 ul li` |
| 조리 순서 | `scrape_recipe_details` | `div.view_step_cont` |

## 향후 확장 방안

-   **데이터 저장**: 현재는 콘솔 출력만 하지만, 수집된 데이터를 CSV, JSON, 또는 데이터베이스에 저장하는 기능을 추가할 수 있습니다. `main` 함수에서 `scrape_recipe_details`의 반환값을 리스트에 저장한 후, 파일로 쓰는 로직을 추가하면 됩니다.
-   **커맨드 라인 인자**: `argparse` 라이브러리를 사용하여 스크랩할 레시피 개수, 출력 파일 경로 등을 커맨드 라인 인자로 받을 수 있도록 개선할 수 있습니다.
-   **로깅**: `print` 대신 Python의 `logging` 모듈을 사용하여 로그 레벨(INFO, DEBUG, ERROR)에 따라 체계적인 로그를 남기도록 개선할 수 있습니다.

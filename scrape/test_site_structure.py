#!/usr/bin/env python3
"""
만개의레시피 사이트 구조 테스트 스크립트
"""

import requests
from bs4 import BeautifulSoup
import re

def test_site_structure():
    """사이트 구조 테스트"""
    base_url = "https://www.10000recipe.com"
    
    # 테스트할 URL들
    test_urls = [
        f"{base_url}/recipe/list.html",
        f"{base_url}/recipe/list.html?order=reco",
        f"{base_url}/recipe/list.html?order=reco&page=1",
        f"{base_url}/recipe/7063127"  # 특정 레시피
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    for url in test_urls:
        print(f"\n=== 테스트 URL: {url} ===")
        try:
            response = session.get(url, timeout=30)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 페이지 제목
                title = soup.find('title')
                if title:
                    print(f"페이지 제목: {title.get_text()}")
                
                # 레시피 링크 찾기
                recipe_links = soup.find_all('a', href=re.compile(r'/recipe/\d+'))
                print(f"레시피 링크 수: {len(recipe_links)}")
                
                if recipe_links:
                    print("첫 번째 레시피 링크들:")
                    for i, link in enumerate(recipe_links[:5]):
                        print(f"  {i+1}. {link.get('href')}")
                
                # data-recipe-id 속성 찾기
                elements_with_recipe_id = soup.find_all(attrs={'data-recipe-id': True})
                print(f"data-recipe-id 속성을 가진 요소 수: {len(elements_with_recipe_id)}")
                
                if elements_with_recipe_id:
                    print("첫 번째 data-recipe-id들:")
                    for i, element in enumerate(elements_with_recipe_id[:5]):
                        print(f"  {i+1}. {element.get('data-recipe-id')}")
                
                # onclick 속성 찾기
                onclick_elements = soup.find_all(attrs={'onclick': re.compile(r'viewRecipe\(\d+\)')})
                print(f"onclick 속성을 가진 요소 수: {len(onclick_elements)}")
                
                if onclick_elements:
                    print("첫 번째 onclick 속성들:")
                    for i, element in enumerate(onclick_elements[:5]):
                        print(f"  {i+1}. {element.get('onclick')}")
                
                # HTML 구조 일부 출력
                print("\nHTML 구조 샘플:")
                body = soup.find('body')
                if body:
                    # 첫 번째 div 몇 개 출력
                    divs = body.find_all('div', limit=10)
                    for i, div in enumerate(divs):
                        if div.get('class') or div.get('id'):
                            print(f"  div {i+1}: class={div.get('class')}, id={div.get('id')}")
                
            else:
                print(f"요청 실패: {response.status_code}")
                
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    test_site_structure()

/**
 * 레시피 관리 페이지
 * API를 통한 레시피 데이터 조회, 생성, 수정, 삭제 기능
 */

"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, RecipeResponse, RecipeCreate } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<RecipeResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(0);
  const [itemsPerPage] = useState(20);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newRecipe, setNewRecipe] = useState<RecipeCreate>({
    url: "",
    title: "",
    description: "",
    image_url: "",
  });

  // 레시피 목록 조회
  const fetchRecipes = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('레시피 API 호출 중...', {
        skip: currentPage * itemsPerPage,
        limit: itemsPerPage,
        search: searchTerm || undefined,
      });
      const data = await api.getRecipes({
        skip: currentPage * itemsPerPage,
        limit: itemsPerPage,
        search: searchTerm || undefined,
      });
      console.log('레시피 API 응답:', data, '타입:', typeof data, '배열 여부:', Array.isArray(data));
      setRecipes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('레시피 API 오류:', err);
      setError(err instanceof Error ? err.message : "레시피를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 레시피 생성
  const handleCreateRecipe = async () => {
    try {
      if (!newRecipe.url || !newRecipe.title) {
        alert("URL과 제목은 필수입니다.");
        return;
      }

      await api.createRecipe(newRecipe);
      setNewRecipe({ url: "", title: "", description: "", image_url: "" });
      setShowCreateForm(false);
      fetchRecipes(); // 목록 새로고침
    } catch (err) {
      alert(err instanceof Error ? err.message : "레시피 생성에 실패했습니다.");
    }
  };

  // 레시피 삭제
  const handleDeleteRecipe = async (recipeId: number) => {
    if (!confirm("정말로 이 레시피를 삭제하시겠습니까?")) {
      return;
    }

    try {
      await api.deleteRecipe(recipeId);
      fetchRecipes(); // 목록 새로고침
    } catch (err) {
      alert(err instanceof Error ? err.message : "레시피 삭제에 실패했습니다.");
    }
  };

  // 검색 및 페이지 변경 시 데이터 조회
  useEffect(() => {
    fetchRecipes();
  }, [currentPage, searchTerm]);

  // 네비게이션 메뉴
  const menuItems = [
    { label: "홈", href: "/", active: false },
    { label: "레시피 관리", href: "/recipes", active: true },
    { label: "식재료 관리", href: "/ingredients", active: false },
    { label: "시스템", href: "/system", active: false },
  ];

  const actionButtons = (
    <div className="flex items-center space-x-2">
      <Button variant="ghost" size="sm">
        로그아웃
      </Button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 네비게이션 바 */}
      <Navbar
        brand={
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">F2F</span>
            </div>
            <span className="text-xl font-semibold text-gray-100">Fridge2Fork</span>
          </div>
        }
        menuItems={menuItems}
        actions={actionButtons}
        glass={true}
        fixed={true}
      />

      {/* 메인 콘텐츠 */}
      <div className="pt-24 px-8 pb-8">
        <div className="max-w-7xl mx-auto">
          {/* 헤더 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-100 mb-2">레시피 관리</h1>
            <p className="text-gray-400">레시피 데이터를 조회하고 관리할 수 있습니다.</p>
          </div>

          {/* 검색 및 액션 바 */}
          <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex-1 max-w-md">
              <Input
                label="레시피 검색"
                placeholder="레시피 제목으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button
              variant="primary"
              onClick={() => setShowCreateForm(!showCreateForm)}
            >
              {showCreateForm ? "취소" : "새 레시피 추가"}
            </Button>
          </div>

          {/* 레시피 생성 폼 */}
          {showCreateForm && (
            <Card variant="glass" className="mb-6">
              <CardHeader>
                <CardTitle>새 레시피 추가</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="URL *"
                    placeholder="레시피 원본 URL"
                    value={newRecipe.url}
                    onChange={(e) => setNewRecipe({ ...newRecipe, url: e.target.value })}
                    required
                  />
                  <Input
                    label="제목 *"
                    placeholder="레시피 제목"
                    value={newRecipe.title}
                    onChange={(e) => setNewRecipe({ ...newRecipe, title: e.target.value })}
                    required
                  />
                  <Input
                    label="이미지 URL"
                    placeholder="레시피 이미지 URL"
                    value={newRecipe.image_url || ""}
                    onChange={(e) => setNewRecipe({ ...newRecipe, image_url: e.target.value })}
                  />
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-100 mb-2">
                      설명
                    </label>
                    <textarea
                      className="w-full px-4 py-3 bg-white/5 border border-white/8 rounded-lg text-sm text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent resize-none"
                      rows={3}
                      placeholder="레시피 설명"
                      value={newRecipe.description || ""}
                      onChange={(e) => setNewRecipe({ ...newRecipe, description: e.target.value })}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="ghost" onClick={() => setShowCreateForm(false)}>
                    취소
                  </Button>
                  <Button variant="primary" onClick={handleCreateRecipe}>
                    레시피 추가
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 에러 메시지 */}
          {error && (
            <Card variant="outlined" className="mb-6 border-red-500/50">
              <CardContent className="pt-6">
                <div className="text-red-400 text-center">
                  <p className="font-medium">오류가 발생했습니다</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 레시피 목록 */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-400"></div>
              <p className="text-gray-400 mt-4">레시피를 불러오는 중...</p>
            </div>
          ) : recipes.length === 0 ? (
            <Card variant="outlined">
              <CardContent className="pt-6">
                <div className="text-center text-gray-400">
                  <p className="font-medium">레시피가 없습니다</p>
                  <p className="text-sm mt-1">
                    {searchTerm ? "검색 결과가 없습니다." : "새로운 레시피를 추가해보세요."}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recipes.map((recipe) => (
                <Card key={recipe.recipe_id} variant="default" hoverable>
                  <CardContent className="p-0">
                    {/* 레시피 이미지 */}
                    {recipe.image_url && (
                      <div className="relative h-48 overflow-hidden rounded-t-xl">
                        <img
                          src={recipe.image_url}
                          alt={recipe.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    
                    <div className="p-6">
                      {/* 레시피 정보 */}
                      <div className="mb-4">
                        <h3 className="text-lg font-semibold text-gray-100 mb-2 line-clamp-2">
                          {recipe.title}
                        </h3>
                        {recipe.description && (
                          <p className="text-sm text-gray-400 line-clamp-3">
                            {recipe.description}
                          </p>
                        )}
                      </div>

                      {/* 메타 정보 */}
                      <div className="mb-4 text-xs text-gray-500">
                        <p>ID: {recipe.recipe_id}</p>
                        <p>생성일: {new Date(recipe.created_at).toLocaleDateString('ko-KR')}</p>
                      </div>

                      {/* 액션 버튼들 */}
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="flex-1"
                          onClick={() => window.open(recipe.url, '_blank')}
                        >
                          원본 보기
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-400 hover:text-red-300"
                          onClick={() => handleDeleteRecipe(recipe.recipe_id)}
                        >
                          삭제
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* 페이지네이션 */}
          {recipes.length > 0 && (
            <div className="mt-8 flex justify-center items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                disabled={currentPage === 0}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                이전
              </Button>
              <span className="text-gray-400 text-sm">
                페이지 {currentPage + 1}
              </span>
              <Button
                variant="ghost"
                size="sm"
                disabled={recipes.length < itemsPerPage}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                다음
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

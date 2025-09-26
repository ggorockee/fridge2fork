/**
 * 식재료 관리 페이지
 * 식재료 목록 조회, 생성, 수정, 삭제 기능
 */

"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api, IngredientResponse, IngredientCreate } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function IngredientsPage() {
  const [ingredients, setIngredients] = useState<IngredientResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(0);
  const [itemsPerPage] = useState(20);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newIngredient, setNewIngredient] = useState<IngredientCreate>({
    name: "",
    is_vague: false,
    vague_description: "",
  });

  // 식재료 목록 조회
  const fetchIngredients = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('식재료 API 호출 중...', {
        skip: currentPage * itemsPerPage,
        limit: itemsPerPage,
        search: searchTerm || undefined,
      });
      const data = await api.getIngredients({
        skip: currentPage * itemsPerPage,
        limit: itemsPerPage,
        search: searchTerm || undefined,
      });
      console.log('식재료 API 응답:', data, '타입:', typeof data, '배열 여부:', Array.isArray(data));
      setIngredients(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('식재료 API 오류:', err);
      setError(err instanceof Error ? err.message : "식재료를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 식재료 생성
  const handleCreateIngredient = async () => {
    try {
      if (!newIngredient.name) {
        alert("식재료 이름을 입력해주세요.");
        return;
      }

      await api.createIngredient(newIngredient);
      setNewIngredient({ name: "", is_vague: false, vague_description: "" });
      setShowCreateForm(false);
      fetchIngredients();
    } catch (err) {
      alert(err instanceof Error ? err.message : "식재료 생성에 실패했습니다.");
    }
  };

  // 식재료 삭제
  const handleDeleteIngredient = async (ingredientId: number, ingredientName: string) => {
    if (!confirm(`"${ingredientName}" 식재료를 삭제하시겠습니까?`)) {
      return;
    }

    try {
      await api.deleteIngredient(ingredientId);
      fetchIngredients();
    } catch (err) {
      alert(err instanceof Error ? err.message : "식재료 삭제에 실패했습니다.");
    }
  };

  // 페이지 변경
  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  // 검색
  const handleSearch = (term: string) => {
    setSearchTerm(term);
    setCurrentPage(0);
  };

  // 초기 데이터 로드
  useEffect(() => {
    fetchIngredients();
  }, [currentPage, searchTerm]);

  // 네비게이션 메뉴
  const menuItems = [
    { label: "홈", href: "/", active: false },
    { label: "레시피 관리", href: "/recipes", active: false },
    { label: "식재료 관리", href: "/ingredients", active: true },
    { label: "시스템", href: "/system", active: false },
  ];

  const actionButtons = (
    <div className="flex items-center space-x-2">
      <Button variant="ghost" size="sm" onClick={fetchIngredients} disabled={loading}>
        {loading ? "새로고침 중..." : "새로고침"}
      </Button>
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
            <span className="text-xl font-semibold text-gray-100">냉털레시피</span>
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
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-100 mb-2">식재료 관리</h1>
                <p className="text-gray-400">
                  총 {ingredients.length}개의 식재료
                </p>
              </div>
              {api.getOfflineMode() && (
                <div className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                  <span className="text-red-400 text-sm font-medium">오프라인 모드</span>
                </div>
              )}
            </div>
          </div>

          {/* 검색 및 필터 */}
          <div className="mb-6">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="식재료 이름으로 검색..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full"
                />
              </div>
              <Button
                variant="primary"
                onClick={() => setShowCreateForm(!showCreateForm)}
              >
                {showCreateForm ? "취소" : "새 식재료 추가"}
              </Button>
            </div>
          </div>

          {/* 식재료 생성 폼 */}
          {showCreateForm && (
            <Card variant="elevated" className="mb-6">
              <CardHeader>
                <CardTitle>새 식재료 추가</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    식재료 이름 *
                  </label>
                  <Input
                    type="text"
                    value={newIngredient.name}
                    onChange={(e) =>
                      setNewIngredient({ ...newIngredient, name: e.target.value })
                    }
                    placeholder="예: 김치, 돼지고기, 양파"
                    className="w-full"
                  />
                </div>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={newIngredient.is_vague}
                      onChange={(e) =>
                        setNewIngredient({ ...newIngredient, is_vague: e.target.checked })
                      }
                      className="rounded border-gray-600 bg-gray-700 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-300">모호한 식재료</span>
                  </label>
                </div>
                {newIngredient.is_vague && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      모호한 설명
                    </label>
                    <Input
                      type="text"
                      value={newIngredient.vague_description || ""}
                      onChange={(e) =>
                        setNewIngredient({ ...newIngredient, vague_description: e.target.value })
                      }
                      placeholder="예: 적당한 양, 조금"
                      className="w-full"
                    />
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <div className="flex space-x-2">
                  <Button variant="primary" onClick={handleCreateIngredient}>
                    식재료 추가
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewIngredient({ name: "", is_vague: false, vague_description: "" });
                    }}
                  >
                    취소
                  </Button>
                </div>
              </CardFooter>
            </Card>
          )}

          {/* 오류 메시지 */}
          {error && (
            <Card variant="elevated" className="mb-6 border-red-500/30">
              <CardContent className="pt-6">
                <div className="text-red-400">
                  <p className="font-medium">오류가 발생했습니다</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 식재료 목록 */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              <p className="text-gray-400 mt-4">식재료를 불러오는 중...</p>
            </div>
          ) : ingredients.length === 0 ? (
            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="text-center text-gray-400">
                  <p className="font-medium">식재료가 없습니다</p>
                  <p className="text-sm mt-1">
                    {searchTerm ? "검색 결과가 없습니다." : "새로운 식재료를 추가해보세요."}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {ingredients.map((ingredient) => (
                <Card key={ingredient.ingredient_id} variant="default" hoverable>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-100 mb-2">
                          {ingredient.name}
                        </h3>
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <span className={cn(
                              "text-xs px-2 py-1 rounded",
                              ingredient.is_vague 
                                ? "bg-yellow-500/20 text-yellow-400" 
                                : "bg-green-500/20 text-green-400"
                            )}>
                              {ingredient.is_vague ? "모호한 식재료" : "정확한 식재료"}
                            </span>
                          </div>
                          {ingredient.is_vague && ingredient.vague_description && (
                            <p className="text-sm text-gray-400">
                              설명: {ingredient.vague_description}
                            </p>
                          )}
                          <p className="text-xs text-gray-500">
                            ID: {ingredient.ingredient_id}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                  <CardFooter className="pt-0">
                    <div className="flex space-x-2 w-full">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="flex-1"
                        onClick={() => {
                          // TODO: 식재료 수정 기능 구현
                          alert("식재료 수정 기능은 준비 중입니다.");
                        }}
                      >
                        수정
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="flex-1 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        onClick={() =>
                          handleDeleteIngredient(ingredient.ingredient_id, ingredient.name)
                        }
                      >
                        삭제
                      </Button>
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}

          {/* 페이지네이션 */}
          {ingredients.length > 0 && (
            <div className="mt-8 flex items-center justify-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 0}
              >
                이전
              </Button>
              <span className="text-gray-400 text-sm">
                페이지 {currentPage + 1}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={ingredients.length < itemsPerPage}
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

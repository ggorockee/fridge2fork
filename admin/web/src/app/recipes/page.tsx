"use client";

import { useState, useEffect } from "react";
import { Container } from "@/components/layout/Container";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { serverApiClient } from "@/lib/api/client";

interface PendingRecipe {
  rcp_sno: number;
  rcp_ttl: string;
  ckg_nm: string;
  ckg_mtrl_cn: string;
  ckg_inbun_nm: string | null;
  ckg_dodf_nm: string | null;
  ckg_time_nm: string | null;
  rcp_img_url: string | null;
  import_batch_id: string;
  approval_status: string;
  created_at: string;
  updated_at: string;
}

interface PaginationInfo {
  page: number;
  size: number;
  total: number;
  total_pages: number;
}

/**
 * Recipes Management Page
 * PendingRecipe 목록 조회 및 상세 편집
 */
export default function RecipesPage() {
  const [recipes, setRecipes] = useState<PendingRecipe[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRecipe, setSelectedRecipe] = useState<PendingRecipe | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // 레시피 목록 조회
  const fetchRecipes = async (page: number = 1) => {
    try {
      setLoading(true);
      const response = await serverApiClient.get(`/fridge2fork/v1/admin/recipes`, {
        params: {
          page,
          size: 20,
        },
      });

      setRecipes(response.data.recipes);
      setPagination(response.data.pagination);
    } catch (error: any) {
      console.error("레시피 목록 조회 실패:", error);
      alert(`레시피 목록 조회 실패: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 레시피 상세 조회
  const fetchRecipeDetail = async (rcp_sno: number) => {
    try {
      const response = await serverApiClient.get(
        `/fridge2fork/v1/admin/recipes/${rcp_sno}`
      );
      setSelectedRecipe(response.data);
      setIsEditModalOpen(true);
    } catch (error: any) {
      console.error("레시피 상세 조회 실패:", error);
      alert(`레시피 상세 조회 실패: ${error.message}`);
    }
  };

  // 레시피 수정
  const updateRecipe = async (rcp_sno: number, data: any) => {
    try {
      await serverApiClient.patch(
        `/fridge2fork/v1/admin/recipes/${rcp_sno}`,
        data
      );
      alert("레시피가 성공적으로 수정되었습니다");
      setIsEditModalOpen(false);
      fetchRecipes(currentPage); // 목록 새로고침
    } catch (error: any) {
      console.error("레시피 수정 실패:", error);
      alert(`레시피 수정 실패: ${error.message}`);
    }
  };

  useEffect(() => {
    fetchRecipes(currentPage);
  }, [currentPage]);

  if (loading) {
    return (
      <Container className="py-8">
        <div className="flex justify-center items-center h-96">
          <LoadingSpinner size="lg" />
        </div>
      </Container>
    );
  }

  return (
    <Container className="py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold mb-2">레시피 관리</h1>
            <p className="text-muted-foreground">
              Pending 레시피 데이터를 조회하고 편집합니다
            </p>
          </div>
          <Button onClick={() => fetchRecipes(currentPage)}>새로고침</Button>
        </div>

        {/* 통계 */}
        {pagination && (
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-3xl font-bold">{pagination.total}</div>
                  <div className="text-sm text-muted-foreground">전체 레시피</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{pagination.page}</div>
                  <div className="text-sm text-muted-foreground">현재 페이지</div>
                </div>
                <div>
                  <div className="text-3xl font-bold">{pagination.total_pages}</div>
                  <div className="text-sm text-muted-foreground">전체 페이지</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 레시피 목록 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recipes.map((recipe) => (
            <Card key={recipe.rcp_sno} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-lg line-clamp-2">
                    {recipe.rcp_ttl}
                  </h3>
                  <Badge
                    variant={
                      recipe.approval_status === "pending"
                        ? "default"
                        : recipe.approval_status === "approved"
                        ? "success"
                        : "destructive"
                    }
                  >
                    {recipe.approval_status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {recipe.rcp_img_url && (
                  <div className="mb-3">
                    <img
                      src={recipe.rcp_img_url}
                      alt={recipe.rcp_ttl}
                      className="w-full h-40 object-cover rounded-md"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = "/placeholder-recipe.png";
                      }}
                    />
                  </div>
                )}
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">요리명:</span> {recipe.ckg_nm || "없음"}
                  </div>
                  <div>
                    <span className="font-medium">난이도:</span>{" "}
                    {recipe.ckg_dodf_nm || "미지정"}
                  </div>
                  <div>
                    <span className="font-medium">조리시간:</span>{" "}
                    {recipe.ckg_time_nm || "미지정"}
                  </div>
                  <div>
                    <span className="font-medium">인분:</span>{" "}
                    {recipe.ckg_inbun_nm || "미지정"}
                  </div>
                </div>
                <Button
                  className="w-full mt-4"
                  variant="outline"
                  onClick={() => fetchRecipeDetail(recipe.rcp_sno)}
                >
                  상세보기 / 편집
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 페이지네이션 */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex justify-center gap-2">
            <Button
              variant="outline"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
            >
              이전
            </Button>
            <div className="flex items-center gap-2 px-4">
              <span className="text-sm text-muted-foreground">
                {currentPage} / {pagination.total_pages}
              </span>
            </div>
            <Button
              variant="outline"
              disabled={currentPage === pagination.total_pages}
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              다음
            </Button>
          </div>
        )}
      </div>

      {/* 편집 모달 */}
      {isEditModalOpen && selectedRecipe && (
        <RecipeEditModal
          recipe={selectedRecipe}
          onClose={() => setIsEditModalOpen(false)}
          onSave={(data) => updateRecipe(selectedRecipe.rcp_sno, data)}
        />
      )}
    </Container>
  );
}

/**
 * 레시피 편집 모달
 */
function RecipeEditModal({
  recipe,
  onClose,
  onSave,
}: {
  recipe: any;
  onClose: () => void;
  onSave: (data: any) => void;
}) {
  const [formData, setFormData] = useState({
    ckg_time_nm: recipe.ckg_time_nm || "",
    ckg_dodf_nm: recipe.ckg_dodf_nm || "",
    ckg_inbun_nm: recipe.ckg_inbun_nm || "",
    rcp_img_url: recipe.rcp_img_url || "",
    approval_status: recipe.approval_status || "pending",
    rejection_reason: recipe.rejection_reason || "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">레시피 편집</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 기본 정보 (읽기 전용) */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">기본 정보</h3>
            <div>
              <label className="block text-sm font-medium mb-1">레시피 제목</label>
              <div className="p-3 bg-gray-100 rounded-md text-gray-700">
                {recipe.rcp_ttl}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">요리명</label>
              <div className="p-3 bg-gray-100 rounded-md text-gray-700">
                {recipe.ckg_nm || "없음"}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">재료 목록</label>
              <div className="p-3 bg-gray-100 rounded-md text-gray-700 max-h-32 overflow-y-auto text-sm">
                {recipe.ckg_mtrl_cn || "없음"}
              </div>
            </div>
          </div>

          {/* 이미지 미리보기 */}
          {formData.rcp_img_url && (
            <div>
              <label className="block text-sm font-medium mb-2">이미지 미리보기</label>
              <img
                src={formData.rcp_img_url}
                alt="Recipe"
                className="w-full max-h-64 object-cover rounded-md"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "/placeholder-recipe.png";
                }}
              />
            </div>
          )}

          {/* 편집 가능 필드 */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">편집 가능 정보</h3>

            <div>
              <label htmlFor="ckg_time_nm" className="block text-sm font-medium mb-1">
                조리 시간
              </label>
              <Input
                id="ckg_time_nm"
                type="text"
                value={formData.ckg_time_nm}
                onChange={(e) =>
                  setFormData({ ...formData, ckg_time_nm: e.target.value })
                }
                placeholder="예: 30분, 1시간 등"
              />
            </div>

            <div>
              <label htmlFor="ckg_dodf_nm" className="block text-sm font-medium mb-1">
                난이도
              </label>
              <select
                id="ckg_dodf_nm"
                value={formData.ckg_dodf_nm}
                onChange={(e) =>
                  setFormData({ ...formData, ckg_dodf_nm: e.target.value })
                }
                className="w-full p-2 border rounded-md"
              >
                <option value="">선택</option>
                <option value="초급">초급</option>
                <option value="중급">중급</option>
                <option value="고급">고급</option>
                <option value="아무나">아무나</option>
              </select>
            </div>

            <div>
              <label htmlFor="ckg_inbun_nm" className="block text-sm font-medium mb-1">
                인분
              </label>
              <Input
                id="ckg_inbun_nm"
                type="text"
                value={formData.ckg_inbun_nm}
                onChange={(e) =>
                  setFormData({ ...formData, ckg_inbun_nm: e.target.value })
                }
                placeholder="예: 2인분, 4인분 등"
              />
            </div>

            <div>
              <label htmlFor="rcp_img_url" className="block text-sm font-medium mb-1">
                이미지 URL
              </label>
              <Input
                id="rcp_img_url"
                type="url"
                value={formData.rcp_img_url}
                onChange={(e) =>
                  setFormData({ ...formData, rcp_img_url: e.target.value })
                }
                placeholder="https://..."
              />
            </div>

            <div>
              <label htmlFor="approval_status" className="block text-sm font-medium mb-1">
                승인 상태
              </label>
              <select
                id="approval_status"
                value={formData.approval_status}
                onChange={(e) =>
                  setFormData({ ...formData, approval_status: e.target.value })
                }
                className="w-full p-2 border rounded-md"
              >
                <option value="pending">대기중</option>
                <option value="approved">승인됨</option>
                <option value="rejected">거부됨</option>
              </select>
            </div>

            {formData.approval_status === "rejected" && (
              <div>
                <label htmlFor="rejection_reason" className="block text-sm font-medium mb-1">
                  거부 사유
                </label>
                <Input
                  id="rejection_reason"
                  type="text"
                  value={formData.rejection_reason}
                  onChange={(e) =>
                    setFormData({ ...formData, rejection_reason: e.target.value })
                  }
                  placeholder="거부 사유를 입력하세요"
                />
              </div>
            )}
          </div>

          {/* 버튼 */}
          <div className="flex gap-2 justify-end">
            <Button type="button" variant="outline" onClick={onClose}>
              취소
            </Button>
            <Button type="submit">저장</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

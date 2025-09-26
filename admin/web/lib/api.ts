/**
 * 냉털레시피 Admin API 클라이언트
 * OpenAPI 스펙에 따른 타입 안전한 API 호출 함수들
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE_URL = 'https://admin-api-dev.woohalabs.com/v1';

// API 응답 타입 정의
export interface RecipeResponse {
  url: string;
  title: string;
  description?: string;
  image_url?: string;
  recipe_id: number;
  created_at: string;
}

export interface IngredientResponse {
  name: string;
  is_vague: boolean;
  vague_description?: string;
  ingredient_id: number;
}

export interface RecipeCreate {
  url: string;
  title: string;
  description?: string;
  image_url?: string;
}

export interface IngredientCreate {
  name: string;
  is_vague?: boolean;
  vague_description?: string;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

// API 클라이언트 클래스
export class ColdRecipeAPI {
  private axiosInstance: AxiosInstance;

  constructor(baseUrl: string = API_BASE_URL) {
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터
    this.axiosInstance.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.axiosInstance.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        // 네트워크 오류나 404는 경고로만 표시
        if (error.code === 'NETWORK_ERROR' || error.response?.status === 404) {
          console.warn(`API 엔드포인트 없음: ${error.config?.url}`);
        } else {
          console.error('Response Error:', error.response?.data || error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // 헬스체크
  async healthCheck(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/health');
    return response.data;
  }

  // 시스템 정보 조회
  async getSystemInfo(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/system/info');
    return response.data;
  }

  // 데이터베이스 테이블 정보 조회
  async getDatabaseTables(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/system/database/tables');
    return response.data;
  }

  // 리소스 사용량 조회
  async getResourceUsage(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/system/resources');
    return response.data;
  }

  // API 엔드포인트 상태 조회
  async getApiEndpoints(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/system/api/endpoints');
    return response.data;
  }

  // 최근 활동 조회
  async getRecentActivities(): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get('/system/activities');
    return response.data;
  }

  // 레시피 관련 API
  async getRecipes(params: {
    skip?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<RecipeResponse[]> {
    const response: AxiosResponse<RecipeResponse[]> = await this.axiosInstance.get('/fridge2fork/v1/recipes/', {
      params,
    });
    return response.data;
  }

  async getRecipe(recipeId: number): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get(`/fridge2fork/v1/recipes/${recipeId}`);
    return response.data;
  }

  async createRecipe(recipe: RecipeCreate): Promise<RecipeResponse> {
    const response: AxiosResponse<RecipeResponse> = await this.axiosInstance.post('/fridge2fork/v1/recipes/', recipe);
    return response.data;
  }

  async updateRecipe(recipeId: number, recipe: Partial<RecipeCreate>): Promise<RecipeResponse> {
    const response: AxiosResponse<RecipeResponse> = await this.axiosInstance.put(`/fridge2fork/v1/recipes/${recipeId}`, recipe);
    return response.data;
  }

  async deleteRecipe(recipeId: number): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await this.axiosInstance.delete(`/fridge2fork/v1/recipes/${recipeId}`);
    return response.data;
  }

  // 식재료 관련 API
  async getIngredients(params: {
    skip?: number;
    limit?: number;
    search?: string;
    is_vague?: boolean;
  } = {}): Promise<IngredientResponse[]> {
    const response: AxiosResponse<IngredientResponse[]> = await this.axiosInstance.get('/fridge2fork/v1/ingredients/', {
      params,
    });
    return response.data;
  }

  async getIngredient(ingredientId: number): Promise<any> {
    const response: AxiosResponse = await this.axiosInstance.get(`/fridge2fork/v1/ingredients/${ingredientId}`);
    return response.data;
  }

  async createIngredient(ingredient: IngredientCreate): Promise<IngredientResponse> {
    const response: AxiosResponse<IngredientResponse> = await this.axiosInstance.post('/fridge2fork/v1/ingredients/', ingredient);
    return response.data;
  }

  async updateIngredient(ingredientId: number, ingredient: Partial<IngredientCreate>): Promise<IngredientResponse> {
    const response: AxiosResponse<IngredientResponse> = await this.axiosInstance.put(`/fridge2fork/v1/ingredients/${ingredientId}`, ingredient);
    return response.data;
  }

  async deleteIngredient(ingredientId: number): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await this.axiosInstance.delete(`/fridge2fork/v1/ingredients/${ingredientId}`);
    return response.data;
  }
}

// 기본 API 인스턴스
export const api = new ColdRecipeAPI();

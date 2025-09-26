/**
 * 냉털레시피 Admin API 클라이언트
 * OpenAPI 스펙에 따른 타입 안전한 API 호출 함수들
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// 환경별 API URL 설정
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // 클라이언트 사이드에서는 환경 변수 또는 기본값 사용
    return process.env.NEXT_PUBLIC_API_BASE_URL || 'https://admin-api-dev.woohalabs.com';
  }
  // 서버 사이드에서는 환경 변수 사용
  return process.env.API_BASE_URL || 'https://admin-api-dev.woohalabs.com';
};

const API_BASE_URL = getApiBaseUrl();
const API_FRIDGE2FORK_BASE_URL = `${API_BASE_URL}/fridge2fork`;
const API_V1_BASE_URL = `${API_BASE_URL}/fridge2fork/v1`;

// 네트워크 상태 확인
const isOnline = () => {
  if (typeof window !== 'undefined') {
    return navigator.onLine;
  }
  return true; // 서버 사이드에서는 항상 온라인으로 가정
};

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
  private isOfflineMode: boolean = false;

  constructor(baseUrl: string = API_BASE_URL) {
    this.axiosInstance = axios.create({
      baseURL: baseUrl,
      timeout: 5000, // 타임아웃을 5초로 단축
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // 오프라인 모드이거나 네트워크가 연결되지 않은 경우
        if (!isOnline() || this.isOfflineMode) {
          console.warn('오프라인 모드: API 요청이 차단되었습니다.');
          return Promise.reject(new Error('오프라인 모드'));
        }
        
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
      (error: AxiosError) => {
        // 네트워크 오류 처리
        if (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED' || !error.response) {
          console.warn(`네트워크 오류: ${error.config?.url} - 서버에 연결할 수 없습니다.`);
          this.isOfflineMode = true;
          
          // 3초 후 오프라인 모드 해제 시도
          setTimeout(() => {
            this.isOfflineMode = false;
          }, 3000);
        } else if (error.response?.status === 404) {
          console.warn(`API 엔드포인트 없음: ${error.config?.url}`);
        } else {
          console.error('Response Error:', error.response?.data || error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // 오프라인 모드 상태 확인
  getOfflineMode(): boolean {
    return this.isOfflineMode || !isOnline();
  }

  // 오프라인 모드 강제 설정/해제
  setOfflineMode(offline: boolean): void {
    this.isOfflineMode = offline;
  }

  // 헬스체크 (/fridge2fork/v1/health 경로 사용)
  async healthCheck(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/health');
      return response.data;
    } catch (error) {
      // 네트워크 오류 시 기본 응답 반환
      if (this.getOfflineMode()) {
        return {
          status: 'offline',
          message: '오프라인 모드',
          timestamp: new Date().toISOString()
        };
      }
      throw error;
    }
  }

  // 시스템 정보 조회 (/fridge2fork/v1/system/info 경로 사용)
  async getSystemInfo(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/system/info');
      return response.data;
    } catch (error) {
      if (this.getOfflineMode()) {
        return {
          status: 'offline',
          uptime: '오프라인 모드',
          version: '1.0.0',
          environment: 'development'
        };
      }
      throw error;
    }
  }

  // 데이터베이스 테이블 정보 조회 (/fridge2fork/v1/system/database/tables 경로 사용)
  async getDatabaseTables(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/system/database/tables');
      return response.data;
    } catch (error) {
      if (this.getOfflineMode()) {
        return {
          tables: [
            {
              name: 'recipes',
              rowCount: 0,
              size: '0 MB',
              indexSize: '0 MB',
              lastUpdated: new Date().toLocaleString('ko-KR'),
              status: 'active'
            },
            {
              name: 'ingredients',
              rowCount: 0,
              size: '0 MB',
              indexSize: '0 MB',
              lastUpdated: new Date().toLocaleString('ko-KR'),
              status: 'active'
            }
          ]
        };
      }
      throw error;
    }
  }

  // 리소스 사용량 조회 (/fridge2fork/v1/system/resources 경로 사용)
  async getResourceUsage(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/system/resources');
      return response.data;
    } catch (error) {
      if (this.getOfflineMode()) {
        return {
          cpu: {
            usage_percent: 0,
            cores: 0,
            load_average: [0, 0, 0]
          },
          memory: {
            usage_percent: 0,
            total_gb: 0,
            used_gb: 0,
            available_gb: 0
          },
          disk: {
            usage_percent: 0,
            total_gb: 0,
            used_gb: 0,
            available_gb: 0
          },
          network: {
            in_mbps: 0,
            out_mbps: 0,
            connections: 0
          }
        };
      }
      throw error;
    }
  }

  // API 엔드포인트 상태 조회 (/fridge2fork/v1/system/api/endpoints 경로 사용)
  async getApiEndpoints(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/system/api/endpoints');
      return response.data;
    } catch (error) {
      if (this.getOfflineMode()) {
        return {
          endpoints: [
            { path: '/fridge2fork/health', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
            { path: '/fridge2fork/v1/recipes/', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
            { path: '/fridge2fork/v1/ingredients/', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') }
          ]
        };
      }
      throw error;
    }
  }

  // 최근 활동 조회 (/fridge2fork/v1/system/activities 경로 사용)
  async getRecentActivities(): Promise<any> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/system/activities');
      return response.data;
    } catch (error) {
      if (this.getOfflineMode()) {
        return {
          activities: [
            { 
              id: '1', 
              type: 'error', 
              table: 'system', 
              user: 'admin', 
              timestamp: new Date().toLocaleString('ko-KR'), 
              details: '오프라인 모드 - API 서버 연결 불가' 
            }
          ]
        };
      }
      throw error;
    }
  }

  // 레시피 관련 API
  async getRecipes(params: {
    skip?: number;
    limit?: number;
    search?: string;
  } = {}): Promise<RecipeResponse[]> {
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/recipes/', {
        params,
      });
      // API 명세서에 따르면 { recipes: [], total, skip, limit } 형태로 응답
      return response.data.recipes || [];
    } catch (error) {
      if (this.getOfflineMode()) {
        // 오프라인 모드에서는 빈 배열 반환
        return [];
      }
      throw error;
    }
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
    try {
      const response: AxiosResponse = await this.axiosInstance.get('/fridge2fork/v1/ingredients/', {
        params,
      });
      // API 명세서에 따르면 { ingredients: [], total, skip, limit } 형태로 응답
      return response.data.ingredients || [];
    } catch (error) {
      if (this.getOfflineMode()) {
        // 오프라인 모드에서는 빈 배열 반환
        return [];
      }
      throw error;
    }
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

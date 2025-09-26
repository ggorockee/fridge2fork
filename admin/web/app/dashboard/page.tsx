/**
 * 관리자 대시보드 페이지
 * 시스템 상태, 데이터베이스 정보, 리소스 사용량 등 종합 모니터링
 */

"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// 시스템 정보 타입 정의
interface SystemInfo {
  status: 'healthy' | 'warning' | 'error';
  uptime: string;
  version: string;
  environment: 'development' | 'production';
}

interface DatabaseTable {
  name: string;
  rowCount: number;
  size: string;
  indexSize: string;
  lastUpdated: string;
  status: 'active' | 'inactive' | 'error';
}

interface ResourceUsage {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
}

interface ApiEndpoint {
  path: string;
  method: string;
  status: 'up' | 'down' | 'slow';
  responseTime: number;
  lastChecked: string;
}

interface RecentActivity {
  id: string;
  type: 'create' | 'update' | 'delete' | 'error';
  table: string;
  user: string;
  timestamp: string;
  details: string;
}

export default function DashboardPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [databaseTables, setDatabaseTables] = useState<DatabaseTable[]>([]);
  const [resourceUsage, setResourceUsage] = useState<ResourceUsage | null>(null);
  const [apiEndpoints, setApiEndpoints] = useState<ApiEndpoint[]>([]);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // 시스템 정보 조회
  const fetchSystemInfo = async () => {
    try {
      // 헬스체크로 시스템 상태 확인
      const healthData = await api.healthCheck();
      
      // 오프라인 모드인지 확인
      if (api.getOfflineMode() || healthData.status === 'offline') {
        setSystemInfo({
          status: 'error',
          uptime: '오프라인 모드',
          version: '1.0.0',
          environment: 'development'
        });
      } else {
        setSystemInfo({
          status: 'healthy',
          uptime: '개발 모드',
          version: '1.0.0',
          environment: 'development'
        });
      }
    } catch (error) {
      console.warn('헬스체크 실패. 시스템 오류로 간주합니다.');
      setSystemInfo({
        status: 'error',
        uptime: '연결 실패',
        version: '1.0.0',
        environment: 'development'
      });
    }
  };

  // 데이터베이스 테이블 정보 조회
  const fetchDatabaseTables = async () => {
    try {
      const tablesData = await api.getDatabaseTables();
      setDatabaseTables(tablesData.tables || []);
    } catch (error) {
      console.warn('데이터베이스 테이블 API 엔드포인트가 없습니다. 기본값을 사용합니다.');
      // API 엔드포인트가 없으므로 기본 테이블 정보 설정
      const defaultTables: DatabaseTable[] = [
        {
          name: 'recipes',
          rowCount: 0,
          size: '0 MB',
          indexSize: '0 MB',
          lastUpdated: new Date().toLocaleString('ko-KR'),
          status: api.getOfflineMode() ? 'inactive' : 'active'
        },
        {
          name: 'ingredients',
          rowCount: 0,
          size: '0 MB',
          indexSize: '0 MB',
          lastUpdated: new Date().toLocaleString('ko-KR'),
          status: api.getOfflineMode() ? 'inactive' : 'active'
        }
      ];
      setDatabaseTables(defaultTables);
    }
  };

  // 리소스 사용량 조회
  const fetchResourceUsage = async () => {
    try {
      const resourceData = await api.getResourceUsage();
      setResourceUsage({
        cpu: resourceData.cpu || 0,
        memory: resourceData.memory || 0,
        disk: resourceData.disk || 0,
        network: {
          in: resourceData.network?.in || 0,
          out: resourceData.network?.out || 0
        }
      });
    } catch (error) {
      console.warn('리소스 사용량 API 엔드포인트가 없습니다. 기본값을 사용합니다.');
      // 기본값 설정
      setResourceUsage({
        cpu: 0,
        memory: 0,
        disk: 0,
        network: {
          in: 0,
          out: 0
        }
      });
    }
  };

  // API 엔드포인트 상태 조회
  const fetchApiEndpoints = async () => {
    try {
      const endpointsData = await api.getApiEndpoints();
      setApiEndpoints(endpointsData.endpoints || []);
    } catch (error) {
      console.warn('API 엔드포인트 상태 API가 없습니다. 실제 엔드포인트를 확인합니다.');
      
      // 오프라인 모드인 경우 모든 엔드포인트를 down으로 설정
      if (api.getOfflineMode()) {
        const endpoints: ApiEndpoint[] = [
          { path: '/fridge2fork/health', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
          { path: '/fridge2fork/v1/recipes/', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
          { path: '/fridge2fork/v1/ingredients/', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') }
        ];
        setApiEndpoints(endpoints);
        return;
      }

      // 실제 API 호출로 상태 확인
      const endpoints: ApiEndpoint[] = [
        { path: '/fridge2fork/health', method: 'GET', status: 'up', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
        { path: '/fridge2fork/v1/recipes/', method: 'GET', status: 'up', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') },
        { path: '/fridge2fork/v1/ingredients/', method: 'GET', status: 'up', responseTime: 0, lastChecked: new Date().toLocaleString('ko-KR') }
      ];

      // 실제 API 호출로 상태 확인
      const checkEndpoints = async () => {
        const startTime = Date.now();
        try {
          await api.healthCheck();
          endpoints[0].responseTime = Date.now() - startTime;
          endpoints[0].status = 'up';
        } catch (error) {
          endpoints[0].status = 'down';
        }

        const recipesStartTime = Date.now();
        try {
          await api.getRecipes({ limit: 1 });
          endpoints[1].responseTime = Date.now() - recipesStartTime;
          endpoints[1].status = 'up';
        } catch (error) {
          endpoints[1].status = 'down';
        }

        const ingredientsStartTime = Date.now();
        try {
          await api.getIngredients({ limit: 1 });
          endpoints[2].responseTime = Date.now() - ingredientsStartTime;
          endpoints[2].status = 'up';
        } catch (error) {
          endpoints[2].status = 'down';
        }
      };

      await checkEndpoints();
      setApiEndpoints(endpoints);
    }
  };

  // 최근 활동 조회
  const fetchRecentActivities = async () => {
    try {
      const activitiesData = await api.getRecentActivities();
      setRecentActivities(activitiesData.activities || []);
    } catch (error) {
      console.warn('최근 활동 API 엔드포인트가 없습니다. 기본값을 사용합니다.');
      // 기본 활동 로그 (대시보드 접근 기록)
      const defaultActivities: RecentActivity[] = [
        { 
          id: '1', 
          type: 'create', 
          table: 'dashboard', 
          user: 'admin', 
          timestamp: new Date().toLocaleString('ko-KR'), 
          details: '대시보드 접근' 
        }
      ];
      setRecentActivities(defaultActivities);
    }
  };

  // 모든 데이터 조회
  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemInfo(),
        fetchDatabaseTables(),
        fetchResourceUsage(),
        fetchApiEndpoints(),
        fetchRecentActivities()
      ]);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('데이터 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 자동 새로고침
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000); // 30초마다 새로고침
    return () => clearInterval(interval);
  }, []);

  // 상태별 색상 반환
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'up':
        return 'text-green-400';
      case 'warning':
      case 'slow':
        return 'text-yellow-400';
      case 'error':
      case 'down':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // 활동 타입별 색상 반환
  const getActivityColor = (type: string) => {
    switch (type) {
      case 'create':
        return 'text-green-400';
      case 'update':
        return 'text-blue-400';
      case 'delete':
        return 'text-red-400';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  // 네비게이션 메뉴
  const menuItems = [
    { label: "홈", href: "/", active: true },
    { label: "레시피 관리", href: "/recipes", active: false },
    { label: "식재료 관리", href: "/ingredients", active: false },
    { label: "시스템", href: "/system", active: false },
  ];

  const actionButtons = (
    <div className="flex items-center space-x-2">
      <Button variant="ghost" size="sm" onClick={fetchAllData} disabled={loading}>
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
                <h1 className="text-3xl font-bold text-gray-100 mb-2">시스템 대시보드</h1>
                <p className="text-gray-400">
                  마지막 업데이트: {lastUpdated.toLocaleString('ko-KR')}
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

          {/* 시스템 상태 카드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">시스템 상태</p>
                    <p className={cn("text-2xl font-bold", getStatusColor(systemInfo?.status || 'unknown'))}>
                      {systemInfo?.status === 'healthy' ? '정상' : 
                       systemInfo?.status === 'warning' ? '주의' : '오류'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                    <div className="w-6 h-6 bg-green-400 rounded-full"></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">가동 시간</p>
                    <p className="text-2xl font-bold text-gray-100">{systemInfo?.uptime || '0일 0시간 0분'}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">총 레시피 수</p>
                    <p className="text-2xl font-bold text-gray-100">
                      {databaseTables.find(t => t.name === 'recipes')?.rowCount.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">총 식재료 수</p>
                    <p className="text-2xl font-bold text-gray-100">
                      {databaseTables.find(t => t.name === 'ingredients')?.rowCount.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 리소스 사용량 */}
          {resourceUsage && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">CPU 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.cpu}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-blue-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.cpu}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">메모리 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.memory}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-green-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.memory}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">디스크 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.disk}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-yellow-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.disk}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">네트워크</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">In</span>
                      <span className="text-sm text-gray-100">{resourceUsage.network.in} MB/s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Out</span>
                      <span className="text-sm text-gray-100">{resourceUsage.network.out} MB/s</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 데이터베이스 테이블 정보 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>데이터베이스 테이블 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {databaseTables.map((table) => (
                    <div key={table.name} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-100">{table.name}</span>
                          <span className={cn("text-xs px-2 py-1 rounded", 
                            table.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          )}>
                            {table.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          {table.rowCount.toLocaleString()} 행 • {table.size} • 인덱스: {table.indexSize}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          마지막 업데이트: {table.lastUpdated}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* API 엔드포인트 상태 */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>API 엔드포인트 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {apiEndpoints.map((endpoint, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={cn("text-xs px-2 py-1 rounded font-mono", 
                            endpoint.method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
                            endpoint.method === 'POST' ? 'bg-green-500/20 text-green-400' :
                            endpoint.method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-red-500/20 text-red-400'
                          )}>
                            {endpoint.method}
                          </span>
                          <span className="text-sm text-gray-100 font-mono">{endpoint.path}</span>
                        </div>
                        <div className="flex items-center gap-4 mt-1">
                          <span className={cn("text-xs", getStatusColor(endpoint.status))}>
                            {endpoint.status === 'up' ? '정상' : endpoint.status === 'slow' ? '느림' : '오류'}
                          </span>
                          <span className="text-xs text-gray-400">
                            {endpoint.responseTime}ms
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 최근 활동 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>최근 활동</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivities.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={cn("w-2 h-2 rounded-full", 
                        activity.type === 'create' ? 'bg-green-400' :
                        activity.type === 'update' ? 'bg-blue-400' :
                        activity.type === 'delete' ? 'bg-red-400' :
                        'bg-red-500'
                      )}></div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={cn("text-sm font-medium", getActivityColor(activity.type))}>
                            {activity.type === 'create' ? '생성' :
                             activity.type === 'update' ? '수정' :
                             activity.type === 'delete' ? '삭제' : '오류'}
                          </span>
                          <span className="text-sm text-gray-400">•</span>
                          <span className="text-sm text-gray-300">{activity.table}</span>
                          <span className="text-sm text-gray-400">•</span>
                          <span className="text-sm text-gray-400">{activity.user}</span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">{activity.details}</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">{activity.timestamp}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

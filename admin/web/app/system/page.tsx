/**
 * 시스템 관리 페이지
 * 시스템 정보, 데이터베이스 테이블, 리소스 사용량, API 엔드포인트 상태 관리
 */

"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SystemInfo {
  status: string;
  version: string;
  uptime: string;
  environment: string;
  timestamp: string;
}

interface DatabaseTable {
  name: string;
  row_count: number;
  status: string;
  last_updated: string;
}

interface ResourceUsage {
  cpu: {
    usage_percent: number;
    cores: number;
    load_average: number[];
  };
  memory: {
    usage_percent: number;
    total: number;
    used: number;
    available: number;
  };
  disk: {
    usage_percent: number;
    total: number;
    used: number;
    available: number;
  };
  network: {
    in_mbps: number;
    out_mbps: number;
    connections: number;
  };
}

interface ApiEndpoint {
  path: string;
  method: string;
  status: string;
  responseTime: number;
  lastChecked: string;
}

interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  user?: string;
}

export default function SystemPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [databaseTables, setDatabaseTables] = useState<DatabaseTable[]>([]);
  const [resourceUsage, setResourceUsage] = useState<ResourceUsage | null>(null);
  const [apiEndpoints, setApiEndpoints] = useState<ApiEndpoint[]>([]);
  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'database' | 'resources' | 'api' | 'activities'>('overview');
  const [refreshInterval, setRefreshInterval] = useState<number>(30); // 기본 30초
  const [customInterval, setCustomInterval] = useState<string>('60'); // 커스텀 간격 (초)
  const [isAutoRefresh, setIsAutoRefresh] = useState<boolean>(true);
  const [nextRefresh, setNextRefresh] = useState<Date>(new Date(Date.now() + 30000));
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // 시스템 정보 조회
  const fetchSystemInfo = async () => {
    try {
      const healthData = await api.healthCheck();
      const systemData = await api.getSystemInfo();
      
      if (api.getOfflineMode() || healthData.status === 'offline') {
        setSystemInfo({
          status: 'error',
          version: 'N/A',
          uptime: '오프라인 모드',
          environment: 'offline',
          timestamp: new Date().toISOString()
        });
      } else {
        setSystemInfo(systemData);
      }
    } catch (err) {
      console.error('시스템 정보 조회 실패:', err);
      setSystemInfo({
        status: 'error',
        version: 'N/A',
        uptime: '연결 실패',
        environment: 'unknown',
        timestamp: new Date().toISOString()
      });
    }
  };

  // 데이터베이스 테이블 조회
  const fetchDatabaseTables = async () => {
    try {
      console.log('데이터베이스 테이블 API 호출 중...');
      const tablesData = await api.getDatabaseTables();
      console.log('데이터베이스 테이블 응답:', tablesData);
      
      if (api.getOfflineMode()) {
        setDatabaseTables([]);
      } else {
        setDatabaseTables(tablesData.tables || []);
      }
    } catch (error) {
      console.warn('데이터베이스 테이블 API 엔드포인트가 없습니다. 기본값을 사용합니다.', error);
      // 기본 테이블 목록
      const defaultTables: DatabaseTable[] = [
        { name: 'recipes', row_count: 0, status: 'inactive', last_updated: new Date().toISOString() },
        { name: 'ingredients', row_count: 0, status: 'inactive', last_updated: new Date().toISOString() },
        { name: 'recipe_ingredients', row_count: 0, status: 'inactive', last_updated: new Date().toISOString() },
        { name: 'users', row_count: 0, status: 'inactive', last_updated: new Date().toISOString() },
        { name: 'categories', row_count: 0, status: 'inactive', last_updated: new Date().toISOString() },
      ];
      setDatabaseTables(defaultTables);
    }
  };

  // 리소스 사용량 조회
  const fetchResourceUsage = async () => {
    try {
      const usageData = await api.getResourceUsage();
      setResourceUsage(usageData);
    } catch (err) {
      console.error('리소스 사용량 조회 실패:', err);
      setResourceUsage(null);
    }
  };

  // API 엔드포인트 상태 조회
  const fetchApiEndpoints = async () => {
    try {
      const endpointsData = await api.getApiEndpoints();
      
      if (api.getOfflineMode()) {
        // 오프라인 모드에서는 모든 엔드포인트를 down으로 표시
        const offlineEndpoints: ApiEndpoint[] = [
          { path: '/fridge2fork/v1/health', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
          { path: '/fridge2fork/v1/recipes', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
          { path: '/fridge2fork/v1/ingredients', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
          { path: '/fridge2fork/v1/system/info', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
          { path: '/fridge2fork/v1/system/database/tables', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
          { path: '/fridge2fork/v1/system/resources', method: 'GET', status: 'down', responseTime: 0, lastChecked: new Date().toISOString() },
        ];
        setApiEndpoints(offlineEndpoints);
      } else {
        setApiEndpoints(endpointsData.endpoints || []);
      }
    } catch (err) {
      console.error('API 엔드포인트 상태 조회 실패:', err);
      setApiEndpoints([]);
    }
  };

  // 최근 활동 조회
  const fetchRecentActivities = async () => {
    try {
      const activitiesData = await api.getRecentActivities();
      setRecentActivities(activitiesData.activities || []);
    } catch (err) {
      console.error('최근 활동 조회 실패:', err);
      setRecentActivities([]);
    }
  };

  // 모든 데이터 조회
  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchSystemInfo(),
        fetchDatabaseTables(),
        fetchResourceUsage(),
        fetchApiEndpoints(),
        fetchRecentActivities(),
      ]);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 자동 새로고침
  useEffect(() => {
    fetchAllData();
    
    if (isAutoRefresh) {
      const interval = setInterval(() => {
        fetchAllData();
        setNextRefresh(new Date(Date.now() + refreshInterval * 1000));
      }, refreshInterval * 1000);
      
      return () => clearInterval(interval);
    }
  }, [refreshInterval, isAutoRefresh]);

  // 다음 새로고침 시간 업데이트
  useEffect(() => {
    if (isAutoRefresh) {
      const timer = setInterval(() => {
        setNextRefresh(new Date(Date.now() + refreshInterval * 1000));
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [refreshInterval, isAutoRefresh]);

  // 새로고침 간격 변경 핸들러
  const handleRefreshIntervalChange = (interval: number) => {
    setRefreshInterval(interval);
    setNextRefresh(new Date(Date.now() + interval * 1000));
  };

  // 커스텀 간격 적용
  const handleCustomIntervalApply = () => {
    const customSeconds = parseInt(customInterval);
    if (customSeconds >= 5 && customSeconds <= 300) { // 5초~5분 제한
      handleRefreshIntervalChange(customSeconds);
    }
  };

  // 자동 새로고침 토글
  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh);
    if (!isAutoRefresh) {
      setNextRefresh(new Date(Date.now() + refreshInterval * 1000));
    }
  };

  // 네비게이션 메뉴
  const menuItems = [
    { label: "홈", href: "/", active: false },
    { label: "레시피 관리", href: "/recipes", active: false },
    { label: "식재료 관리", href: "/ingredients", active: false },
    { label: "시스템", href: "/system", active: true },
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

  // 탭 렌더링
  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* 시스템 상태 카드 */}
      <Card variant="elevated">
        <CardHeader>
          <CardTitle>시스템 상태</CardTitle>
        </CardHeader>
        <CardContent>
          {systemInfo ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={cn(
                  "w-3 h-3 rounded-full mx-auto mb-2",
                  systemInfo.status === 'healthy' ? "bg-green-500" : "bg-red-500"
                )}></div>
                <p className="text-sm text-gray-400">상태</p>
                <p className="text-lg font-semibold text-gray-100">
                  {systemInfo.status === 'healthy' ? '정상' : '오류'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-400">버전</p>
                <p className="text-lg font-semibold text-gray-100">{systemInfo.version}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-400">가동 시간</p>
                <p className="text-lg font-semibold text-gray-100">{systemInfo.uptime}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-400">환경</p>
                <p className="text-lg font-semibold text-gray-100">{systemInfo.environment}</p>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-400">
              <p>시스템 정보를 불러올 수 없습니다.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 데이터베이스 요약 */}
      <Card variant="elevated">
        <CardHeader>
          <CardTitle>데이터베이스 요약</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-100">
                {databaseTables.find(t => t.name === 'recipes')?.row_count.toLocaleString() ?? 0}
              </p>
              <p className="text-sm text-gray-400">총 레시피 수</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-100">
                {databaseTables.find(t => t.name === 'ingredients')?.row_count.toLocaleString() ?? 0}
              </p>
              <p className="text-sm text-gray-400">총 식재료 수</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-100">
                {databaseTables.length}
              </p>
              <p className="text-sm text-gray-400">활성 테이블</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderDatabaseTab = () => (
    <Card variant="elevated">
      <CardHeader>
        <CardTitle>데이터베이스 테이블</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-gray-300">테이블명</th>
                <th className="text-left py-3 px-4 text-gray-300">행 수</th>
                <th className="text-left py-3 px-4 text-gray-300">상태</th>
                <th className="text-left py-3 px-4 text-gray-300">마지막 업데이트</th>
              </tr>
            </thead>
            <tbody>
              {databaseTables.map((table) => (
                <tr key={table.name} className="border-b border-gray-800">
                  <td className="py-3 px-4 text-gray-100 font-medium">{table.name}</td>
                  <td className="py-3 px-4 text-gray-300">{table.row_count.toLocaleString()}</td>
                  <td className="py-3 px-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      table.status === 'active' 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-gray-500/20 text-gray-400"
                    )}>
                      {table.status === 'active' ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-400 text-sm">
                    {new Date(table.last_updated).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  const renderResourcesTab = () => (
    <div className="space-y-6">
      {resourceUsage ? (
        <>
          {/* CPU 사용량 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>CPU 사용량</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-bold text-gray-100">{resourceUsage.cpu?.usage_percent ?? 0}%</span>
                  <p className="text-sm text-gray-400 mt-1">
                    {resourceUsage.cpu?.cores ?? 0}개 코어
                  </p>
                </div>
                <div className="w-24 h-24">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-gray-700"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${resourceUsage.cpu?.usage_percent ?? 0}, 100`}
                      className="text-orange-500"
                    />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 메모리 사용량 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>메모리 사용량</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-bold text-gray-100">{resourceUsage.memory?.usage_percent ?? 0}%</span>
                  <p className="text-sm text-gray-400 mt-1">
                    {((resourceUsage.memory?.used ?? 0) / 1024 / 1024 / 1024).toFixed(1)}GB / {((resourceUsage.memory?.total ?? 0) / 1024 / 1024 / 1024).toFixed(1)}GB
                  </p>
                </div>
                <div className="w-24 h-24">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-gray-700"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${resourceUsage.memory?.usage_percent ?? 0}, 100`}
                      className="text-blue-500"
                    />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 디스크 사용량 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>디스크 사용량</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-bold text-gray-100">{resourceUsage.disk?.usage_percent ?? 0}%</span>
                  <p className="text-sm text-gray-400 mt-1">
                    {((resourceUsage.disk?.used ?? 0) / 1024 / 1024 / 1024).toFixed(1)}GB / {((resourceUsage.disk?.total ?? 0) / 1024 / 1024 / 1024).toFixed(1)}GB
                  </p>
                </div>
                <div className="w-24 h-24">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      className="text-gray-700"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${resourceUsage.disk?.usage_percent ?? 0}, 100`}
                      className="text-green-500"
                    />
                  </svg>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 네트워크 사용량 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>네트워크 사용량</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-100">{resourceUsage.network?.in_mbps ?? 0} MB/s</p>
                  <p className="text-sm text-gray-400">다운로드</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-100">{resourceUsage.network?.out_mbps ?? 0} MB/s</p>
                  <p className="text-sm text-gray-400">업로드</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card variant="elevated">
          <CardContent className="pt-6">
            <div className="text-center text-gray-400">
              <p>리소스 사용량 정보를 불러올 수 없습니다.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderApiTab = () => (
    <Card variant="elevated">
      <CardHeader>
        <CardTitle>API 엔드포인트 상태</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-gray-300">경로</th>
                <th className="text-left py-3 px-4 text-gray-300">메서드</th>
                <th className="text-left py-3 px-4 text-gray-300">상태</th>
                <th className="text-left py-3 px-4 text-gray-300">응답 시간</th>
                <th className="text-left py-3 px-4 text-gray-300">마지막 확인</th>
              </tr>
            </thead>
            <tbody>
              {apiEndpoints.map((endpoint, index) => (
                <tr key={index} className="border-b border-gray-800">
                  <td className="py-3 px-4 text-gray-100 font-mono text-sm">{endpoint.path}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                      {endpoint.method}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs",
                      endpoint.status === 'up' 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-red-500/20 text-red-400"
                    )}>
                      {endpoint.status === 'up' ? '정상' : '오류'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-300">{endpoint.responseTime}ms</td>
                  <td className="py-3 px-4 text-gray-400 text-sm">
                    {new Date(endpoint.lastChecked).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  const renderActivitiesTab = () => (
    <Card variant="elevated">
      <CardHeader>
        <CardTitle>최근 활동</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-800/50 rounded-lg">
                <div className="w-2 h-2 bg-orange-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-gray-100">{activity.description}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs text-gray-400">{activity.type}</span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-400">
                      {new Date(activity.timestamp).toLocaleString()}
                    </span>
                    {activity.user && (
                      <>
                        <span className="text-xs text-gray-500">•</span>
                        <span className="text-xs text-gray-400">{activity.user}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-400 py-8">
              <p>최근 활동이 없습니다.</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
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
                <h1 className="text-3xl font-bold text-gray-100 mb-2">시스템 관리</h1>
                <p className="text-gray-400">시스템 상태 및 리소스 모니터링</p>
                <p className="text-gray-500 text-sm">
                  마지막 업데이트: {lastUpdated.toLocaleString('ko-KR')}
                </p>
                {isAutoRefresh && (
                  <p className="text-gray-500 text-sm">
                    다음 새로고침: {nextRefresh.toLocaleString('ko-KR')}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-4">
                {/* 새로고침 간격 선택 */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-400">새로고침:</label>
                  <select
                    value={refreshInterval}
                    onChange={(e) => handleRefreshIntervalChange(parseInt(e.target.value))}
                    className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-gray-100"
                  >
                    <option value={5}>5초</option>
                    <option value={15}>15초</option>
                    <option value={30}>30초</option>
                    <option value={60}>1분</option>
                    <option value={120}>2분</option>
                    <option value={300}>5분</option>
                    <option value={-1}>커스텀</option>
                  </select>
                  
                  {refreshInterval === -1 && (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        value={customInterval}
                        onChange={(e) => setCustomInterval(e.target.value)}
                        min="5"
                        max="300"
                        className="w-16 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-gray-100"
                        placeholder="초"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCustomIntervalApply}
                        className="text-xs"
                      >
                        적용
                      </Button>
                    </div>
                  )}
                </div>

                {/* 자동 새로고침 토글 */}
                <Button
                  variant={isAutoRefresh ? "primary" : "ghost"}
                  size="sm"
                  onClick={toggleAutoRefresh}
                  className="text-xs"
                >
                  {isAutoRefresh ? "자동 ON" : "자동 OFF"}
                </Button>

                {api.getOfflineMode() && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg">
                    <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
                    <span className="text-red-400 text-sm font-medium">오프라인 모드</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 탭 네비게이션 */}
          <div className="mb-6">
            <div className="flex space-x-1 bg-gray-800/50 p-1 rounded-lg">
              {[
                { id: 'overview', label: '개요' },
                { id: 'database', label: '데이터베이스' },
                { id: 'resources', label: '리소스' },
                { id: 'api', label: 'API 상태' },
                { id: 'activities', label: '활동 로그' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                    activeTab === tab.id
                      ? "bg-orange-500 text-white"
                      : "text-gray-400 hover:text-gray-100 hover:bg-gray-700/50"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

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

          {/* 로딩 상태 */}
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              <p className="text-gray-400 mt-4">시스템 정보를 불러오는 중...</p>
            </div>
          ) : (
            <>
              {/* 탭 콘텐츠 */}
              {activeTab === 'overview' && renderOverviewTab()}
              {activeTab === 'database' && renderDatabaseTab()}
              {activeTab === 'resources' && renderResourcesTab()}
              {activeTab === 'api' && renderApiTab()}
              {activeTab === 'activities' && renderActivitiesTab()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

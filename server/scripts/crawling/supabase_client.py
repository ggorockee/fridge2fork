"""
Supabase MCP 클라이언트 래퍼
"""

class SupabaseMCPClient:
    """Supabase MCP 클라이언트"""
    
    @staticmethod
    def execute_sql(query: str):
        """SQL 실행"""
        # MCP Supabase 함수 호출을 위한 임포트
        try:
            # 전역으로 사용 가능한 MCP 함수들
            import __main__
            if hasattr(__main__, 'mcp_supabase_execute_sql'):
                return __main__.mcp_supabase_execute_sql({"query": query})
            else:
                # 직접 MCP 함수 호출
                from mcp_supabase import execute_sql
                return execute_sql(query)
        except Exception as e:
            print(f"Supabase 실행 오류: {e}")
            return None
    
    @staticmethod
    def apply_migration(name: str, query: str):
        """마이그레이션 적용"""
        try:
            import __main__
            if hasattr(__main__, 'mcp_supabase_apply_migration'):
                return __main__.mcp_supabase_apply_migration({
                    "name": name,
                    "query": query
                })
            else:
                from mcp_supabase import apply_migration
                return apply_migration(name, query)
        except Exception as e:
            print(f"마이그레이션 오류: {e}")
            return None

# 전역 클라이언트 인스턴스
supabase_client = SupabaseMCPClient()


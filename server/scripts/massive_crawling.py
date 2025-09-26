#!/usr/bin/env python3
"""
대규모 크롤링 시스템 (20만개 레시피)
- 자동 재시작 기능
- 진행률 추적
- 오류 복구
- 24시간 무인 운영
"""
import asyncio
import argparse
import sys
import os
import time
import json
import signal
from datetime import datetime, timedelta
from typing import Dict, List

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MassiveCrawler:
    """대규모 크롤링 관리자"""
    
    def __init__(self):
        self.target_total = 200000  # 20만개 목표
        self.batch_size = 5000      # 배치당 5,000개
        self.session_file = "crawling_session.json"
        self.log_file = f"massive_crawling_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.is_running = True
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러 - 안전한 종료"""
        print(f"\n🛑 시그널 {signum} 수신 - 안전하게 종료 중...")
        self.is_running = False
    
    def save_session(self, progress: Dict):
        """세션 정보 저장"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"세션 저장 오류: {e}")
    
    def load_session(self) -> Dict:
        """세션 정보 로드"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"세션 로드 오류: {e}")
        
        return {
            "total_crawled": 0,
            "current_batch": 1,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "failed_batches": [],
            "completed_batches": []
        }
    
    async def get_current_db_count(self) -> int:
        """현재 DB에 저장된 레시피 수 조회"""
        try:
            from scripts.crawling.database import recipe_storage
            stats = await recipe_storage.get_crawling_stats()
            return stats.get('total_recipes', 0)
        except Exception as e:
            print(f"DB 조회 오류: {e}")
            return 0
    
    def calculate_optimal_settings(self, remaining: int, time_limit_hours: int = 24) -> Dict:
        """최적 크롤링 설정 계산"""
        # 시간당 목표 레시피 수
        recipes_per_hour = remaining / time_limit_hours
        
        if recipes_per_hour <= 500:
            return {
                "mode": "safe",
                "delay": 2.0,
                "batch_size": 50,
                "description": "🛡️ 안전 모드"
            }
        elif recipes_per_hour <= 1500:
            return {
                "mode": "normal", 
                "delay": 1.0,
                "batch_size": 100,
                "description": "⚖️ 균형 모드"
            }
        elif recipes_per_hour <= 3000:
            return {
                "mode": "fast",
                "delay": 0.5,
                "batch_size": 150,
                "description": "⚡ 빠른 모드"
            }
        elif recipes_per_hour <= 5000:
            return {
                "mode": "turbo",
                "delay": 0.3,
                "batch_size": 200,
                "description": "🚀 터보 모드"
            }
        else:
            return {
                "mode": "extreme",
                "delay": 0.1,
                "batch_size": 300,
                "description": "🔥 극한 모드 (위험)"
            }
    
    def estimate_completion_time(self, remaining: int, settings: Dict) -> str:
        """완료 예상 시간 계산"""
        recipes_per_second = 1 / settings["delay"]
        total_seconds = remaining / recipes_per_second
        
        # 배치 처리 및 기타 오버헤드 고려 (30% 추가)
        total_seconds *= 1.3
        
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}일 {hours}시간 {minutes}분"
        elif hours > 0:
            return f"{hours}시간 {minutes}분"
        else:
            return f"{minutes}분"
    
    async def run_batch_crawling(self, target: int, settings: Dict) -> bool:
        """배치 크롤링 실행"""
        try:
            import subprocess
            
            cmd = [
                "python", "scripts/optimized_crawling.py",
                f"--{settings['mode']}",
                "--target", str(target)
            ]
            
            print(f"🚀 배치 크롤링 시작: {target}개 ({settings['description']})")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=7200  # 2시간 타임아웃
            )
            
            if result.returncode == 0:
                print(f"✅ 배치 완료: {target}개")
                return True
            else:
                print(f"❌ 배치 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ 배치 타임아웃: {target}개")
            return False
        except Exception as e:
            print(f"❌ 배치 오류: {e}")
            return False
    
    def log_progress(self, message: str):
        """진행상황 로깅"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"로그 저장 오류: {e}")
    
    async def massive_crawling(self, resume: bool = True):
        """대규모 크롤링 메인 함수"""
        self.log_progress("🚀 대규모 크롤링 시작 (20만개 목표)")
        
        # 세션 로드
        if resume:
            progress = self.load_session()
            self.log_progress(f"📂 기존 세션 로드: {progress.get('total_crawled', 0)}개 완료")
        else:
            progress = self.load_session()
            progress.update({
                "total_crawled": 0,
                "current_batch": 1,
                "start_time": datetime.now().isoformat(),
                "failed_batches": [],
                "completed_batches": []
            })
        
        start_time = datetime.fromisoformat(progress["start_time"])
        
        while self.is_running and progress["total_crawled"] < self.target_total:
            try:
                # 현재 DB 상태 확인
                current_db_count = await self.get_current_db_count()
                remaining = self.target_total - current_db_count
                
                if remaining <= 0:
                    self.log_progress(f"🎉 목표 달성! DB에 {current_db_count:,}개 레시피 저장됨")
                    break
                
                # 최적 설정 계산
                elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
                remaining_hours = max(24 - elapsed_hours, 1)  # 최소 1시간
                
                settings = self.calculate_optimal_settings(remaining, remaining_hours)
                estimated_time = self.estimate_completion_time(remaining, settings)
                
                # 진행상황 출력
                progress_percent = (current_db_count / self.target_total) * 100
                self.log_progress("=" * 60)
                self.log_progress(f"📊 진행률: {progress_percent:.1f}% ({current_db_count:,}/{self.target_total:,})")
                self.log_progress(f"📋 남은 레시피: {remaining:,}개")
                self.log_progress(f"⚙️ 현재 모드: {settings['description']}")
                self.log_progress(f"⏰ 예상 완료: {estimated_time}")
                self.log_progress(f"🕐 경과 시간: {elapsed_hours:.1f}시간")
                
                # 배치 크기 결정 (남은 수량에 맞춰 조정)
                batch_target = min(self.batch_size, remaining)
                
                # 배치 크롤링 실행
                success = await self.run_batch_crawling(batch_target, settings)
                
                if success:
                    progress["completed_batches"].append({
                        "batch": progress["current_batch"],
                        "target": batch_target,
                        "timestamp": datetime.now().isoformat(),
                        "mode": settings["mode"]
                    })
                    progress["total_crawled"] += batch_target
                    self.log_progress(f"✅ 배치 {progress['current_batch']} 완료")
                else:
                    progress["failed_batches"].append({
                        "batch": progress["current_batch"],
                        "target": batch_target,
                        "timestamp": datetime.now().isoformat(),
                        "mode": settings["mode"]
                    })
                    self.log_progress(f"❌ 배치 {progress['current_batch']} 실패")
                    
                    # 실패 시 잠시 대기 후 재시도
                    self.log_progress("⏱️ 30초 대기 후 재시도...")
                    await asyncio.sleep(30)
                
                progress["current_batch"] += 1
                progress["last_update"] = datetime.now().isoformat()
                
                # 세션 저장
                self.save_session(progress)
                
                # 배치 간 휴식 (서버 부하 방지)
                if settings["mode"] in ["turbo", "extreme"]:
                    rest_time = 60  # 1분 휴식
                    self.log_progress(f"😴 서버 부하 방지를 위해 {rest_time}초 휴식...")
                    await asyncio.sleep(rest_time)
                else:
                    await asyncio.sleep(10)  # 10초 휴식
                
            except Exception as e:
                self.log_progress(f"❌ 크롤링 오류: {e}")
                self.log_progress("⏱️ 60초 대기 후 재시도...")
                await asyncio.sleep(60)
        
        # 최종 결과
        final_count = await self.get_current_db_count()
        total_time = datetime.now() - start_time
        
        self.log_progress("=" * 60)
        self.log_progress("🎊 대규모 크롤링 완료!")
        self.log_progress(f"📊 최종 결과: {final_count:,}개 레시피")
        self.log_progress(f"🎯 목표 달성률: {(final_count/self.target_total)*100:.1f}%")
        self.log_progress(f"⏰ 총 소요 시간: {total_time}")
        self.log_progress(f"📈 성공한 배치: {len(progress.get('completed_batches', []))}개")
        self.log_progress(f"❌ 실패한 배치: {len(progress.get('failed_batches', []))}개")
        
        # 세션 파일 정리
        if final_count >= self.target_total:
            try:
                os.remove(self.session_file)
                self.log_progress("🧹 세션 파일 정리 완료")
            except:
                pass

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="대규모 레시피 크롤링 시스템 (20만개)")
    parser.add_argument("--target", type=int, default=200000, help="목표 레시피 수")
    parser.add_argument("--batch-size", type=int, default=5000, help="배치 크기")
    parser.add_argument("--resume", action="store_true", default=True, help="기존 세션 이어서 진행")
    parser.add_argument("--fresh", action="store_true", help="새로 시작")
    
    args = parser.parse_args()
    
    print("🔥 Fridge2Fork 대규모 크롤링 시스템")
    print("=" * 60)
    print(f"🎯 목표: {args.target:,}개 레시피")
    print(f"📦 배치 크기: {args.batch_size:,}개")
    print(f"🔄 이어서 진행: {'예' if args.resume and not args.fresh else '아니오'}")
    print("=" * 60)
    
    crawler = MassiveCrawler()
    crawler.target_total = args.target
    crawler.batch_size = args.batch_size
    
    try:
        asyncio.run(crawler.massive_crawling(resume=args.resume and not args.fresh))
    except KeyboardInterrupt:
        print("\n🛑 사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()

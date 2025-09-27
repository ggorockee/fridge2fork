"""
Gunicorn 설정 파일
OpenAPI 스키마 로딩 최적화 및 타임아웃 설정
"""
import multiprocessing
import os

# 서버 설정
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# 타임아웃 설정 (OpenAPI 스키마 로딩을 위한 충분한 시간)
timeout = 120  # 2분 타임아웃
keepalive = 30
graceful_timeout = 30

# 로깅 설정
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 성능 최적화
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 환경 설정
raw_env = [
    "ENVIRONMENT=prod",
]

# OpenAPI 스키마 로딩을 위한 추가 설정
def when_ready(server):
    """서버 준비 완료 시 실행"""
    server.log.info("🚀 Gunicorn 서버 준비 완료")
    server.log.info("OpenAPI 스키마 로딩을 위한 충분한 타임아웃 설정됨")

def worker_int(worker):
    """워커 종료 시 실행"""
    worker.log.info("워커 종료 중...")

def on_exit(server):
    """서버 종료 시 실행"""
    server.log.info("Gunicorn 서버 종료 완료")

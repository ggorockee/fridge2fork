# 1. 경량화된 파이썬 이미지를 기반으로 합니다.
FROM python:3.10-slim

# 2. 컨테이너 내 작업 디렉토리를 설정합니다.
WORKDIR /app

# 3. 의존성 파일을 먼저 복사하여 Docker 레이어 캐시를 활용합니다.
COPY requirements.txt .

# 4. pip를 업그레이드하고 의존성을 설치합니다. --no-cache-dir 옵션으로 이미지 크기를 최적화합니다.
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드를 컨테이너에 복사합니다.
COPY . .

# 6. 컨테이너가 시작될 때 실행할 기본 명령어를 설정합니다.
CMD ["python", "crawler.py"]

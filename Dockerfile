# 文件路径: Dockerfile (已修复挂载冲突)

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

# 【修复】不再使用 "COPY ./app/ ./"
# 而是精确地复制程序运行所必需的文件和文件夹
COPY ./app/requirements.txt .
COPY ./app/main.py .
COPY ./app/node_parser.py .
COPY ./app/templates/ ./templates/

# 修正命令顺序：必须先安装 pip 包，再运行 playwright
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps chromium

EXPOSE 8000

CMD ["python", "main.py"]

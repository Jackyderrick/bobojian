# 文件路径: Dockerfile
# 作用: 定义如何构建包含所有依赖的 Docker 镜像。

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY ./app/requirements.txt .
COPY ./app/ ./

# 【修复】修正命令顺序：必须先安装 pip 包，再运行 playwright
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps chromium

EXPOSE 8000

CMD ["python", "main.py"]
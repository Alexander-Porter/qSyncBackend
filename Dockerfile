# 使用官方Python运行时作为父镜像
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# 设置工作目录
WORKDIR /app
# 将当前目录内容复制到位于/app中的容器中docker build -t myapp .
COPY . /app
# 安装requirements.txt中的所有依赖，gunicorn
RUN pip install --no-cache-dir -r requirements.txt
# 使端口10080可供此容器外的环境使用
EXPOSE 8080
# 使用gunicorn运行app.py，假设您的FastAPI应用实例名为app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
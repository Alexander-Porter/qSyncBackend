# 使用官方Python运行时作为父镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到位于/app中的容器中
COPY . /app

# 安装requirements.txt中的所有依赖
RUN pip install --no-cache-dir -r requirements.txt

# 使端口10080可供此容器外的环境使用
EXPOSE 10080

# 定义环境变量，这里仅作为示例，实际值应在运行容器时通过-docker run的-e参数指定
ENV SQLALCHEMY_DATABASE_URI=""

# 运行app.py当容器启动时
CMD ["python", "app.py"]
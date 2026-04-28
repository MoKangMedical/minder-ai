# Minder AI红娘 - 多阶段构建
# 阶段1: 构建阶段
FROM python:3.12-slim as builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml setup.py setup.cfg ./
COPY requirements*.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# 阶段2: 运行阶段
FROM python:3.12-slim as runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    APP_USER=minder

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用用户
RUN groupadd -r ${APP_USER} && useradd -r -g ${APP_USER} -d ${APP_HOME} -s /sbin/nologin ${APP_USER}

# 设置工作目录
WORKDIR ${APP_HOME}

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p ${APP_HOME}/uploads/avatars \
    ${APP_HOME}/uploads/voices \
    ${APP_HOME}/logs \
    ${APP_HOME}/data && \
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME}

# 切换到非root用户
USER ${APP_USER}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "minder.main:app", \
     "--config", "deploy/gunicorn.conf.py", \
     "--bind", "0.0.0.0:8000"]

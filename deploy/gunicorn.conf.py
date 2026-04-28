# Minder AI红娘 - Gunicorn 配置文件
# 生产环境 WSGI 服务器配置

import multiprocessing
import os

# 服务器配置
bind = "0.0.0.0:8000"
backlog = 2048

# Worker 配置
# 推荐: CPU核心数 * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# 重启配置
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# 日志配置
accesslog = os.environ.get("ACCESS_LOG", "/app/logs/access.log")
errorlog = os.environ.get("ERROR_LOG", "/app/logs/error.log")
loglevel = os.environ.get("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "minder"

# 安全配置
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# 性能配置
preload_app = True
sendfile = True

# SSL配置（如果需要）
# keyfile = "/etc/ssl/private/minder.key"
# certfile = "/etc/ssl/certs/minder.crt"

# 环境变量
raw_env = [
    "APP_ENV=production",
]

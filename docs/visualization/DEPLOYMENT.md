# 部署指南

本文档描述如何部署 HyperGraphRAG Visualization API 到生产环境。

---

## 📋 前置要求

### 系统要求
- **操作系统**: Linux (Ubuntu 20.04+) / macOS
- **Python**: 3.9+
- **内存**: 最少 2GB，推荐 4GB+
- **存储**: 最少 10GB（取决于数据规模）

### 依赖服务
- **OpenAI API**: 需要有效的 API Key
- **可选**: Redis（用于缓存）
- **可选**: PostgreSQL（用于查询历史持久化）

---

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# OpenAI API 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# 数据目录
WORKING_DIR=expr/example
```

### 5. 生成数据（首次部署）

```bash
python script_construct.py
```

### 6. 启动服务

```bash
# 开发模式
python api/main.py

# 生产模式
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 验证部署

```bash
curl http://localhost:8000/api/health
```

---

## 🐳 Docker 部署

### 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 构建镜像

```bash
docker build -t hypergraphrag-api:latest .
```

### 运行容器

```bash
docker run -d \
  --name hypergraphrag-api \
  -p 8000:8000 \
  -v $(pwd)/expr:/app/expr \
  -e OPENAI_API_KEY=your_key \
  hypergraphrag-api:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_BASE=${OPENAI_API_BASE}
      - LOG_LEVEL=INFO
    volumes:
      - ./expr:/app/expr
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 可选: Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

启动：

```bash
docker-compose up -d
```

---

## ☁️ 云平台部署

### AWS 部署

#### 使用 EC2

1. **启动 EC2 实例**
   - 选择 Ubuntu 20.04 LTS
   - 实例类型: t3.medium 或更高
   - 配置安全组（开放 8000 端口）

2. **SSH 连接并部署**

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 克隆项目
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG

# 使用 Docker Compose 部署
docker-compose up -d
```

3. **配置域名和 HTTPS**

使用 Nginx 反向代理：

```nginx
# /etc/nginx/sites-available/hypergraphrag
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

配置 SSL（使用 Let's Encrypt）：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 使用 ECS (Elastic Container Service)

1. 推送镜像到 ECR
2. 创建 ECS 任务定义
3. 创建 ECS 服务
4. 配置 Application Load Balancer

### 阿里云部署

#### 使用 ECS

类似 AWS EC2 部署流程。

#### 使用容器服务 ACK

1. 创建 Kubernetes 集群
2. 部署应用到 ACK
3. 配置 SLB 负载均衡

---

## 🔒 生产环境配置

### 1. 环境变量管理

使用环境变量管理敏感信息，不要硬编码：

```bash
# 使用 .env 文件（不要提交到 Git）
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### 2. 日志配置

```python
# 在 api/main.py 中配置
import logging
from logging.handlers import RotatingFileHandler

# 配置日志轮转
handler = RotatingFileHandler(
    'logs/api.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
```

### 3. 性能优化

#### 使用多进程

```bash
# 使用 Gunicorn + Uvicorn workers
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

#### 启用缓存

```python
# 使用 Redis 缓存
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

### 4. 监控和告警

#### Prometheus + Grafana

```python
# 添加 Prometheus 指标
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

#### 健康检查

```python
@app.get("/api/health")
async def health_check():
    # 检查依赖服务
    checks = {
        "api": "ok",
        "database": await check_database(),
        "redis": await check_redis(),
    }
    
    if all(v == "ok" for v in checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail=checks)
```

### 5. 安全配置

#### HTTPS

强制使用 HTTPS：

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

#### CORS 配置

生产环境限制允许的源：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

#### API 认证

添加 JWT 认证：

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.get("/api/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # 验证 token
    ...
```

#### 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/query/")
@limiter.limit("10/minute")
async def query_endpoint():
    ...
```

---

## 📊 监控指标

### 关键指标

1. **请求指标**
   - 请求数（QPS）
   - 响应时间（P50, P95, P99）
   - 错误率

2. **系统指标**
   - CPU 使用率
   - 内存使用率
   - 磁盘 I/O

3. **业务指标**
   - 查询成功率
   - 平均查询时间
   - 活跃用户数

### 告警规则

```yaml
# Prometheus 告警规则
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowResponse
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 5
        for: 5m
        annotations:
          summary: "API response time too slow"
```

---

## 🔄 更新和维护

### 滚动更新

```bash
# 拉取最新代码
git pull origin main

# 重启服务（零停机）
docker-compose up -d --no-deps --build api
```

### 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz expr/

# 上传到云存储
aws s3 cp backup-*.tar.gz s3://your-bucket/backups/
```

### 日志管理

```bash
# 查看日志
docker-compose logs -f api

# 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 🐛 故障排查

### 常见问题

#### 1. API 启动失败

**症状**: 服务无法启动

**排查**:
```bash
# 检查日志
docker-compose logs api

# 检查端口占用
lsof -i :8000

# 检查环境变量
docker-compose config
```

#### 2. 查询超时

**症状**: 查询请求超时

**排查**:
- 检查 OpenAI API 连接
- 增加超时时间
- 检查数据规模

#### 3. 内存不足

**症状**: OOM 错误

**解决**:
- 增加服务器内存
- 优化数据加载
- 使用数据分片

---

## 📞 支持

如有问题，请：
1. 查看文档: `docs/visualization/`
2. 查看日志: `logs/api.log`
3. 提交 Issue: GitHub Issues

---

**最后更新**: 2025-10-21  
**维护者**: Tao An

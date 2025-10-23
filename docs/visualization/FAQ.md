# 常见问题解答 (FAQ)

## 安装和配置

### Q: 如何安装 HyperGraphRAG 可视化系统？

**A**: 有两种方式：

**方法 1 - Docker（推荐）**：
```bash
docker-compose up -d
```

**方法 2 - 本地开发**：
```bash
# 后端
pip install -r requirements.txt
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload

# 前端
cd web_ui
pnpm install
pnpm dev
```

详见 [快速开始指南](./QUICKSTART.md)

---

### Q: 需要什么系统要求？

**A**: 
- Python 3.10+
- Node.js 18+
- pnpm 8+
- 4GB+ RAM
- 现代浏览器（Chrome 90+, Firefox 88+, Safari 14+）

---

### Q: 如何配置 OpenAI API Key？

**A**: 
1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env` 文件：
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. 重启后端服务

---

## 使用问题

### Q: 图加载很慢怎么办？

**A**: 尝试以下方法：
1. 使用过滤器减少显示节点数
2. 启用"视口裁剪"（设置 → 性能）
3. 启用"懒加载"
4. 降低初始加载数量限制

---

### Q: 搜索没有结果？

**A**: 可能原因：
1. 关键词拼写错误
2. 实体不存在于知识库
3. 尝试更通用的关键词
4. 使用语义相关的词（系统支持语义搜索）

---

### Q: 查询返回错误怎么办？

**A**: 检查以下几点：
1. 确认 OpenAI API Key 已配置且有效
2. 检查网络连接
3. 查看浏览器控制台的错误信息
4. 确认后端服务正常运行（访问 http://localhost:3401/api/health）
5. 检查 API Key 余额是否充足

---

### Q: 节点标签重叠看不清？

**A**: 解决方法：
1. 放大视图（鼠标滚轮）
2. 增加"斥力强度"（设置 → 布局）
3. 调整"节点大小"和"标签字体大小"
4. 手动拖动节点调整位置

---

### Q: 如何重置视图？

**A**: 
- 点击工具栏的"重置视图"按钮
- 或按快捷键 `Ctrl/Cmd + 0`

---

## 功能问题

### Q: 什么是超边（Hyperedge）？

**A**: 超边是连接 3 个或更多实体的关系。例如：
- 普通边：A ↔ B（2 个实体）
- 超边：A ↔ B ↔ C（3+ 个实体）

在可视化中，超边用特殊样式（虚线或不同颜色）标识。

---

### Q: 查询模式有什么区别？

**A**: 
- **Local**: 基于实体描述，适合"What is X?"类问题
- **Global**: 基于关系描述，适合"How are X and Y related?"
- **Hybrid**: 结合两者，适合复杂问题（推荐）
- **Naive**: 简单 RAG，不使用图结构

---

### Q: 如何导出高质量图像？

**A**: 
1. 调整视图到最佳角度
2. 打开导出面板
3. 选择 PNG 格式
4. 设置高分辨率（300 DPI, 3000px 宽度）
5. 选择白色背景
6. 下载

或使用 SVG 格式获得矢量图（无限缩放不失真）。

---

### Q: 可以导出数据吗？

**A**: 可以。选择 JSON 格式导出，包含：
- 所有节点数据
- 所有边数据
- 布局位置信息

可用于导入其他工具（Gephi, Cytoscape）或数据分析。

---

## 数据问题

### Q: 如何使用自己的数据？

**A**: 
1. 准备文本数据（.txt, .md, .json 等）
2. 运行构建脚本：
   ```bash
   python script_construct.py
   ```
3. 数据保存在 `expr/example/` 目录
4. 重启可视化系统

---

### Q: 支持哪些数据格式？

**A**: 
- 纯文本（.txt）
- Markdown（.md）
- JSON（.json）
- 其他文本格式

HyperGraphRAG 会自动提取实体和关系。

---

### Q: 如何更新知识库？

**A**: 
1. 添加新文档到数据目录
2. 重新运行 `python script_construct.py`
3. 重启可视化系统
4. 新数据会自动加载

---

### Q: 数据存储在哪里？

**A**: 数据存储在 `working_dir` 目录（默认 `expr/example/`）：
- `vdb_entities.json`: 实体向量数据库
- `vdb_hyperedges.json`: 超边向量数据库
- `graph_chunk_entity_relation.graphml`: 图结构
- `kv_store_text_chunks.json`: 文本块
- `kv_store_llm_response_cache.json`: LLM 缓存

---

## 性能问题

### Q: 查询速度慢怎么办？

**A**: 优化方法：
1. 减少 `top_k` 参数（默认 60）
2. 使用更快的 LLM 模型
3. 启用查询缓存
4. 检查网络延迟
5. 使用 Local 或 Global 模式（比 Hybrid 快）

---

### Q: 大规模图如何优化性能？

**A**: 
1. 使用过滤器只显示关键节点
2. 启用"懒加载"（初始只加载 1000 节点）
3. 启用"视口裁剪"（只渲染可见区域）
4. 减少布局迭代次数
5. 使用预计算布局

---

### Q: 浏览器卡顿怎么办？

**A**: 
1. 关闭其他标签页释放内存
2. 使用 Chrome（性能最好）
3. 减少显示的节点数
4. 降低动画效果
5. 禁用实时布局更新

---

## 技术问题

### Q: 支持离线使用吗？

**A**: 
- 可视化界面：可以离线使用
- 查询功能：需要网络（调用 LLM API）
- 可以使用本地 LLM（需要配置）

---

### Q: 支持多语言吗？

**A**: 
- 界面：中文和英文
- 数据：支持任何语言（取决于 LLM）
- 可以添加更多界面语言

---

### Q: 如何集成到现有系统？

**A**: 
1. 使用 REST API（参考 [API 文档](../api/README.md)）
2. 嵌入 iframe
3. 使用 Docker 容器部署
4. 自定义开发（参考 [架构文档](./ARCHITECTURE.md)）

---

### Q: 支持哪些浏览器？

**A**: 
- ✅ Chrome 90+（推荐）
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ❌ IE 11（不支持）

---

### Q: 移动端可以使用吗？

**A**: 可以，支持响应式设计：
- 手机：全屏画布 + 底部抽屉
- 平板：可折叠侧边栏
- 支持触摸手势（双指缩放、单指拖动）

---

## 错误处理

### Q: 出现 "Failed to fetch" 错误？

**A**: 
1. 检查后端是否运行（http://localhost:3401/api/health）
2. 检查端口是否被占用
3. 检查防火墙设置
4. 确认 CORS 配置正确

---

### Q: 出现 "Node not found" 错误？

**A**: 
1. 节点 ID 可能不存在
2. 检查拼写是否正确
3. 使用搜索功能查找正确的节点 ID
4. 刷新页面重新加载数据

---

### Q: 出现 "Service Unavailable" 错误？

**A**: 
1. 后端服务未初始化
2. 检查后端日志
3. 确认数据文件存在（`expr/example/`）
4. 重启后端服务

---

### Q: 导出失败怎么办？

**A**: 
1. 检查浏览器是否阻止下载
2. 尝试不同的导出格式
3. 减小导出分辨率
4. 检查浏览器控制台错误

---

## 开发问题

### Q: 如何贡献代码？

**A**: 
1. Fork 项目仓库
2. 创建功能分支
3. 提交 Pull Request
4. 参考 [贡献指南](./CONTRIBUTING.md)

---

### Q: 如何添加新功能？

**A**: 
1. 后端：在 `api/routes/` 添加新端点
2. 前端：在 `web_ui/src/components/` 添加新组件
3. 参考 [架构文档](./ARCHITECTURE.md)
4. 编写测试

---

### Q: 如何调试？

**A**: 
- 后端：启用 DEBUG 日志
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```
- 前端：使用浏览器 DevTools（F12）
- 查看网络请求和控制台错误

---

### Q: 如何运行测试？

**A**: 
```bash
# 后端测试
pytest tests/

# 前端测试
cd web_ui
pnpm test

# E2E 测试
pnpm test:e2e
```

---

## 部署问题

### Q: 如何部署到生产环境？

**A**: 
1. 使用 Docker Compose（推荐）：
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```
2. 或手动部署：
   - 后端：使用 Gunicorn + Nginx
   - 前端：构建静态文件 + Nginx

详见 [部署文档](./DEPLOYMENT.md)

---

### Q: 如何配置 HTTPS？

**A**: 
1. 获取 SSL 证书（Let's Encrypt）
2. 配置 Nginx：
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       ...
   }
   ```
3. 更新前端 API 地址为 HTTPS

---

### Q: 如何扩展到多用户？

**A**: 
1. 添加用户认证（JWT）
2. 使用数据库存储用户数据
3. 实现会话管理
4. 配置负载均衡

---

### Q: 如何监控系统状态？

**A**: 
1. 使用 `/api/health` 端点
2. 配置日志收集（ELK Stack）
3. 使用 Prometheus + Grafana 监控
4. 设置告警规则

---

## 其他问题

### Q: 有示例数据吗？

**A**: 有，在 `expr/example/` 目录：
- 医疗领域示例数据
- 包含疾病、症状、治疗等实体
- 可以直接使用

---

### Q: 支持哪些图布局算法？

**A**: 当前支持：
- 力导向布局（Force-directed）
- 可以扩展支持：
  - 层次布局（Hierarchical）
  - 圆形布局（Circular）
  - 网格布局（Grid）

---

### Q: 可以自定义样式吗？

**A**: 可以，在设置面板中：
- 节点颜色、大小、形状
- 边颜色、宽度、样式
- 标签字体、大小
- 布局参数

或通过 CSS 自定义（开发者）。

---

### Q: 有 API 文档吗？

**A**: 有，访问：
- Swagger UI: http://localhost:3401/docs
- ReDoc: http://localhost:3401/redoc
- Markdown: [API 文档](../api/README.md)

---

### Q: 如何获取帮助？

**A**: 
- 📖 阅读文档：[快速开始](./QUICKSTART.md)、[教程](./TUTORIAL.md)
- 🐛 提交 Issue 到 GitHub
- 💬 加入社区讨论
- 📧 联系技术支持

---

## 更新日志

### Q: 如何查看更新日志？

**A**: 查看 `CHANGELOG.md` 文件或 GitHub Releases。

---

### Q: 如何更新到最新版本？

**A**: 
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt
cd web_ui && pnpm install

# 重启服务
docker-compose restart
```

---

## 还有问题？

如果您的问题没有在这里找到答案：

1. 📖 查看完整文档
2. 🔍 搜索 GitHub Issues
3. 💬 在社区提问
4. 📧 联系我们

我们会持续更新 FAQ，感谢您的反馈！

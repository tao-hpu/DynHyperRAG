# 贡献指南

感谢您对 HyperGraphRAG 可视化项目的关注！本指南将帮助您了解如何为项目做出贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题报告](#问题报告)
- [功能建议](#功能建议)

---

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 尊重不同的观点和经验
- 接受建设性的批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

---

## 如何贡献

### 贡献类型

您可以通过以下方式贡献：

1. **报告 Bug**：发现问题并提交 Issue
2. **建议功能**：提出新功能想法
3. **改进文档**：修正错误或添加说明
4. **编写代码**：修复 Bug 或实现新功能
5. **代码审查**：审查其他人的 Pull Request
6. **测试**：测试新功能并提供反馈

---

## 开发环境设置

### 前置要求

- Python 3.10+
- Node.js 18+
- pnpm 8+
- Git

### 克隆仓库

```bash
git clone https://github.com/your-org/HyperGraphRAG.git
cd HyperGraphRAG
```

### 设置后端

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY

# 运行测试
pytest tests/

# 启动开发服务器
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload
```

### 设置前端

```bash
cd web_ui

# 安装依赖（使用 pnpm）
pnpm install

# 运行测试
pnpm test

# 启动开发服务器
pnpm dev
```

### 验证设置

1. 后端：访问 http://localhost:3401/docs
2. 前端：访问 http://localhost:3400
3. 运行测试：`pytest tests/` 和 `pnpm test`

---

## 代码规范

### Python 代码规范

#### 格式化

使用 Black 格式化代码：

```bash
pip install black
black api/ tests/
```

#### 类型注解

使用 Type Hints：

```python
def get_nodes(limit: int, offset: int) -> List[Node]:
    """获取节点列表"""
    pass
```

#### Docstrings

使用 Google 风格的 Docstrings：

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    函数的简短描述
    
    详细描述函数的功能和用途。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值的描述
    
    Raises:
        ValueError: 什么情况下抛出此异常
    """
    pass
```

#### 命名规范

- 类名：`PascalCase`
- 函数/变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：`_leading_underscore`

#### 示例

```python
from typing import List, Optional
from pydantic import BaseModel

class GraphNode(BaseModel):
    """图节点模型"""
    id: str
    label: str
    type: str

async def get_nodes(
    limit: int = 100,
    offset: int = 0,
    entity_type: Optional[str] = None
) -> List[GraphNode]:
    """
    获取图节点列表
    
    Args:
        limit: 返回的最大节点数
        offset: 分页偏移量
        entity_type: 可选的实体类型过滤
    
    Returns:
        节点列表
    """
    # 实现逻辑
    pass
```

### TypeScript 代码规范

#### 格式化

使用 Prettier：

```bash
pnpm format
```

#### ESLint

遵循 ESLint 规则：

```bash
pnpm lint
```

#### 类型定义

避免使用 `any`：

```typescript
// ❌ 不好
function process(data: any) {
  return data.value;
}

// ✅ 好
interface Data {
  value: string;
}

function process(data: Data): string {
  return data.value;
}
```

#### 组件规范

使用函数式组件 + Hooks：

```typescript
import React, { useState, useEffect } from 'react';

interface Props {
  title: string;
  onClose: () => void;
}

export const MyComponent: React.FC<Props> = ({ title, onClose }) => {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    // 副作用逻辑
  }, []);
  
  return (
    <div>
      <h1>{title}</h1>
      <button onClick={onClose}>Close</button>
    </div>
  );
};
```

#### 命名规范

- 组件：`PascalCase`
- 函数/变量：`camelCase`
- 常量：`UPPER_SNAKE_CASE`
- 类型/接口：`PascalCase`

---

## 提交规范

### Conventional Commits

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具配置

### Scope 范围

- `api`: 后端 API
- `ui`: 前端 UI
- `graph`: 图可视化
- `query`: 查询功能
- `docs`: 文档
- `test`: 测试

### 示例

```bash
# 新功能
git commit -m "feat(graph): add node search functionality"

# Bug 修复
git commit -m "fix(api): resolve CORS issue for production"

# 文档更新
git commit -m "docs: update API documentation"

# 重构
git commit -m "refactor(ui): simplify GraphCanvas component"
```

### 详细提交

```bash
git commit -m "feat(query): add query history feature

- Add QueryHistory component
- Implement history storage in queryStore
- Add API endpoint for history retrieval
- Update UI to display recent queries

Closes #123"
```

---

## Pull Request 流程

### 1. Fork 仓库

点击 GitHub 页面右上角的 "Fork" 按钮。

### 2. 克隆 Fork

```bash
git clone https://github.com/your-username/HyperGraphRAG.git
cd HyperGraphRAG
```

### 3. 添加上游仓库

```bash
git remote add upstream https://github.com/original-org/HyperGraphRAG.git
```

### 4. 创建功能分支

```bash
git checkout -b feature/my-new-feature
```

### 5. 进行更改

- 编写代码
- 添加测试
- 更新文档

### 6. 运行测试

```bash
# 后端测试
pytest tests/

# 前端测试
cd web_ui
pnpm test
```

### 7. 提交更改

```bash
git add .
git commit -m "feat: add my new feature"
```

### 8. 同步上游

```bash
git fetch upstream
git rebase upstream/main
```

### 9. 推送分支

```bash
git push origin feature/my-new-feature
```

### 10. 创建 Pull Request

1. 访问您的 Fork 页面
2. 点击 "New Pull Request"
3. 填写 PR 描述
4. 提交 PR

### PR 描述模板

```markdown
## 描述

简要描述此 PR 的目的和内容。

## 更改类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 其他

## 相关 Issue

Closes #123

## 测试

描述如何测试这些更改：

1. 步骤 1
2. 步骤 2
3. 预期结果

## 截图（如适用）

添加截图展示 UI 更改。

## 检查清单

- [ ] 代码遵循项目规范
- [ ] 已添加/更新测试
- [ ] 所有测试通过
- [ ] 已更新文档
- [ ] 提交信息遵循规范
```

### PR 审查流程

1. **自动检查**：CI/CD 运行测试
2. **代码审查**：维护者审查代码
3. **反馈**：根据反馈进行修改
4. **批准**：获得批准后合并
5. **合并**：维护者合并 PR

---

## 问题报告

### 报告 Bug

使用 GitHub Issues 报告 Bug，包含以下信息：

#### Bug 报告模板

```markdown
## Bug 描述

清晰简洁地描述 Bug。

## 复现步骤

1. 访问 '...'
2. 点击 '...'
3. 滚动到 '...'
4. 看到错误

## 预期行为

描述您期望发生什么。

## 实际行为

描述实际发生了什么。

## 截图

如果适用，添加截图帮助解释问题。

## 环境

- OS: [e.g. macOS 13.0]
- Browser: [e.g. Chrome 120]
- Version: [e.g. 1.0.0]

## 附加信息

添加任何其他相关信息。
```

### 报告前检查

- [ ] 搜索现有 Issues，确认未重复
- [ ] 使用最新版本
- [ ] 提供完整的复现步骤
- [ ] 包含错误日志或截图

---

## 功能建议

### 提出新功能

使用 GitHub Issues 提出功能建议：

#### 功能建议模板

```markdown
## 功能描述

清晰简洁地描述您想要的功能。

## 问题/需求

描述这个功能解决什么问题或满足什么需求。

## 建议的解决方案

描述您希望如何实现这个功能。

## 替代方案

描述您考虑过的其他解决方案。

## 附加信息

添加任何其他相关信息、截图或示例。
```

### 功能讨论

1. 提交 Issue
2. 等待社区讨论
3. 获得维护者批准
4. 开始实现

---

## 开发工作流

### 日常开发

```bash
# 1. 同步主分支
git checkout main
git pull upstream main

# 2. 创建功能分支
git checkout -b feature/new-feature

# 3. 开发和测试
# ... 编写代码 ...
pytest tests/
pnpm test

# 4. 提交更改
git add .
git commit -m "feat: add new feature"

# 5. 推送并创建 PR
git push origin feature/new-feature
```

### 代码审查

作为审查者：

1. **检查代码质量**：
   - 是否遵循代码规范
   - 是否有适当的注释
   - 是否有潜在的 Bug

2. **检查测试**：
   - 是否有足够的测试覆盖
   - 测试是否通过

3. **检查文档**：
   - 是否更新了相关文档
   - API 文档是否完整

4. **提供反馈**：
   - 具体、建设性的反馈
   - 建议改进方案

---

## 测试指南

### 编写测试

#### 后端测试

```python
# tests/test_graph_service.py
import pytest
from api.services.graph_service import GraphService

@pytest.mark.asyncio
async def test_get_nodes():
    """测试获取节点功能"""
    service = GraphService()
    await service.initialize()
    
    nodes = await service.get_nodes(limit=10, offset=0)
    
    assert len(nodes) <= 10
    assert all(hasattr(node, 'id') for node in nodes)
```

#### 前端测试

```typescript
// tests/components/SearchBar.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchBar } from '@/components/SearchBar';

test('search input works correctly', () => {
  const onSearch = jest.fn();
  render(<SearchBar onSearch={onSearch} />);
  
  const input = screen.getByPlaceholderText('Search');
  fireEvent.change(input, { target: { value: 'test' } });
  
  expect(onSearch).toHaveBeenCalledWith('test');
});
```

### 运行测试

```bash
# 后端
pytest tests/ -v
pytest tests/ --cov=api  # 带覆盖率

# 前端
pnpm test
pnpm test:coverage
```

---

## 文档贡献

### 文档类型

- **用户文档**：面向最终用户
- **API 文档**：API 参考
- **开发者文档**：架构和贡献指南
- **教程**：分步指南

### 文档规范

- 使用 Markdown 格式
- 包含代码示例
- 添加截图（如适用）
- 保持简洁清晰

### 更新文档

```bash
# 编辑文档
vim docs/visualization/QUICKSTART.md

# 提交更改
git add docs/
git commit -m "docs: update quickstart guide"
git push origin docs/update-quickstart
```

---

## 发布流程

### 版本号规范

使用语义化版本（Semantic Versioning）：

- **主版本号**：不兼容的 API 更改
- **次版本号**：向后兼容的功能添加
- **修订号**：向后兼容的 Bug 修复

示例：`1.2.3`

### 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
- [ ] 版本号已更新
- [ ] 创建 Git 标签
- [ ] 发布 Release Notes

---

## 获取帮助

### 资源

- **文档**：查看 `docs/` 目录
- **Issues**：搜索现有问题
- **Discussions**：参与社区讨论

### 联系方式

- GitHub Issues
- 开发者邮件列表
- 社区论坛

---

## 致谢

感谢所有贡献者！您的贡献让这个项目变得更好。

### 贡献者名单

查看 [CONTRIBUTORS.md](./CONTRIBUTORS.md) 了解所有贡献者。

---

**感谢您的贡献！** 🎉

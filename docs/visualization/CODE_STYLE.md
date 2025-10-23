# 代码风格指南

本文档定义了 HyperGraphRAG 可视化项目的代码风格规范。

## Python 代码风格

### 基本规范

遵循 [PEP 8](https://pep8.org/) 和 [PEP 257](https://pep257.readthedocs.io/)。

### 格式化工具

使用 **Black** 自动格式化：

```bash
pip install black
black api/ tests/
```

配置（`pyproject.toml`）：
```toml
[tool.black]
line-length = 88
target-version = ['py310']
```

### 导入顺序

```python
# 1. 标准库
import os
import sys
from typing import List, Optional

# 2. 第三方库
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import networkx as nx

# 3. 本地模块
from api.models.graph import Node, Edge
from api.services.graph_service import GraphService
```

### 类型注解

**必须**使用类型注解：

```python
from typing import List, Optional, Dict, Any

def get_nodes(
    limit: int,
    offset: int = 0,
    entity_type: Optional[str] = None
) -> List[Node]:
    """获取节点列表"""
    pass

async def process_data(data: Dict[str, Any]) -> None:
    """处理数据"""
    pass
```

### Docstrings

使用 Google 风格：

```python
def complex_function(param1: str, param2: int, param3: Optional[float] = None) -> dict:
    """
    函数的简短描述（一行）
    
    详细描述函数的功能、用途和注意事项。
    可以多行。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        param3: 可选参数的描述。默认为 None
    
    Returns:
        返回值的描述。如果返回复杂对象，详细说明结构：
        {
            'key1': 'value1',
            'key2': 123
        }
    
    Raises:
        ValueError: 当 param2 < 0 时抛出
        HTTPException: 当 API 调用失败时抛出
    
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'key1': 'test', 'key2': 42}
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    
    return {'key1': param1, 'key2': param2}
```

### 命名规范

```python
# 类名：PascalCase
class GraphService:
    pass

class NodeModel:
    pass

# 函数和变量：snake_case
def get_node_by_id(node_id: str) -> Node:
    pass

user_name = "John"
node_count = 100

# 常量：UPPER_SNAKE_CASE
MAX_NODES = 10000
DEFAULT_LIMIT = 100
API_VERSION = "1.0.0"

# 私有成员：前导下划线
class MyClass:
    def __init__(self):
        self._private_var = 42
    
    def _private_method(self):
        pass
```

### 异步函数

```python
# 使用 async/await
async def fetch_data() -> dict:
    """异步获取数据"""
    result = await some_async_operation()
    return result

# 异步上下文管理器
async with aiofiles.open('file.txt', 'r') as f:
    content = await f.read()
```

### 错误处理

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def get_node(node_id: str) -> Node:
    """获取节点"""
    try:
        node = await graph_service.get_node_by_id(node_id)
        if node is None:
            raise HTTPException(
                status_code=404,
                detail=f"Node {node_id} not found"
            )
        return node
    except ValueError as e:
        logger.error(f"Invalid node_id: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## TypeScript 代码风格

### 基本规范

遵循 [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)。

### 格式化工具

使用 **Prettier**：

```bash
pnpm format
```

配置（`.prettierrc`）：
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

### ESLint

```bash
pnpm lint
```

配置（`.eslintrc.js`）：
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-script/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
  },
};
```

### 类型定义

**避免使用 `any`**：

```typescript
// ❌ 不好
function process(data: any) {
  return data.value;
}

// ✅ 好
interface Data {
  value: string;
  count: number;
}

function process(data: Data): string {
  return data.value;
}

// 使用泛型
function getFirst<T>(items: T[]): T | undefined {
  return items[0];
}
```

### 接口 vs 类型

优先使用 `interface`，除非需要联合类型或其他高级特性：

```typescript
// ✅ 使用 interface
interface Node {
  id: string;
  label: string;
  type: string;
}

// ✅ 使用 type（联合类型）
type QueryMode = 'local' | 'global' | 'hybrid' | 'naive';

// ✅ 使用 type（交叉类型）
type NodeWithScore = Node & { score: number };
```

### React 组件

使用函数式组件 + Hooks：

```typescript
import React, { useState, useEffect, useCallback } from 'react';

interface Props {
  title: string;
  initialCount?: number;
  onCountChange?: (count: number) => void;
}

export const Counter: React.FC<Props> = ({ 
  title, 
  initialCount = 0,
  onCountChange 
}) => {
  const [count, setCount] = useState(initialCount);
  
  useEffect(() => {
    // 副作用逻辑
    console.log(`Count changed: ${count}`);
  }, [count]);
  
  const handleIncrement = useCallback(() => {
    setCount(prev => {
      const newCount = prev + 1;
      onCountChange?.(newCount);
      return newCount;
    });
  }, [onCountChange]);
  
  return (
    <div className="counter">
      <h2>{title}</h2>
      <p>Count: {count}</p>
      <button onClick={handleIncrement}>Increment</button>
    </div>
  );
};
```

### 命名规范

```typescript
// 组件：PascalCase
const GraphCanvas: React.FC = () => { };
const SearchBar: React.FC = () => { };

// 函数和变量：camelCase
const getUserName = () => { };
const nodeCount = 100;

// 常量：UPPER_SNAKE_CASE
const MAX_NODES = 10000;
const API_BASE_URL = 'http://localhost:3401';

// 类型和接口：PascalCase
interface NodeData { }
type QueryMode = 'local' | 'global';

// 私有成员：前导下划线（约定）
class MyClass {
  private _privateField: string;
  
  private _privateMethod(): void { }
}
```

### 异步操作

```typescript
// 使用 async/await
async function fetchNodes(): Promise<Node[]> {
  try {
    const response = await api.get<Node[]>('/graph/nodes');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch nodes:', error);
    throw error;
  }
}

// 在组件中
const MyComponent: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    const loadNodes = async () => {
      setLoading(true);
      try {
        const data = await fetchNodes();
        setNodes(data);
      } catch (error) {
        // 错误处理
      } finally {
        setLoading(false);
      }
    };
    
    loadNodes();
  }, []);
  
  return <div>{/* ... */}</div>;
};
```

### 错误处理

```typescript
// API 错误处理
import axios, { AxiosError } from 'axios';

async function fetchData(): Promise<Data> {
  try {
    const response = await api.get<Data>('/data');
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      if (axiosError.response) {
        // 服务器返回错误
        console.error('Server error:', axiosError.response.data.detail);
      } else if (axiosError.request) {
        // 请求发送但无响应
        console.error('Network error');
      }
    }
    throw error;
  }
}
```

---

## 通用规范

### 注释

```python
# Python
# 单行注释使用 #

"""
多行注释或文档字符串
使用三引号
"""

# TODO: 待办事项
# FIXME: 需要修复的问题
# NOTE: 重要说明
```

```typescript
// TypeScript
// 单行注释使用 //

/*
 * 多行注释
 * 使用斜杠星号
 */

// TODO: 待办事项
// FIXME: 需要修复的问题
// NOTE: 重要说明
```

### 文件组织

#### Python 文件

```python
"""
模块文档字符串
描述模块的用途
"""

# 导入
import os
from typing import List

# 常量
MAX_SIZE = 1000

# 类定义
class MyClass:
    pass

# 函数定义
def my_function():
    pass

# 主程序
if __name__ == "__main__":
    main()
```

#### TypeScript 文件

```typescript
/**
 * 文件文档注释
 * 描述文件的用途
 */

// 导入
import React from 'react';
import { Node } from '@/types/graph';

// 类型定义
interface Props {
  // ...
}

// 常量
const MAX_SIZE = 1000;

// 组件定义
export const MyComponent: React.FC<Props> = (props) => {
  // ...
};

// 导出
export default MyComponent;
```

### 代码长度

- **行长度**：
  - Python: 88 字符（Black 默认）
  - TypeScript: 100 字符（Prettier 配置）

- **函数长度**：
  - 尽量保持在 50 行以内
  - 超过 100 行考虑拆分

- **文件长度**：
  - 尽量保持在 500 行以内
  - 超过 1000 行考虑拆分

### 空行

```python
# Python
import os  # 导入后空一行

MAX_SIZE = 1000  # 常量后空一行


class MyClass:  # 类定义前空两行
    def method1(self):  # 方法间空一行
        pass
    
    def method2(self):
        pass


def function1():  # 函数定义前空两行
    pass


def function2():
    pass
```

```typescript
// TypeScript
import React from 'react';  // 导入后空一行

const MAX_SIZE = 1000;  // 常量后空一行

export const Component1: React.FC = () => {  // 组件间空一行
  return <div />;
};

export const Component2: React.FC = () => {
  return <div />;
};
```

---

## Git 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建/工具

### 示例

```bash
feat(graph): add node search functionality

- Implement semantic search using vector similarity
- Add search bar component
- Update GraphService with search method

Closes #123
```

---

## 最佳实践

### DRY (Don't Repeat Yourself)

```python
# ❌ 不好
def get_user_name(user_id):
    user = db.get_user(user_id)
    return user.name

def get_user_email(user_id):
    user = db.get_user(user_id)
    return user.email

# ✅ 好
def get_user(user_id):
    return db.get_user(user_id)

def get_user_name(user_id):
    return get_user(user_id).name

def get_user_email(user_id):
    return get_user(user_id).email
```

### KISS (Keep It Simple, Stupid)

```typescript
// ❌ 不好（过度复杂）
const isValid = (value: string): boolean => {
  return value !== null && value !== undefined && value.length > 0 && value.trim() !== '';
};

// ✅ 好（简单明了）
const isValid = (value: string): boolean => {
  return value?.trim().length > 0;
};
```

### YAGNI (You Aren't Gonna Need It)

不要实现当前不需要的功能。

### 单一职责原则

每个函数/类只做一件事。

```python
# ❌ 不好
def process_and_save_data(data):
    # 处理数据
    processed = transform(data)
    # 验证数据
    if not validate(processed):
        raise ValueError()
    # 保存数据
    db.save(processed)
    # 发送通知
    send_notification()

# ✅ 好
def process_data(data):
    return transform(data)

def validate_data(data):
    if not validate(data):
        raise ValueError()

def save_data(data):
    db.save(data)

def send_notification():
    # ...
```

---

## 工具配置

### VS Code 设置

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### 推荐扩展

- Python: `ms-python.python`
- Black Formatter: `ms-python.black-formatter`
- ESLint: `dbaeumer.vscode-eslint`
- Prettier: `esbenp.prettier-vscode`
- TypeScript: 内置

---

## 检查清单

提交代码前检查：

- [ ] 代码遵循风格指南
- [ ] 添加了必要的注释
- [ ] 添加了类型注解（Python）或类型定义（TypeScript）
- [ ] 编写了测试
- [ ] 所有测试通过
- [ ] 运行了格式化工具
- [ ] 运行了 Linter
- [ ] 更新了文档
- [ ] Commit message 遵循规范

---

## 参考资源

- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

---

**保持代码整洁，让协作更愉快！** ✨

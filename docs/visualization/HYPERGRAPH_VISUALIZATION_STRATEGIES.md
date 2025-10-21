# 超图可视化策略

## 问题背景

HyperGraphRAG 使用**二部图（Bipartite Graph）**结构存储超图：
- **实体节点（Entity）**：129 个
- **超边节点（Hyperedge）**：84 个  
- **连接**：实体 ↔ 超边 ↔ 实体（145 条边）

这种结构的特点：
- 实体之间没有直接连接
- 所有连接都通过超边节点中转
- 一个超边可以连接 2+ 个实体（n 元关系）

## 可视化策略对比

### 策略 1：二部图直接可视化 ⭐ 最准确

**原理**：直接显示实体节点和超边节点

```
[Entity A] ──┐
             ├── [Hyperedge: "A and B are related"]
[Entity B] ──┘
```

**优点**：
- ✅ 完全保留原始图结构
- ✅ 超边作为独立节点，可以显示详细信息
- ✅ 适合理解超图的真实结构

**缺点**：
- ❌ 视觉复杂度高（节点数翻倍）
- ❌ 不符合用户对"关系图"的直觉
- ❌ 超边节点的标签通常很长（如 `<hyperedge>"The ESC's funding..."`）

**实现**：
```python
# 返回所有节点（实体 + 超边）
nodes = [
    {"id": "Entity A", "type": "entity"},
    {"id": "Entity B", "type": "entity"},
    {"id": "hyperedge-1", "type": "hyperedge", "label": "A and B are related"}
]
edges = [
    {"source": "Entity A", "target": "hyperedge-1"},
    {"source": "Entity B", "target": "hyperedge-1"}
]
```

---

### 策略 2：转换为普通图（当前实现）⭐ 最直观

**原理**：将 Entity-Hyperedge-Entity 路径转换为 Entity-Entity 边

```
[Entity A] ────── [Entity B]
         (via: "A and B are related")
```

**优点**：
- ✅ 符合用户直觉（传统关系图）
- ✅ 视觉简洁，易于理解
- ✅ 节点数量减半

**缺点**：
- ❌ 丢失了超边的独立性
- ❌ 对于 3+ 实体的超边，需要创建多条边（组合爆炸）
  - 例如：3 个实体 → 3 条边，4 个实体 → 6 条边
- ❌ 超边信息只能作为边的属性显示

**实现**（当前代码）：
```python
# 对每个超边，创建所有实体对之间的边
for hyperedge in hyperedges:
    entities = get_connected_entities(hyperedge)
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            edges.append({
                "source": entities[i],
                "target": entities[j],
                "description": hyperedge.label,
                "isHyperedge": len(entities) >= 3
            })
```

---

### 策略 3：混合模式（推荐）⭐⭐⭐ 最灵活

**原理**：提供两种视图模式，用户可切换

**模式 A - 简化视图**（默认）：
- 显示实体节点
- 边表示超边连接
- 适合快速浏览

**模式 B - 完整视图**：
- 显示实体 + 超边节点
- 完整的二部图结构
- 适合深入分析

**实现**：
```typescript
// 前端组件
<GraphCanvas 
  data={graphData}
  viewMode={viewMode}  // "simplified" | "full"
  onViewModeChange={setViewMode}
/>
```

---

### 策略 4：超边作为复合节点 ⭐⭐ 最美观

**原理**：使用 Cytoscape.js 的复合节点（Compound Nodes）功能

```
┌─────────────────────────────┐
│  Hyperedge Container        │
│  ┌─────┐  ┌─────┐  ┌─────┐ │
│  │  A  │  │  B  │  │  C  │ │
│  └─────┘  └─────┘  └─────┘ │
└─────────────────────────────┘
```

**优点**：
- ✅ 视觉上清晰表达"多个实体属于同一个超边"
- ✅ 可以折叠/展开超边
- ✅ 保留超边的独立性

**缺点**：
- ❌ 实现复杂度高
- ❌ 布局算法需要特殊处理
- ❌ 不适合大规模图

**实现**：
```javascript
cy.add([
  // 超边作为父节点
  { data: { id: 'hyperedge-1', label: 'Relation' } },
  // 实体作为子节点
  { data: { id: 'A', parent: 'hyperedge-1' } },
  { data: { id: 'B', parent: 'hyperedge-1' } },
  { data: { id: 'C', parent: 'hyperedge-1' } }
]);
```

---

### 策略 5：超边作为标签/注释

**原理**：只显示实体节点，超边信息作为边的标签或悬浮提示

```
[Entity A] ──────────── [Entity B]
              ↑
         "A and B are related"
```

**优点**：
- ✅ 最简洁
- ✅ 适合关系简单的场景

**缺点**：
- ❌ 完全丢失超边的结构信息
- ❌ 不适合复杂超边

---

## 推荐方案

### 短期（当前实现）：策略 2 - 转换为普通图

**理由**：
1. 实现简单，快速上线
2. 符合大多数用户的直觉
3. 对于当前数据规模（129 实体，84 超边）足够用

**优化建议**：
- 在边的详情面板中显示完整的超边信息
- 用不同颜色/样式区分普通边和超边（3+ 实体）
- 提供"查看原始超边"的功能

### 中期：策略 3 - 混合模式

**实现步骤**：
1. 保留当前的简化视图
2. 添加"完整视图"模式，显示二部图
3. 提供视图切换按钮

**代码示例**：
```typescript
// 后端 API 添加参数
GET /api/graph/edges?view_mode=simplified  // 返回 entity-entity 边
GET /api/graph/edges?view_mode=full        // 返回完整二部图

// 前端组件
const [viewMode, setViewMode] = useState<'simplified' | 'full'>('simplified');

<ToggleButton 
  value={viewMode}
  onChange={setViewMode}
  options={[
    { value: 'simplified', label: 'Simplified View' },
    { value: 'full', label: 'Full Bipartite Graph' }
  ]}
/>
```

### 长期：策略 4 - 复合节点

**适用场景**：
- 用户需要深入分析超边结构
- 数据规模可控（< 1000 节点）
- 有足够的开发资源

---

## 当前实现的问题和解决方案

### 问题 1：组合爆炸

**场景**：一个超边连接 10 个实体
- 需要创建 C(10,2) = 45 条边
- 视觉上非常混乱

**解决方案**：
```python
# 限制每个超边生成的边数
MAX_EDGES_PER_HYPEREDGE = 10

if len(entities) > 5:  # 超过 5 个实体
    # 只创建星形连接（以第一个实体为中心）
    center = entities[0]
    for entity in entities[1:]:
        edges.append(create_edge(center, entity, hyperedge))
else:
    # 创建完全连接
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            edges.append(create_edge(entities[i], entities[j], hyperedge))
```

### 问题 2：超边信息丢失

**解决方案**：
- 在边的 `description` 字段保存完整的超边标签
- 在边的 `entities` 字段保存所有连接的实体
- 点击边时，在详情面板显示完整信息

### 问题 3：无法区分超边和普通边

**解决方案**：
```typescript
// 前端样式
{
  selector: 'edge[isHyperedge="true"]',
  style: {
    'line-color': '#f59e0b',      // 橙色
    'line-style': 'dashed',        // 虚线
    'width': 3,                    // 更粗
    'target-arrow-shape': 'none'   // 无箭头（无向）
  }
}
```

---

## 数据示例

### 原始二部图数据

```json
{
  "nodes": [
    {"id": "HYPERTENSION", "role": "entity", "type": "DISEASE"},
    {"id": "BLOOD PRESSURE", "role": "entity", "type": "MEASUREMENT"},
    {"id": "CARDIOVASCULAR RISK", "role": "entity", "type": "CONCEPT"},
    {
      "id": "<hyperedge>\"Hypertension increases cardiovascular risk through elevated blood pressure\"",
      "role": "hyperedge",
      "weight": 15.0
    }
  ],
  "edges": [
    {"source": "HYPERTENSION", "target": "<hyperedge>..."},
    {"source": "BLOOD PRESSURE", "target": "<hyperedge>..."},
    {"source": "CARDIOVASCULAR RISK", "target": "<hyperedge>..."}
  ]
}
```

### 转换后的简化数据（当前实现）

```json
{
  "nodes": [
    {"id": "HYPERTENSION", "type": "DISEASE"},
    {"id": "BLOOD PRESSURE", "type": "MEASUREMENT"},
    {"id": "CARDIOVASCULAR RISK", "type": "CONCEPT"}
  ],
  "edges": [
    {
      "source": "HYPERTENSION",
      "target": "BLOOD PRESSURE",
      "description": "Hypertension increases cardiovascular risk through elevated blood pressure",
      "weight": 15.0,
      "entities": ["HYPERTENSION", "BLOOD PRESSURE", "CARDIOVASCULAR RISK"],
      "isHyperedge": true
    },
    {
      "source": "HYPERTENSION",
      "target": "CARDIOVASCULAR RISK",
      "description": "Hypertension increases cardiovascular risk through elevated blood pressure",
      "weight": 15.0,
      "entities": ["HYPERTENSION", "BLOOD PRESSURE", "CARDIOVASCULAR RISK"],
      "isHyperedge": true
    },
    {
      "source": "BLOOD PRESSURE",
      "target": "CARDIOVASCULAR RISK",
      "description": "Hypertension increases cardiovascular risk through elevated blood pressure",
      "weight": 15.0,
      "entities": ["HYPERTENSION", "BLOOD PRESSURE", "CARDIOVASCULAR RISK"],
      "isHyperedge": true
    }
  ]
}
```

---

## 总结

当前实现（策略 2）是一个**实用的折中方案**：
- ✅ 快速实现，满足基本需求
- ✅ 用户体验好，符合直觉
- ⚠️ 需要注意组合爆炸问题
- ⚠️ 需要在 UI 上清晰标识超边

建议后续迭代时考虑**混合模式**（策略 3），给用户更多选择。

# G6 二部图到超边的转换方案

## 问题

我们的数据是**二部图**结构：
```
Entity A ──┐
           ├── Hyperedge Node
Entity B ──┤
           │
Entity C ──┘
```

G6 的 Combo 功能期望的输入是：
```javascript
{
  nodes: [
    { id: 'A', comboId: 'hyperedge-1' },
    { id: 'B', comboId: 'hyperedge-1' },
    { id: 'C', comboId: 'hyperedge-1' }
  ],
  combos: [
    { id: 'hyperedge-1', label: 'Hyperedge' }
  ]
}
```

## G6 能否直接处理二部图？

### 答案：不能直接处理，但可以轻松转换

G6 的 Combo 功能**不支持**二部图输入，需要我们在前端或后端进行转换。

## 转换方案

### 方案 A：后端转换（推荐）⭐⭐⭐⭐⭐

**优点**：
- ✅ 前端代码简洁
- ✅ 可以复用转换逻辑
- ✅ 减少前端数据处理

**实现**：

```python
# api/services/graph_service.py

async def get_graph_data_for_g6(
    self,
    limit: int = 500
) -> dict:
    """
    获取适配 G6 Combo 的图数据
    
    将二部图转换为 G6 的 Combo 格式：
    - Entity 节点 -> nodes (带 comboId)
    - Hyperedge 节点 -> combos
    - Entity-Hyperedge 边 -> 忽略（由 Combo 表示）
    """
    from api.models.graph import Node
    
    graph = self.rag.chunk_entity_relation_graph._graph
    
    # 1. 获取所有实体节点
    entity_nodes = []
    for node_id, data in graph.nodes(data=True):
        if data.get("role") != "entity":
            continue
        
        entity_type_raw = data.get("entity_type", "")
        entity_type_clean = entity_type_raw.strip('"') if entity_type_raw else "unknown"
        
        entity_nodes.append({
            "id": node_id,
            "label": node_id.strip('"'),
            "type": entity_type_clean,
            "description": data.get("description", "").strip('"'),
            "weight": float(data.get("weight", 1.0)),
            "comboId": None,  # 稍后填充
        })
    
    # 2. 获取所有超边节点并转换为 Combo
    combos = []
    entity_to_combos = {}  # 记录每个实体属于哪些 combo
    
    for node_id, data in graph.nodes(data=True):
        if data.get("role") != "hyperedge":
            continue
        
        # 获取超边连接的所有实体
        entity_neighbors = [
            n for n in graph.neighbors(node_id)
            if graph.nodes[n].get("role") == "entity"
        ]
        
        if len(entity_neighbors) < 2:
            continue
        
        hyperedge_weight = float(data.get("weight", 1.0))
        hyperedge_label = node_id.strip('"').strip('<hyperedge>')
        
        # 创建 Combo
        combo_id = f"combo-{node_id}"
        combos.append({
            "id": combo_id,
            "label": hyperedge_label[:50] + "..." if len(hyperedge_label) > 50 else hyperedge_label,
            "description": hyperedge_label,
            "weight": hyperedge_weight,
            "entityCount": len(entity_neighbors),
        })
        
        # 记录实体-Combo 关系
        for entity_id in entity_neighbors:
            if entity_id not in entity_to_combos:
                entity_to_combos[entity_id] = []
            entity_to_combos[entity_id].append(combo_id)
    
    # 3. 处理实体的 comboId
    # 问题：一个实体可能属于多个超边
    # 解决：只分配给第一个 combo，其他用边表示
    
    nodes_with_combo = []
    nodes_without_combo = []
    
    for node in entity_nodes:
        node_id = node["id"]
        if node_id in entity_to_combos and entity_to_combos[node_id]:
            # 分配给第一个 combo
            node["comboId"] = entity_to_combos[node_id][0]
            nodes_with_combo.append(node)
        else:
            nodes_without_combo.append(node)
    
    # 4. 创建跨 Combo 的边（实体属于多个超边时）
    edges = []
    for entity_id, combo_ids in entity_to_combos.items():
        if len(combo_ids) > 1:
            # 实体属于多个超边，创建边连接这些 combo
            for i in range(len(combo_ids)):
                for j in range(i + 1, len(combo_ids)):
                    edges.append({
                        "source": combo_ids[i],
                        "target": combo_ids[j],
                        "label": f"via {entity_id.strip('\"')}",
                        "style": {
                            "lineDash": [5, 5],
                            "stroke": "#f59e0b",
                        }
                    })
    
    return {
        "nodes": nodes_with_combo + nodes_without_combo,
        "edges": edges,
        "combos": combos,
    }
```

**API 路由**：

```python
# api/routes/graph.py

@router.get("/g6-data", response_model=dict)
async def get_g6_graph_data(
    limit: int = Query(500, le=1000)
):
    """
    获取适配 G6 Combo 的图数据
    
    返回格式：
    {
        "nodes": [...],     // 实体节点（带 comboId）
        "edges": [...],     // 跨 Combo 的边
        "combos": [...]     // 超边（作为 Combo）
    }
    """
    return await graph_service.get_graph_data_for_g6(limit)
```

---

### 方案 B：前端转换

**优点**：
- ✅ 后端无需改动
- ✅ 灵活性高

**缺点**：
- ❌ 前端代码复杂
- ❌ 性能开销

**实现**：

```typescript
// web_ui/src/utils/bipartiteToG6.ts

interface BipartiteGraph {
  nodes: Node[];
  edges: Edge[];
}

interface G6Graph {
  nodes: G6Node[];
  edges: G6Edge[];
  combos: G6Combo[];
}

export function convertBipartiteToG6(data: BipartiteGraph): G6Graph {
  const entityNodes: G6Node[] = [];
  const hyperedgeNodes = new Map<string, Node>();
  const entityToHyperedges = new Map<string, string[]>();
  
  // 1. 分离实体节点和超边节点
  data.nodes.forEach(node => {
    if (node.type === 'hyperedge') {
      hyperedgeNodes.set(node.id, node);
    } else {
      entityNodes.push({
        id: node.id,
        label: node.label,
        type: node.type,
        comboId: undefined,
      });
    }
  });
  
  // 2. 分析边，建立实体-超边关系
  data.edges.forEach(edge => {
    const sourceNode = data.nodes.find(n => n.id === edge.source);
    const targetNode = data.nodes.find(n => n.id === edge.target);
    
    let entityId: string;
    let hyperedgeId: string;
    
    if (sourceNode?.type === 'hyperedge') {
      hyperedgeId = edge.source;
      entityId = edge.target;
    } else if (targetNode?.type === 'hyperedge') {
      hyperedgeId = edge.target;
      entityId = edge.source;
    } else {
      return; // 跳过实体-实体边
    }
    
    if (!entityToHyperedges.has(entityId)) {
      entityToHyperedges.set(entityId, []);
    }
    entityToHyperedges.get(entityId)!.push(hyperedgeId);
  });
  
  // 3. 创建 Combos
  const combos: G6Combo[] = Array.from(hyperedgeNodes.entries()).map(([id, node]) => ({
    id: `combo-${id}`,
    label: node.label.substring(0, 50),
    description: node.description,
  }));
  
  // 4. 分配实体到 Combo
  entityNodes.forEach(node => {
    const hyperedges = entityToHyperedges.get(node.id);
    if (hyperedges && hyperedges.length > 0) {
      node.comboId = `combo-${hyperedges[0]}`;
    }
  });
  
  // 5. 创建跨 Combo 的边
  const crossComboEdges: G6Edge[] = [];
  entityToHyperedges.forEach((hyperedges, entityId) => {
    if (hyperedges.length > 1) {
      for (let i = 0; i < hyperedges.length; i++) {
        for (let j = i + 1; j < hyperedges.length; j++) {
          crossComboEdges.push({
            source: `combo-${hyperedges[i]}`,
            target: `combo-${hyperedges[j]}`,
            label: `via ${entityId}`,
            style: {
              lineDash: [5, 5],
              stroke: '#f59e0b',
            },
          });
        }
      }
    }
  });
  
  return {
    nodes: entityNodes,
    edges: crossComboEdges,
    combos,
  };
}
```

---

## 关键问题：一个实体属于多个超边

### 问题描述

在真实数据中，一个实体可能同时属于多个超边：

```
Hyperedge 1: [A, B, C]
Hyperedge 2: [A, D, E]
```

实体 A 同时属于两个超边。

### G6 的限制

G6 的 Combo 功能**不支持节点属于多个 Combo**。

### 解决方案

#### 方案 1：节点只属于一个 Combo（推荐）

```
┌─────────────────┐         ┌─────────────────┐
│  Hyperedge 1    │         │  Hyperedge 2    │
│  ┌───┐ ┌───┐   │         │  ┌───┐ ┌───┐   │
│  │ A │ │ B │   │ ─ ─ ─ ─ │  │ D │ │ E │   │
│  └───┘ └───┘   │  via A  │  └───┘ └───┘   │
│    ┌───┐       │         │                 │
│    │ C │       │         │                 │
│    └───┘       │         │                 │
└─────────────────┘         └─────────────────┘
```

- A 只属于 Hyperedge 1
- 用虚线边表示 A 也连接到 Hyperedge 2

#### 方案 2：复制节点

```
┌─────────────────┐         ┌─────────────────┐
│  Hyperedge 1    │         │  Hyperedge 2    │
│  ┌───┐ ┌───┐   │         │  ┌───┐ ┌───┐   │
│  │ A │ │ B │   │         │  │ A'│ │ D │   │
│  └───┘ └───┘   │         │  └───┘ └───┘   │
│    ┌───┐       │         │    ┌───┐       │
│    │ C │       │         │    │ E │       │
│    └───┘       │         │    └───┘       │
└─────────────────┘         └─────────────────┘
```

- 创建 A 的副本 A'
- 缺点：节点重复，不直观

#### 方案 3：使用 Hull 代替 Combo

```typescript
// 使用 Hull（轮廓包裹）代替 Combo
graph.on('afterlayout', () => {
  // Hyperedge 1
  graph.createHull({
    id: 'hull-1',
    members: ['A', 'B', 'C'],
    style: {
      fill: '#fef3c7',
      stroke: '#f59e0b',
    },
  });
  
  // Hyperedge 2
  graph.createHull({
    id: 'hull-2',
    members: ['A', 'D', 'E'],
    style: {
      fill: '#dbeafe',
      stroke: '#3b82f6',
    },
  });
});
```

**效果**：
```
    ╭─────────╮
   ╱ A   B    ╲╲
  │            │╲╲
   ╲    C     ╱  ╲╲
    ╰─────────╯   ╲╲
         ╭──────────╮
        ╱  D    E    ╲
       │              │
        ╲            ╱
         ╰──────────╯
```

- A 同时在两个 Hull 内
- 视觉上更清晰
- **推荐用于复杂超边场景**

---

## 最终推荐方案

### 对于 HyperGraphRAG 数据

**使用 Hull 而不是 Combo**

**理由**：
1. ✅ 支持节点属于多个超边
2. ✅ 视觉效果更好
3. ✅ 更灵活

**实现**：

```typescript
// web_ui/src/components/GraphCanvasG6.tsx

import G6 from '@antv/g6';

const graph = new G6.Graph({
  container: 'container',
  width: 800,
  height: 600,
  modes: {
    default: ['drag-node', 'zoom-canvas', 'drag-canvas'],
  },
});

// 加载数据
graph.data({
  nodes: entityNodes,
  edges: [], // 不需要边
});

graph.render();

// 布局完成后创建 Hull
graph.on('afterlayout', () => {
  hyperedges.forEach((hyperedge, index) => {
    graph.createHull({
      id: `hull-${hyperedge.id}`,
      members: hyperedge.entities,
      type: 'smooth-convex',
      style: {
        fill: colors[index % colors.length],
        stroke: strokeColors[index % strokeColors.length],
        opacity: 0.2,
        lineWidth: 2,
      },
      label: hyperedge.label,
      labelCfg: {
        position: 'top',
        style: {
          fontSize: 12,
          fill: strokeColors[index % strokeColors.length],
        },
      },
    });
  });
});
```

---

## 总结

### G6 能否直接处理二部图？

**答案**：❌ 不能直接处理

### 需要转换吗？

**答案**：✅ 需要，但很简单

### 推荐方案

1. **后端转换**：将二部图转换为实体节点 + 超边元数据
2. **前端使用 Hull**：用轮廓包裹表示超边
3. **支持重叠**：一个实体可以属于多个 Hull

### 优势

- ✅ 完美支持超边可视化
- ✅ 支持实体属于多个超边
- ✅ 视觉效果优秀
- ✅ 实现相对简单

### 下一步

要不要我实现一个 G6 + Hull 的原型？可以和当前的 Cytoscape 版本对比效果。

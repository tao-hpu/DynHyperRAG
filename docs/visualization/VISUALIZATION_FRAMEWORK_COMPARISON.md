# 图可视化框架选型分析

## 当前问题

Cytoscape.js 的局限性：
- ❌ 视觉效果较为基础
- ❌ 动画效果有限
- ❌ 自定义样式能力弱
- ❌ 对超边的原生支持不足
- ❌ 大规模图性能一般

## 候选方案对比

### 1. Cytoscape.js（当前）

**优点**：
- ✅ 专为图可视化设计
- ✅ 文档完善，社区活跃
- ✅ 开箱即用的布局算法
- ✅ 学习曲线平缓
- ✅ 支持复合节点（可用于超边）

**缺点**：
- ❌ 视觉效果较为朴素
- ❌ 动画和交互效果有限
- ❌ 自定义渲染能力弱
- ❌ 对超边没有原生支持

**适用场景**：
- 快速原型开发
- 中小规模图（< 1000 节点）
- 功能性优先于美观性

**评分**：⭐⭐⭐ (3/5)

---

### 2. D3.js

**优点**：
- ✅ 极强的自定义能力
- ✅ 丰富的动画效果
- ✅ 可以实现任何想要的视觉效果
- ✅ 社区庞大，示例丰富
- ✅ 可以完美实现超边可视化

**缺点**：
- ❌ 学习曲线陡峭
- ❌ 开发成本高（需要从零实现）
- ❌ 没有开箱即用的图布局
- ❌ 性能优化需要手动处理
- ❌ 代码量大，维护成本高

**适用场景**：
- 需要高度定制化的可视化
- 有充足的开发时间和资源
- 对视觉效果要求极高

**评分**：⭐⭐⭐⭐ (4/5) - 强大但复杂

---

### 3. AntV G6 ⭐⭐⭐⭐⭐ 推荐

**优点**：
- ✅ 专为图可视化设计（蚂蚁金服出品）
- ✅ 视觉效果现代化、美观
- ✅ 丰富的内置布局算法
- ✅ 强大的交互能力
- ✅ 性能优秀（支持 10,000+ 节点）
- ✅ 支持自定义节点/边渲染
- ✅ 完善的 TypeScript 支持
- ✅ 中文文档友好
- ✅ **原生支持超边（Combo/Hull）**

**缺点**：
- ⚠️ 学习曲线中等
- ⚠️ 需要重构现有代码

**超边支持**：
```typescript
// G6 原生支持 Combo（组合节点）
graph.addItem('combo', {
  id: 'hyperedge-1',
  label: 'Hyperedge',
  type: 'circle',
});

// 将节点添加到 Combo
graph.updateItem('node-a', { comboId: 'hyperedge-1' });
graph.updateItem('node-b', { comboId: 'hyperedge-1' });
graph.updateItem('node-c', { comboId: 'hyperedge-1' });
```

**适用场景**：
- 企业级图可视化应用
- 需要美观且功能强大的界面
- 中大规模图（1000-10000 节点）
- **超图可视化**（原生支持）

**评分**：⭐⭐⭐⭐⭐ (5/5)

---

### 4. Sigma.js

**优点**：
- ✅ 专注于大规模图（10,000+ 节点）
- ✅ 性能极佳（WebGL 渲染）
- ✅ 视觉效果现代化
- ✅ 轻量级

**缺点**：
- ❌ 功能相对简单
- ❌ 自定义能力有限
- ❌ 对超边支持不足
- ❌ 社区较小

**适用场景**：
- 超大规模图可视化
- 性能是首要考虑

**评分**：⭐⭐⭐⭐ (4/5) - 性能优先

---

### 5. Vis.js Network

**优点**：
- ✅ 简单易用
- ✅ 开箱即用
- ✅ 物理引擎效果好

**缺点**：
- ❌ 视觉效果一般
- ❌ 性能较差（> 500 节点卡顿）
- ❌ 自定义能力弱
- ❌ 项目维护不活跃

**适用场景**：
- 小规模图（< 100 节点）
- 快速 demo

**评分**：⭐⭐ (2/5)

---

### 6. Apache ECharts（关系图）

**优点**：
- ✅ 百度出品，文档完善
- ✅ 中文支持好
- ✅ 视觉效果不错
- ✅ 集成简单

**缺点**：
- ❌ 主要是图表库，图可视化是附加功能
- ❌ 图功能相对简单
- ❌ 对超边支持不足
- ❌ 大规模图性能一般

**适用场景**：
- 已经使用 ECharts 的项目
- 简单的关系图

**评分**：⭐⭐⭐ (3/5)

---

## 推荐方案：AntV G6

### 为什么选择 G6？

1. **原生超边支持**
   - Combo 功能完美适配超边场景
   - 可以将多个节点组合在一起
   - 视觉上清晰表达 n 元关系

2. **视觉效果现代化**
   - 内置多种精美主题
   - 流畅的动画效果
   - 支持自定义渲染

3. **性能优秀**
   - 支持 10,000+ 节点
   - WebGL 渲染模式
   - 虚拟化渲染

4. **开发体验好**
   - TypeScript 原生支持
   - 完善的 API 文档
   - 丰富的示例

5. **企业级支持**
   - 蚂蚁金服维护
   - 持续更新
   - 社区活跃

### G6 超边可视化方案

#### 方案 A：使用 Combo（推荐）

```typescript
import G6 from '@antv/g6';

const graph = new G6.Graph({
  container: 'container',
  width: 800,
  height: 600,
  modes: {
    default: ['drag-combo', 'drag-node', 'zoom-canvas'],
  },
  defaultCombo: {
    type: 'circle',
    style: {
      lineWidth: 2,
      stroke: '#f59e0b',
      fill: '#fef3c7',
      opacity: 0.3,
    },
    labelCfg: {
      position: 'top',
      style: {
        fontSize: 12,
        fill: '#f59e0b',
      },
    },
  },
});

// 添加数据
graph.data({
  nodes: [
    { id: 'A', label: 'Entity A', comboId: 'hyperedge-1' },
    { id: 'B', label: 'Entity B', comboId: 'hyperedge-1' },
    { id: 'C', label: 'Entity C', comboId: 'hyperedge-1' },
  ],
  combos: [
    { 
      id: 'hyperedge-1', 
      label: 'Hyperedge: A, B, C are related',
      type: 'circle',
    },
  ],
});

graph.render();
```

**效果**：
```
┌─────────────────────────────┐
│  Hyperedge Container        │
│  ┌─────┐  ┌─────┐  ┌─────┐ │
│  │  A  │  │  B  │  │  C  │ │
│  └─────┘  └─────┘  └─────┘ │
└─────────────────────────────┘
```

#### 方案 B：使用 Hull（轮廓包裹）

```typescript
graph.on('afterlayout', () => {
  graph.createHull({
    id: 'hyperedge-1',
    members: ['A', 'B', 'C'],
    type: 'smooth-convex',
    style: {
      fill: '#fef3c7',
      stroke: '#f59e0b',
      opacity: 0.3,
    },
    label: 'Hyperedge',
  });
});
```

**效果**：
```
    ╭─────────────╮
   ╱   A     B    ╲
  │                │
   ╲      C       ╱
    ╰─────────────╯
```

### 迁移成本评估

#### 工作量

- **前端重构**：2-3 天
  - 替换 Cytoscape.js 为 G6
  - 重新实现布局和交互
  - 调整样式和主题

- **后端调整**：0.5 天
  - 调整数据格式（添加 comboId）
  - 无需大改

- **测试和优化**：1 天

**总计**：3-4 天

#### 代码改动

**需要改动**：
- `web_ui/src/components/GraphCanvas.tsx` - 完全重写
- `web_ui/src/types/graph.ts` - 添加 Combo 类型
- `api/services/graph_service.py` - 调整返回格式

**不需要改动**：
- API 路由
- 数据加载逻辑
- 其他组件

### 实施建议

#### 短期（当前）

保持 Cytoscape.js，因为：
- ✅ 已经实现基本功能
- ✅ 可以快速迭代
- ✅ 满足 MVP 需求

#### 中期（1-2 周后）

迁移到 G6，因为：
- ✅ 更好的超边可视化
- ✅ 更美观的界面
- ✅ 更强的扩展性
- ✅ 更好的性能

#### 实施步骤

1. **创建 G6 分支**
   ```bash
   git checkout -b feature/g6-visualization
   ```

2. **安装依赖**
   ```bash
   cd web_ui
   pnpm add @antv/g6
   ```

3. **创建新组件**
   ```typescript
   // web_ui/src/components/GraphCanvasG6.tsx
   ```

4. **并行开发**
   - 保留 Cytoscape 版本
   - 开发 G6 版本
   - 对比效果

5. **切换**
   - 测试通过后切换到 G6
   - 删除 Cytoscape 代码

---

## 其他考虑

### 混合方案

可以同时支持两种渲染引擎：

```typescript
// web_ui/src/App.tsx
const [renderer, setRenderer] = useState<'cytoscape' | 'g6'>('cytoscape');

{renderer === 'cytoscape' ? (
  <GraphCanvas data={graphData} />
) : (
  <GraphCanvasG6 data={graphData} />
)}
```

用户可以在设置中切换。

### WebGL 渲染

对于超大规模图（10,000+ 节点），考虑：
- G6 的 WebGL 模式
- Sigma.js
- 自定义 Three.js 实现

---

## 结论

### 推荐方案

**立即行动**：
1. 保持当前 Cytoscape.js 实现
2. 完善功能和交互
3. 收集用户反馈

**下一步（1-2 周）**：
1. 迁移到 **AntV G6**
2. 使用 Combo 实现超边可视化
3. 提升视觉效果和性能

### 为什么不立即迁移？

1. **当前方案可用**：Cytoscape.js 已经满足基本需求
2. **避免过度工程**：先验证需求，再优化实现
3. **降低风险**：稳定后再重构

### 最终目标

使用 **AntV G6** 实现：
- 美观的超边可视化（Combo）
- 流畅的交互体验
- 优秀的性能表现
- 企业级的代码质量

---

## 参考资源

- [AntV G6 官网](https://g6.antv.antgroup.com/)
- [G6 超边示例](https://g6.antv.antgroup.com/examples/item/combo)
- [D3.js 官网](https://d3js.org/)
- [Cytoscape.js 官网](https://js.cytoscape.org/)
- [Sigma.js 官网](https://www.sigmajs.org/)

# Cytoscape.js 高级可视化特性

## 已实现的特性 ✅

### 1. Cytoscape.js 核心库
- ✅ 使用 Cytoscape.js 3.33.1 作为核心可视化引擎
- ✅ 完整的交互支持（缩放、平移、拖拽）
- ✅ 高性能渲染优化

### 2. 高质量力导向布局 - cose-bilkent ⭐⭐⭐⭐⭐
```typescript
import coseBilkent from 'cytoscape-cose-bilkent';
cytoscape.use(coseBilkent);

const layout = cy.layout({
  name: 'cose-bilkent',
  idealEdgeLength: 100,
  nodeRepulsion: 4500,
  gravity: 0.25,
  numIter: 2500,
  tile: true,
});
```

**优势：**
- 比默认 cose 布局质量更高
- 更好的节点分布和边交叉最小化
- 支持增量布局和动画

### 3. 超边凸包渲染 🎨

实现了自定义超边可视化，使用凸包（Convex Hull）算法：

```typescript
// Graham Scan 算法计算凸包
const computeConvexHull = (points) => {
  // 找到最下方的点作为起点
  // 按极角排序
  // 使用叉积判断转向
  // 返回凸包顶点序列
};

// 在每次渲染时绘制超边包围区域
cy.on('render', () => {
  const hyperedges = cy.edges('[?isHyperedge]');
  hyperedges.forEach(edge => {
    const entities = edge.data('entities');
    const positions = entities.map(id => getNodePosition(id));
    const hull = computeConvexHull(positions);
    
    // 绘制半透明橙色区域
    ctx.fillStyle = 'rgba(251, 191, 36, 0.1)';
    ctx.fill();
    
    // 绘制虚线边框
    ctx.strokeStyle = 'rgba(251, 191, 36, 0.5)';
    ctx.setLineDash([5, 5]);
    ctx.stroke();
  });
});
```

**效果：**
- 超边连接的所有实体被包围在一个半透明橙色区域内
- 虚线边框清晰标识超边范围
- 直观展示多实体关系

### 4. 样式系统

#### 节点样式
- 根据实体类型自动着色：
  - Person: 绿色 (#10b981)
  - Organization: 橙色 (#f59e0b)
  - Location: 紫色 (#8b5cf6)
  - Event: 粉色 (#ec4899)
  - Concept: 青色 (#06b6d4)
- 节点大小根据权重动态调整
- 选中状态高亮显示

#### 边样式
- **普通边**：灰色细线，半透明
- **超边**：橙色粗线（5px），更高不透明度
- 箭头指示方向
- 贝塞尔曲线避免重叠

### 5. 交互功能

#### 鼠标事件
- **单击节点/边**：显示详细信息
- **双击节点**：展开邻居节点（动态加载子图）
- **拖拽节点**：手动调整位置
- **鼠标滚轮**：缩放画布
- **拖拽画布**：平移视图

#### 悬停提示（Tooltip）
```typescript
// 节点悬停
tooltip.innerHTML = `
  <strong>${label}</strong>
  Type: ${type}
  Weight: ${weight}
`;

// 超边悬停
tooltip.innerHTML = `
  ⚡ Hyperedge (${entities.length} entities)
  ${description}
  Connected entities: ${entities.join(', ')}
`;
```

### 6. 性能优化

```typescript
const cy = cytoscape({
  // 视口外隐藏边，提升性能
  hideEdgesOnViewport: true,
  
  // 使用纹理渲染，减少重绘
  textureOnViewport: true,
  
  // 运动模糊效果
  motionBlur: true,
  
  // 自动像素比
  pixelRatio: 'auto',
});
```

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| cytoscape | 3.33.1 | 核心图可视化库 |
| cytoscape-cose-bilkent | 4.1.0 | 高质量力导向布局 |
| React | 19.1.1 | UI 框架 |
| TypeScript | 5.9.3 | 类型安全 |
| Tailwind CSS | 4.1.15 | 样式系统 |

## 与其他方案对比

### Cytoscape.js vs D3.js
- ✅ Cytoscape.js 专为图可视化设计，API 更简洁
- ✅ 内置多种布局算法
- ✅ 更好的性能（大规模图）
- ✅ 丰富的插件生态

### Cytoscape.js vs vis.js
- ✅ 更灵活的样式系统
- ✅ 更好的 TypeScript 支持
- ✅ 更活跃的社区维护

## 未来增强计划

### 可选的布局插件
```bash
# 快速力导向布局
pnpm add cytoscape-fcose

# Cola.js 约束布局
pnpm add cytoscape-cola

# 层次布局（适合有向无环图）
pnpm add cytoscape-dagre

# 欧拉图布局（适合集合可视化）
pnpm add cytoscape-euler
```

### 高级渲染特性
- [ ] 超边的曲线包络（Spline Hull）
- [ ] 节点聚类可视化
- [ ] 时间序列动画
- [ ] 3D 可视化（cytoscape.js-3d）

### 交互增强
- [ ] 节点搜索高亮
- [ ] 路径查找可视化
- [ ] 子图导出
- [ ] 布局参数实时调整

## 参考资源

- [Cytoscape.js 官方文档](https://js.cytoscape.org/)
- [cose-bilkent 布局](https://github.com/cytoscape/cytoscape.js-cose-bilkent)
- [Cytoscape.js 扩展列表](https://js.cytoscape.org/#extensions)
- [Graham Scan 凸包算法](https://en.wikipedia.org/wiki/Graham_scan)

## 示例代码

完整实现见：`web_ui/src/components/GraphCanvas.tsx`

关键特性：
1. ✅ cose-bilkent 高质量布局
2. ✅ 超边凸包渲染
3. ✅ 丰富的交互事件
4. ✅ 性能优化配置
5. ✅ 类型安全的 TypeScript 实现

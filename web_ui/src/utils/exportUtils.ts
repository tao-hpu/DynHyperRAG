import type { Core } from 'cytoscape';
import type { ExportOptions } from '@/components/ExportPanel';
import type { GraphData } from '@/types/graph';

/**
 * 触发浏览器下载文件
 */
export const downloadFile = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * 导出为 PNG 图像
 */
export const exportToPNG = (cy: Core, options: ExportOptions = {}) => {
  const {
    scale = 2,
    backgroundColor = '#ffffff',
  } = options;

  // 使用 Cytoscape 的 png() 方法获取 base64 数据
  const pngDataUrl = cy.png({
    output: 'base64uri',
    bg: backgroundColor,
    full: true, // 导出整个图，不只是视口
    scale: scale,
  });

  // 将 base64 转换为 Blob
  const base64Data = pngDataUrl.split(',')[1];
  const byteCharacters = atob(base64Data);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const pngBlob = new Blob([byteArray], { type: 'image/png' });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  downloadFile(pngBlob, `hypergraph-${timestamp}.png`);
};

/**
 * 导出为 SVG 图像
 * 注意：Cytoscape.js 核心不直接支持 SVG 导出，需要使用插件或手动生成
 * 这里我们使用 PNG 作为替代方案，或者可以考虑使用 cytoscape-svg 插件
 */
export const exportToSVG = (cy: Core, options: ExportOptions = {}) => {
  const {
    scale = 2,
    backgroundColor = '#ffffff',
  } = options;

  // 创建一个简单的 SVG 包装器，包含 PNG 图像
  // 这是一个简化方案，真正的 SVG 导出需要 cytoscape-svg 插件
  const pngDataUrl = cy.png({
    output: 'base64uri',
    bg: backgroundColor,
    full: true,
    scale: scale,
  });

  // 获取图的边界
  const extent = cy.elements().boundingBox();
  const width = (extent.x2 - extent.x1) * scale;
  const height = (extent.y2 - extent.y1) * scale;

  // 创建 SVG 内容，嵌入 PNG 图像
  const svgContent = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
     width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="${backgroundColor}"/>
  <image width="${width}" height="${height}" xlink:href="${pngDataUrl}"/>
</svg>`;

  // 创建 SVG Blob
  const svgBlob = new Blob([svgContent], { type: 'image/svg+xml;charset=utf-8' });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  downloadFile(svgBlob, `hypergraph-${timestamp}.svg`);
};

/**
 * 导出为 JSON 数据
 */
export const exportToJSON = (
  cy: Core,
  graphData: GraphData,
  options: ExportOptions = {}
) => {
  const {
    includeLayout = true,
    includeStyles = false,
  } = options;

  // 基础数据
  const exportData: any = {
    version: '1.0',
    timestamp: new Date().toISOString(),
    nodes: graphData.nodes,
    edges: graphData.edges,
  };

  // 包含布局位置
  if (includeLayout) {
    const layoutData: Record<string, { x: number; y: number }> = {};
    
    cy.nodes().forEach((node) => {
      const pos = node.position();
      layoutData[node.id()] = {
        x: pos.x,
        y: pos.y,
      };
    });
    
    exportData.layout = layoutData;
  }

  // 包含样式信息
  if (includeStyles) {
    const styleData: Record<string, any> = {};
    
    cy.nodes().forEach((node) => {
      styleData[node.id()] = {
        backgroundColor: node.style('background-color'),
        borderColor: node.style('border-color'),
        borderWidth: node.style('border-width'),
        width: node.style('width'),
        height: node.style('height'),
      };
    });
    
    exportData.styles = styleData;
  }

  // 创建 JSON Blob
  const jsonString = JSON.stringify(exportData, null, 2);
  const jsonBlob = new Blob([jsonString], { type: 'application/json;charset=utf-8' });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  downloadFile(jsonBlob, `hypergraph-${timestamp}.json`);
};

/**
 * 从 JSON 导入图数据
 */
export const importFromJSON = (
  jsonString: string
): {
  graphData: GraphData;
  layout?: Record<string, { x: number; y: number }>;
  styles?: Record<string, any>;
} | null => {
  try {
    const data = JSON.parse(jsonString);
    
    // 验证数据格式
    if (!data.nodes || !data.edges) {
      throw new Error('Invalid graph data format');
    }

    return {
      graphData: {
        nodes: data.nodes,
        edges: data.edges,
      },
      layout: data.layout,
      styles: data.styles,
    };
  } catch (error) {
    console.error('Failed to import JSON:', error);
    return null;
  }
};

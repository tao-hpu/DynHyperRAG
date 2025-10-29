/**
 * Performance Optimization Tests
 * 基本的性能优化功能测试
 */

import { describe, it, expect, vi } from 'vitest';

// Mock Cytoscape
const mockCy = {
  extent: vi.fn(() => ({ x1: 0, y1: 0, x2: 1000, y2: 1000 })),
  zoom: vi.fn(() => 1),
  nodes: vi.fn(() => ({
    forEach: vi.fn(),
    length: 100,
  })),
  edges: vi.fn(() => ({
    forEach: vi.fn(),
    length: 150,
  })),
  elements: vi.fn(() => ({
    style: vi.fn(),
  })),
  batch: vi.fn((fn) => fn()),
  on: vi.fn(),
  off: vi.fn(),
  destroyed: vi.fn(() => false),
};

describe('Viewport Culling', () => {
  it('should calculate viewport bounds', () => {
    const { getViewportBounds } = require('../viewportCulling');
    const bounds = getViewportBounds(mockCy as any);
    
    expect(bounds).toEqual({
      x1: 0,
      y1: 0,
      x2: 1000,
      y2: 1000,
    });
  });

  it('should create ViewportCullingManager', () => {
    const { ViewportCullingManager } = require('../viewportCulling');
    const manager = new ViewportCullingManager(mockCy as any, {
      enabled: true,
      padding: 100,
      minZoom: 0.5,
    });
    
    expect(manager).toBeDefined();
    expect(typeof manager.update).toBe('function');
    expect(typeof manager.destroy).toBe('function');
  });
});

describe('Lazy Loading', () => {
  it('should create LazyLoadingManager', () => {
    const { LazyLoadingManager } = require('../lazyLoading');
    const manager = new LazyLoadingManager({
      initialLimit: 1000,
      batchSize: 500,
      loadThreshold: 0.8,
      cacheEnabled: true,
    });
    
    expect(manager).toBeDefined();
    expect(typeof manager.loadInitialData).toBe('function');
    expect(typeof manager.loadMoreNodes).toBe('function');
  });

  it('should get initial stats', () => {
    const { LazyLoadingManager } = require('../lazyLoading');
    const manager = new LazyLoadingManager();
    const stats = manager.getStats();
    
    expect(stats).toEqual({
      cachedNodes: 0,
      cachedEdges: 0,
      hasMoreNodes: true,
      hasMoreEdges: true,
      isLoading: false,
    });
  });

  it('should check if should load more', () => {
    const { LazyLoadingManager } = require('../lazyLoading');
    const manager = new LazyLoadingManager({
      loadThreshold: 0.8,
    });
    
    // 80% threshold: 80/100 = 0.8, should load
    expect(manager.shouldLoadMore(80, 100)).toBe(true);
    
    // 70% threshold: 70/100 = 0.7, should not load
    expect(manager.shouldLoadMore(70, 100)).toBe(false);
  });
});

describe('Loading Indicator', () => {
  it('should create loading indicator data', () => {
    const { LazyLoadingManager, createLoadingIndicator } = require('../lazyLoading');
    const manager = new LazyLoadingManager();
    const indicator = createLoadingIndicator(manager, 1000);
    
    expect(indicator).toHaveProperty('isLoading');
    expect(indicator).toHaveProperty('progress');
    expect(indicator).toHaveProperty('message');
    expect(indicator.isLoading).toBe(false);
  });
});

describe('Performance Integration', () => {
  it('should work together', () => {
    const { ViewportCullingManager } = require('../viewportCulling');
    const { LazyLoadingManager } = require('../lazyLoading');
    
    const cullingManager = new ViewportCullingManager(mockCy as any);
    const lazyManager = new LazyLoadingManager();
    
    expect(cullingManager).toBeDefined();
    expect(lazyManager).toBeDefined();
    
    // Cleanup
    cullingManager.destroy();
    lazyManager.clearCache();
  });
});

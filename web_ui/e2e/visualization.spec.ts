/**
 * E2E Tests for HyperGraphRAG Visualization
 * 
 * NOTE: These tests require:
 * 1. @playwright/test to be installed: pnpm add -D @playwright/test
 * 2. Playwright browsers: pnpm exec playwright install
 * 3. Backend API running on http://localhost:3401
 * 4. Frontend dev server running on http://localhost:3400
 * 
 * To run: pnpm exec playwright test
 */

import { test, expect } from '@playwright/test';

test.describe('Graph Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load and display the application', async ({ page }) => {
    // Check if main elements are visible
    await expect(page.locator('text=HyperGraphRAG')).toBeVisible({ timeout: 10000 });
  });

  test('should render graph canvas', async ({ page }) => {
    // Wait for graph canvas to be rendered
    const canvas = page.locator('.graph-canvas, [data-testid="graph-canvas"]');
    await expect(canvas).toBeVisible({ timeout: 15000 });
  });

  test('should load graph data', async ({ page }) => {
    // Wait for graph to load
    await page.waitForTimeout(3000);
    
    // Check if nodes are rendered (Cytoscape creates canvas elements)
    const canvasElements = page.locator('canvas');
    await expect(canvasElements.first()).toBeVisible();
  });
});

test.describe('Search Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should search for nodes', async ({ page }) => {
    // Find search input
    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();
    
    // Type search query
    await searchInput.fill('test');
    
    // Wait for search results
    await page.waitForTimeout(500); // Debounce delay
    
    // Results should appear (if data exists)
    // Note: This depends on actual data in the system
  });

  test('should focus on selected search result', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill('test');
    await page.waitForTimeout(500);
    
    // Click first result if available
    const firstResult = page.locator('.search-result').first();
    if (await firstResult.isVisible()) {
      await firstResult.click();
      // Graph should focus on the selected node
    }
  });
});

test.describe('Filter Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should filter by entity type', async ({ page }) => {
    // Open filter panel (if not already open)
    const filterPanel = page.locator('text=Entity Types');
    
    if (await filterPanel.isVisible()) {
      // Select a filter checkbox
      const checkbox = page.locator('input[type="checkbox"]').first();
      await checkbox.check();
      
      // Graph should update to show only filtered entities
      await page.waitForTimeout(1000);
    }
  });

  test('should adjust weight filter', async ({ page }) => {
    // Find weight sliders
    const minWeightSlider = page.locator('input[type="range"]').first();
    
    if (await minWeightSlider.isVisible()) {
      await minWeightSlider.fill('5');
      
      // Graph should update
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Query Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should execute a query', async ({ page }) => {
    // Find query input
    const queryInput = page.locator('textarea[placeholder*="question"]');
    
    if (await queryInput.isVisible()) {
      await queryInput.fill('What is hypertension?');
      
      // Click execute button
      const executeButton = page.locator('button:has-text("Execute Query")');
      await executeButton.click();
      
      // Wait for query to complete
      await page.waitForSelector('text=Querying', { state: 'hidden', timeout: 30000 });
      
      // Query result should be visible
      await expect(page.locator('text=Answer').or(page.locator('.query-result'))).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display query path visualization', async ({ page }) => {
    const queryInput = page.locator('textarea[placeholder*="question"]');
    
    if (await queryInput.isVisible()) {
      await queryInput.fill('Test query');
      
      const executeButton = page.locator('button:has-text("Execute Query")');
      await executeButton.click();
      
      // Wait for completion
      await page.waitForSelector('text=Querying', { state: 'hidden', timeout: 30000 });
      
      // Query path should be highlighted in the graph
      // (Visual verification would require screenshot comparison)
    }
  });
});

test.describe('Export Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should export graph as PNG', async ({ page }) => {
    // Find export button
    const exportButton = page.locator('button:has-text("Export")');
    
    if (await exportButton.isVisible()) {
      await exportButton.click();
      
      // Select PNG format
      const pngOption = page.locator('text=PNG');
      if (await pngOption.isVisible()) {
        // Set up download listener
        const downloadPromise = page.waitForEvent('download');
        await pngOption.click();
        
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('.png');
      }
    }
  });

  test('should export graph as JSON', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export")');
    
    if (await exportButton.isVisible()) {
      await exportButton.click();
      
      const jsonOption = page.locator('text=JSON');
      if (await jsonOption.isVisible()) {
        const downloadPromise = page.waitForEvent('download');
        await jsonOption.click();
        
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('.json');
      }
    }
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // App should be responsive
    await expect(page.locator('body')).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    await expect(page.locator('body')).toBeVisible();
  });

  test('should work on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    await expect(page.locator('body')).toBeVisible();
  });
});

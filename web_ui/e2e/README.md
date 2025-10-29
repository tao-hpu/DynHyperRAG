# E2E Tests for HyperGraphRAG Visualization

## Overview

End-to-end tests using Playwright to test the complete user workflows in the HyperGraphRAG visualization system.

## Prerequisites

1. **Install Playwright**:
   ```bash
   cd web_ui
   pnpm add -D @playwright/test
   ```

2. **Install Browsers**:
   ```bash
   pnpm exec playwright install
   ```

3. **Backend API Running**:
   - The backend API must be running on `http://localhost:3401`
   - Start with: `python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401`

4. **Sample Data**:
   - Ensure you have sample data in `expr/example/` directory
   - The tests expect actual graph data to be available

## Running Tests

### Run all tests:
```bash
pnpm exec playwright test
```

### Run tests in UI mode (interactive):
```bash
pnpm exec playwright test --ui
```

### Run specific test file:
```bash
pnpm exec playwright test e2e/visualization.spec.ts
```

### Run tests in headed mode (see browser):
```bash
pnpm exec playwright test --headed
```

### Run tests in specific browser:
```bash
pnpm exec playwright test --project=chromium
pnpm exec playwright test --project=firefox
pnpm exec playwright test --project=webkit
```

## Test Coverage

The E2E tests cover:

1. **Graph Visualization**
   - Loading and rendering the graph
   - Displaying nodes and edges
   - Hyperedge visualization with convex hulls

2. **Search Functionality**
   - Searching for nodes
   - Displaying search results
   - Focusing on selected nodes

3. **Filter Functionality**
   - Filtering by entity type
   - Adjusting weight thresholds
   - Real-time graph updates

4. **Query Functionality**
   - Executing RAG queries
   - Displaying query results
   - Visualizing query paths
   - Query mode selection (local/global/hybrid/naive)

5. **Export Functionality**
   - Exporting as PNG
   - Exporting as SVG
   - Exporting as JSON

6. **Responsive Design**
   - Mobile viewport (375x667)
   - Tablet viewport (768x1024)
   - Desktop viewport (1920x1080)

## Test Structure

```
e2e/
├── README.md                 # This file
├── visualization.spec.ts     # Main E2E test suite
└── fixtures/                 # Test fixtures (if needed)
```

## Debugging Tests

### View test report:
```bash
pnpm exec playwright show-report
```

### Debug specific test:
```bash
pnpm exec playwright test --debug
```

### Generate trace:
```bash
pnpm exec playwright test --trace on
```

## CI/CD Integration

For continuous integration, add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: pnpm install

- name: Install Playwright browsers
  run: pnpm exec playwright install --with-deps

- name: Start backend
  run: python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 &

- name: Run E2E tests
  run: pnpm exec playwright test

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Notes

- Tests assume the backend API is running and has data
- Some tests may be skipped if UI elements are not visible (conditional testing)
- Visual regression testing can be added using Playwright's screenshot comparison
- Tests use reasonable timeouts to account for graph rendering and API calls

## Troubleshooting

### Tests timing out
- Increase timeout in `playwright.config.ts`
- Ensure backend API is responding quickly
- Check network connectivity

### Elements not found
- Verify the frontend is running on port 3400
- Check that data is loaded in the backend
- Inspect element selectors in the test file

### Browser installation issues
- Run: `pnpm exec playwright install --with-deps`
- On Linux, may need system dependencies

## Future Enhancements

- Visual regression testing with screenshot comparison
- Performance testing (load time, interaction responsiveness)
- Accessibility testing (ARIA labels, keyboard navigation)
- Cross-browser compatibility verification
- Mobile gesture testing (pinch zoom, swipe)

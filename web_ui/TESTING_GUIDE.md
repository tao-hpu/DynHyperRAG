# Testing Guide - HyperGraphRAG Web UI

## Overview

This guide provides comprehensive information about the testing infrastructure for the HyperGraphRAG visualization frontend.

## Test Structure

```
web_ui/
├── src/
│   ├── components/
│   │   └── __tests__/          # Component unit tests
│   │       ├── SearchBar.test.tsx
│   │       ├── FilterPanel.test.tsx
│   │       ├── QueryInterface.test.tsx
│   │       └── GraphCanvas.test.tsx
│   ├── services/
│   │   └── __tests__/          # Service integration tests
│   │       ├── graphService.test.ts
│   │       └── queryService.test.ts
│   ├── stores/
│   │   └── __tests__/          # Store integration tests
│   │       ├── graphStore.test.ts
│   │       └── queryStore.test.ts
│   ├── test/
│   │   ├── setup.ts            # Test setup and global mocks
│   │   └── mockData.ts         # Shared mock data
│   └── utils/
│       └── __tests__/          # Utility tests
│           └── performance.test.ts
├── e2e/                        # E2E tests (Playwright)
│   ├── README.md
│   └── visualization.spec.ts
├── vitest.config.ts            # Vitest configuration
├── playwright.config.ts        # Playwright configuration
└── TEST_SUMMARY.md             # Test results summary

```

## Testing Technologies

### Unit & Integration Tests
- **Framework**: [Vitest](https://vitest.dev/) - Fast, Vite-native test runner
- **Testing Library**: [@testing-library/react](https://testing-library.com/react) - User-centric testing utilities
- **DOM Environment**: [happy-dom](https://github.com/capricorn86/happy-dom) - Lightweight DOM implementation
- **Assertions**: [Vitest expect](https://vitest.dev/api/expect.html) + [@testing-library/jest-dom](https://github.com/testing-library/jest-dom)

### E2E Tests
- **Framework**: [Playwright](https://playwright.dev/) - Cross-browser automation
- **Browsers**: Chromium, Firefox, WebKit

## Quick Start

### 1. Install Dependencies
```bash
cd web_ui
pnpm install
```

### 2. Run Unit & Integration Tests
```bash
# Run all tests once
pnpm test

# Run tests in watch mode (auto-rerun on changes)
pnpm test:watch

# Run tests with UI (interactive)
pnpm test:ui

# Run tests with coverage report
pnpm test:coverage
```

### 3. Run E2E Tests (Optional)
```bash
# Install Playwright (first time only)
pnpm add -D @playwright/test
pnpm exec playwright install

# Start backend API (in separate terminal)
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401

# Run E2E tests
pnpm test:e2e

# Run E2E tests in UI mode (interactive)
pnpm test:e2e:ui
```

## Writing Tests

### Component Tests

Component tests focus on user interactions and rendered output.

**Example: Testing a Button Component**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MyButton from '../MyButton';

describe('MyButton', () => {
  it('renders with text', () => {
    render(<MyButton>Click me</MyButton>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    
    render(<MyButton onClick={handleClick}>Click me</MyButton>);
    
    await user.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Service Tests

Service tests verify API interactions and data transformations.

**Example: Testing an API Service**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { myService } from '../myService';
import api from '@/utils/api';

vi.mock('@/utils/api');

describe('MyService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    vi.mocked(api.get).mockResolvedValue({ data: mockData });

    const result = await myService.getData();

    expect(api.get).toHaveBeenCalledWith('/api/data');
    expect(result).toEqual(mockData);
  });
});
```

### Store Tests

Store tests verify state management logic.

**Example: Testing a Zustand Store**
```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useMyStore } from '../myStore';

describe('MyStore', () => {
  beforeEach(() => {
    // Reset store state
    useMyStore.setState({ count: 0 });
  });

  it('increments count', () => {
    const { increment } = useMyStore.getState();
    
    increment();
    
    expect(useMyStore.getState().count).toBe(1);
  });
});
```

### E2E Tests

E2E tests verify complete user workflows.

**Example: Testing a User Flow**
```typescript
import { test, expect } from '@playwright/test';

test('user can search for nodes', async ({ page }) => {
  await page.goto('/');
  
  // Type in search box
  await page.fill('input[placeholder*="Search"]', 'test');
  
  // Wait for results
  await page.waitForSelector('.search-result');
  
  // Click first result
  await page.click('.search-result:first-child');
  
  // Verify node is selected
  await expect(page.locator('.node-details')).toBeVisible();
});
```

## Best Practices

### General
1. **Test behavior, not implementation** - Focus on what users see and do
2. **Keep tests simple** - One concept per test
3. **Use descriptive names** - Test names should explain what they verify
4. **Avoid test interdependence** - Each test should run independently
5. **Mock external dependencies** - API calls, timers, etc.

### Component Tests
1. **Query by accessibility** - Use `getByRole`, `getByLabelText` over `getByTestId`
2. **User-centric queries** - Test what users see, not implementation details
3. **Async properly** - Use `waitFor` for async updates
4. **Setup user events** - Use `userEvent.setup()` for realistic interactions

### Service Tests
1. **Mock API calls** - Don't make real network requests
2. **Test error cases** - Verify error handling
3. **Test edge cases** - Empty responses, null values, etc.

### Store Tests
1. **Reset state** - Clean state between tests
2. **Test actions** - Verify state changes
3. **Test selectors** - Verify computed values

## Debugging Tests

### View Test Output
```bash
# Run specific test file
pnpm test src/components/__tests__/SearchBar.test.tsx

# Run tests matching pattern
pnpm test SearchBar

# Run with verbose output
pnpm test --reporter=verbose
```

### Debug in Browser
```bash
# Open Vitest UI
pnpm test:ui

# Debug E2E tests
pnpm exec playwright test --debug
```

### Common Issues

#### Tests timing out
- Increase timeout: `{ timeout: 10000 }`
- Check for missing `await` on async operations
- Verify mocks are returning resolved promises

#### Elements not found
- Use `screen.debug()` to see rendered HTML
- Check if element is rendered asynchronously
- Verify correct query method (getBy vs findBy vs queryBy)

#### Mocks not working
- Ensure `vi.mock()` is called before imports
- Clear mocks between tests with `vi.clearAllMocks()`
- Check mock implementation returns correct data structure

## Coverage Reports

### Generate Coverage
```bash
pnpm test:coverage
```

### View Coverage Report
Coverage report is generated in `coverage/` directory:
- `coverage/index.html` - Interactive HTML report
- `coverage/coverage-final.json` - JSON data

### Coverage Goals
- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install pnpm
        run: npm install -g pnpm
      
      - name: Install dependencies
        run: pnpm install
        working-directory: ./web_ui
      
      - name: Run tests
        run: pnpm test
        working-directory: ./web_ui
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./web_ui/coverage/coverage-final.json
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library Documentation](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Support

For questions or issues:
1. Check `TEST_SUMMARY.md` for current test status
2. Review test examples in `src/**/__tests__/`
3. Consult E2E test guide in `e2e/README.md`

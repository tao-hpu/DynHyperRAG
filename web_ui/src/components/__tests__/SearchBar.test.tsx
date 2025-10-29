import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from '../SearchBar';
import { graphService } from '@/services/graphService';
import { mockNodes } from '@/test/mockData';

// Mock the graphService
vi.mock('@/services/graphService', () => ({
    graphService: {
        searchNodes: vi.fn(),
    },
}));

describe('SearchBar', () => {
    const mockOnNodeSelect = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders search input', () => {
        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        expect(input).toBeInTheDocument();
    });

    it('shows loading indicator while searching', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockImplementation(
            () => new Promise(resolve => setTimeout(() => resolve(mockNodes), 100))
        );

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        await user.type(input, 'test');

        // Should show loading spinner
        await waitFor(() => {
            const spinner = document.querySelector('.animate-spin');
            expect(spinner).toBeInTheDocument();
        });
    });

    it('displays search results after typing', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockResolvedValue(mockNodes);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        await user.type(input, 'test');

        // Wait for debounce (300ms) and results to appear
        await waitFor(() => {
            expect(screen.getByText('Test Node 1')).toBeInTheDocument();
        }, { timeout: 500 });

        expect(screen.getByText('Test Node 2')).toBeInTheDocument();
        expect(screen.getByText('Test Node 3')).toBeInTheDocument();
    });

    it('calls onNodeSelect when result is clicked', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockResolvedValue(mockNodes);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        await user.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Test Node 1')).toBeInTheDocument();
        }, { timeout: 500 });

        const result = screen.getByText('Test Node 1');
        await user.click(result);

        expect(mockOnNodeSelect).toHaveBeenCalledWith('node1');
    });

    it('clears search after selecting a result', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockResolvedValue(mockNodes);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...') as HTMLInputElement;
        await user.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('Test Node 1')).toBeInTheDocument();
        }, { timeout: 500 });

        const result = screen.getByText('Test Node 1');
        await user.click(result);

        expect(input.value).toBe('');
    });

    it('shows "no results" message when search returns empty', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockResolvedValue([]);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        await user.type(input, 'nonexistent');

        await waitFor(() => {
            expect(screen.getByText(/No results found/i)).toBeInTheDocument();
        }, { timeout: 500 });
    });

    it('debounces search requests', async () => {
        const user = userEvent.setup();
        vi.mocked(graphService.searchNodes).mockResolvedValue(mockNodes);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');

        // Type multiple characters quickly
        await user.type(input, 'test');

        // Should only call searchNodes once after debounce
        await waitFor(() => {
            expect(graphService.searchNodes).toHaveBeenCalledTimes(1);
        }, { timeout: 500 });
    });

    it('displays node type and relevance score', async () => {
        const user = userEvent.setup();
        const nodesWithScore = mockNodes.map(node => ({
            ...node,
            relevanceScore: 0.85,
        }));
        vi.mocked(graphService.searchNodes).mockResolvedValue(nodesWithScore);

        render(<SearchBar onNodeSelect={mockOnNodeSelect} />);

        const input = screen.getByPlaceholderText('Search nodes...');
        await user.type(input, 'test');

        await waitFor(() => {
            expect(screen.getByText('person')).toBeInTheDocument();
            expect(screen.getByText('Score: 0.85')).toBeInTheDocument();
        }, { timeout: 500 });
    });
});

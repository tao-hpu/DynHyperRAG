import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import QueryInterface from '../QueryInterface';

describe('QueryInterface', () => {
    const mockOnQuerySubmit = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders query input and mode selector', () => {
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        expect(screen.getByPlaceholderText(/Enter your question/i)).toBeInTheDocument();
        expect(screen.getByText('Query Mode')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Execute Query/i })).toBeInTheDocument();
    });

    it('disables submit button when query is empty', () => {
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        const submitButton = screen.getByRole('button', { name: /Execute Query/i });
        expect(submitButton).toBeDisabled();
    });

    it('enables submit button when query is entered', async () => {
        const user = userEvent.setup();
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        const input = screen.getByPlaceholderText(/Enter your question/i);
        await user.type(input, 'What is hypertension?');

        const submitButton = screen.getByRole('button', { name: /Execute Query/i });
        expect(submitButton).toBeEnabled();
    });

    it('calls onQuerySubmit with correct parameters', async () => {
        const user = userEvent.setup();
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        const input = screen.getByPlaceholderText(/Enter your question/i);
        await user.type(input, 'What is hypertension?');

        const submitButton = screen.getByRole('button', { name: /Execute Query/i });
        await user.click(submitButton);

        expect(mockOnQuerySubmit).toHaveBeenCalledWith(
            'What is hypertension?',
            'hybrid',
            expect.objectContaining({
                topK: 60,
                maxTokenForTextUnit: 4000,
                maxTokenForLocalContext: 4000,
                maxTokenForGlobalContext: 4000,
            })
        );
    });

    it('submits query with Ctrl+Enter', async () => {
        const user = userEvent.setup();
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        const input = screen.getByPlaceholderText(/Enter your question/i);
        await user.type(input, 'What is hypertension?');
        await user.keyboard('{Control>}{Enter}{/Control}');

        expect(mockOnQuerySubmit).toHaveBeenCalled();
    });

    it('shows loading state when isLoading is true', () => {
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} isLoading={true} />);

        expect(screen.getByText('Querying...')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Querying/i })).toBeDisabled();
    });

    it('toggles advanced parameters panel', async () => {
        const user = userEvent.setup();
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        // Initially hidden
        expect(screen.queryByText('Top K')).not.toBeInTheDocument();

        // Click to show
        const advancedButton = screen.getByText('Advanced Parameters');
        await user.click(advancedButton);

        expect(screen.getByText('Top K')).toBeInTheDocument();
        expect(screen.getByText(/Max Token for Text Unit/i)).toBeInTheDocument();
    });

    it('updates advanced parameters', async () => {
        const user = userEvent.setup();
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        // Show advanced parameters
        const advancedButton = screen.getByText('Advanced Parameters');
        await user.click(advancedButton);

        // Update top_k
        const topKInput = screen.getByLabelText(/Top K/i);
        await user.clear(topKInput);
        await user.type(topKInput, '100');

        // Submit query
        const queryInput = screen.getByPlaceholderText(/Enter your question/i);
        await user.type(queryInput, 'test query');

        const submitButton = screen.getByRole('button', { name: /Execute Query/i });
        await user.click(submitButton);

        expect(mockOnQuerySubmit).toHaveBeenCalledWith(
            'test query',
            'hybrid',
            expect.objectContaining({
                topK: 100,
            })
        );
    });

    it('displays helpful tips', () => {
        render(<QueryInterface onQuerySubmit={mockOnQuerySubmit} />);

        expect(screen.getByText(/Press Ctrl\+Enter/i)).toBeInTheDocument();
        expect(screen.getByText(/Different modes provide different perspectives/i)).toBeInTheDocument();
    });
});

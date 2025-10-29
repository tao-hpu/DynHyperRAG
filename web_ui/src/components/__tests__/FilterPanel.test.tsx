import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FilterPanel from '../FilterPanel';

describe('FilterPanel', () => {
    const mockOnFilterChange = vi.fn();
    const availableTypes = ['person', 'organization', 'location', 'event'];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders all available entity types', () => {
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        expect(screen.getByText('person')).toBeInTheDocument();
        expect(screen.getByText('organization')).toBeInTheDocument();
        expect(screen.getByText('location')).toBeInTheDocument();
        expect(screen.getByText('event')).toBeInTheDocument();
    });

    it('calls onFilterChange when type is selected', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });
        await user.click(personCheckbox);

        expect(mockOnFilterChange).toHaveBeenCalledWith({
            entityTypes: ['person'],
            minWeight: 0,
            maxWeight: 20,
        });
    });

    it('allows multiple type selections', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });
        const orgCheckbox = screen.getByRole('checkbox', { name: /organization/i });

        await user.click(personCheckbox);
        await user.click(orgCheckbox);

        expect(mockOnFilterChange).toHaveBeenLastCalledWith({
            entityTypes: ['person', 'organization'],
            minWeight: 0,
            maxWeight: 20,
        });
    });

    it('deselects type when clicked again', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });

        // Select
        await user.click(personCheckbox);
        expect(mockOnFilterChange).toHaveBeenCalledWith({
            entityTypes: ['person'],
            minWeight: 0,
            maxWeight: 20,
        });

        // Deselect
        await user.click(personCheckbox);
        expect(mockOnFilterChange).toHaveBeenLastCalledWith({
            entityTypes: [],
            minWeight: 0,
            maxWeight: 20,
        });
    });

    it('updates min weight filter', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const minWeightSlider = screen.getByLabelText(/Min:/i);
        await user.clear(minWeightSlider);
        await user.type(minWeightSlider, '5');

        expect(mockOnFilterChange).toHaveBeenCalledWith({
            entityTypes: [],
            minWeight: 5,
            maxWeight: 20,
        });
    });

    it('updates max weight filter', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const maxWeightSlider = screen.getByLabelText(/Max:/i);
        await user.clear(maxWeightSlider);
        await user.type(maxWeightSlider, '15');

        expect(mockOnFilterChange).toHaveBeenCalledWith({
            entityTypes: [],
            minWeight: 0,
            maxWeight: 15,
        });
    });

    it('shows reset button when filters are active', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        // Initially no reset button
        expect(screen.queryByText('Reset')).not.toBeInTheDocument();

        // Select a type
        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });
        await user.click(personCheckbox);

        // Reset button should appear
        expect(screen.getByText('Reset')).toBeInTheDocument();
    });

    it('resets all filters when reset is clicked', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        // Apply some filters
        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });
        await user.click(personCheckbox);

        const minWeightSlider = screen.getByLabelText(/Min:/i);
        await user.clear(minWeightSlider);
        await user.type(minWeightSlider, '5');

        // Click reset
        const resetButton = screen.getByText('Reset');
        await user.click(resetButton);

        expect(mockOnFilterChange).toHaveBeenLastCalledWith({
            entityTypes: [],
            minWeight: 0,
            maxWeight: 20,
        });
    });

    it('displays active filter summary', async () => {
        const user = userEvent.setup();
        render(
            <FilterPanel
                onFilterChange={mockOnFilterChange}
                availableTypes={availableTypes}
            />
        );

        const personCheckbox = screen.getByRole('checkbox', { name: /person/i });
        await user.click(personCheckbox);

        expect(screen.getByText(/Active filters:/i)).toBeInTheDocument();
        expect(screen.getByText(/1 types/i)).toBeInTheDocument();
    });
});

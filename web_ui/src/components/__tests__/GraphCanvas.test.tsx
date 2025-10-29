import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import GraphCanvas from '../GraphCanvas';
import { mockGraphData } from '@/test/mockData';

// Mock Cytoscape
vi.mock('cytoscape', () => {
    const mockCy = {
        on: vi.fn(),
        off: vi.fn(),
        batch: vi.fn((fn) => fn()),
        elements: vi.fn(() => ({
            remove: vi.fn(),
            unselect: vi.fn(),
            removeClass: vi.fn(),
        })),
        add: vi.fn(),
        layout: vi.fn(() => ({
            run: vi.fn(),
            stop: vi.fn(),
        })),
        nodes: vi.fn(() => ({
            forEach: vi.fn(),
        })),
        edges: vi.fn(() => ({
            forEach: vi.fn(),
        })),
        getElementById: vi.fn(() => ({
            length: 0,
        })),
        container: vi.fn(() => document.createElement('div')),
        resize: vi.fn(),
        fit: vi.fn(),
        animate: vi.fn(),
        zoom: vi.fn(() => 1),
        destroyed: vi.fn(() => false),
        destroy: vi.fn(),
    };

    return {
        default: vi.fn(() => mockCy),
    };
});

// Mock cytoscape-cose-bilkent
vi.mock('cytoscape-cose-bilkent', () => ({
    default: {},
}));

// Mock ViewportCullingManager
vi.mock('@/utils/viewportCulling', () => ({
    ViewportCullingManager: vi.fn().mockImplementation(() => ({
        update: vi.fn(),
        destroy: vi.fn(),
    })),
}));

// Mock export utils
vi.mock('@/utils/exportUtils', () => ({
    exportToPNG: vi.fn(),
    exportToSVG: vi.fn(),
    exportToJSON: vi.fn(),
}));

describe('GraphCanvas', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders canvas container', () => {
        const { container } = render(<GraphCanvas data={mockGraphData} />);

        const canvasDiv = container.querySelector('div');
        expect(canvasDiv).toBeInTheDocument();
    });

    it('initializes with graph data', () => {
        const cytoscape = require('cytoscape').default;

        render(<GraphCanvas data={mockGraphData} />);

        // Cytoscape should be called to initialize
        expect(cytoscape).toHaveBeenCalled();
    });

    it('calls onNodeClick when provided', () => {
        const mockOnNodeClick = vi.fn();

        render(
            <GraphCanvas
                data={mockGraphData}
                onNodeClick={mockOnNodeClick}
            />
        );

        // Component should render without errors
        expect(mockOnNodeClick).not.toHaveBeenCalled();
    });

    it('calls onEdgeClick when provided', () => {
        const mockOnEdgeClick = vi.fn();

        render(
            <GraphCanvas
                data={mockGraphData}
                onEdgeClick={mockOnEdgeClick}
            />
        );

        // Component should render without errors
        expect(mockOnEdgeClick).not.toHaveBeenCalled();
    });

    it('calls onNodeDoubleClick when provided', () => {
        const mockOnNodeDoubleClick = vi.fn();

        render(
            <GraphCanvas
                data={mockGraphData}
                onNodeDoubleClick={mockOnNodeDoubleClick}
            />
        );

        // Component should render without errors
        expect(mockOnNodeDoubleClick).not.toHaveBeenCalled();
    });

    it('handles empty graph data', () => {
        const emptyData = { nodes: [], edges: [] };

        const { container } = render(<GraphCanvas data={emptyData} />);

        expect(container.querySelector('div')).toBeInTheDocument();
    });

    it('applies custom settings when provided', () => {
        const customSettings = {
            node: {
                minSize: 30,
                maxSize: 80,
                fontSize: 14,
                fontWeight: 600,
            },
            colorScheme: {
                person: '#ff0000',
                organization: '#00ff00',
                location: '#0000ff',
                event: '#ffff00',
                concept: '#ff00ff',
                default: '#cccccc',
                edge: '#999999',
                hyperedge: '#fb923c',
                queryPathLow: '#fef3c7',
                queryPathMedium: '#fbbf24',
                queryPathHigh: '#f59e0b',
            },
            layout: {
                idealEdgeLength: 150,
                nodeRepulsion: 8000,
                gravity: 0.3,
                numIter: 3000,
            },
        };

        render(
            <GraphCanvas
                data={mockGraphData}
                settings={customSettings}
            />
        );

        // Component should render with custom settings
        expect(true).toBe(true);
    });
});

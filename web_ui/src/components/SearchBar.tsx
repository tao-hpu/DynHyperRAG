import { useState, useEffect, useCallback } from 'react';
import type { Node } from '@/types/graph';
import { graphService } from '@/services/graphService';

interface SearchBarProps {
  onNodeSelect: (nodeId: string) => void;
}

const SearchBar = ({ onNodeSelect }: SearchBarProps) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Node[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setShowResults(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const searchResults = await graphService.searchNodes({ keyword: query, limit: 10 });
        setResults(searchResults);
        setShowResults(true);
      } catch (err) {
        console.error('Search failed:', err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleResultClick = useCallback((nodeId: string) => {
    onNodeSelect(nodeId);
    setShowResults(false);
    setQuery('');
  }, [onNodeSelect]);

  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder="Search nodes..."
          className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          {loading ? (
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          ) : (
            <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
      </div>

      {showResults && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {results.map((node) => (
            <button
              key={node.id}
              onClick={() => handleResultClick(node.id)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
            >
              <div className="font-medium text-gray-900">{node.label}</div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                  {node.type}
                </span>
                {node.relevanceScore && (
                  <span className="text-xs text-gray-500">
                    Score: {node.relevanceScore.toFixed(2)}
                  </span>
                )}
              </div>
              {node.description && (
                <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                  {node.description}
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {showResults && query && results.length === 0 && !loading && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-gray-500 text-sm">
          No results found for "{query}"
        </div>
      )}
    </div>
  );
};

export default SearchBar;

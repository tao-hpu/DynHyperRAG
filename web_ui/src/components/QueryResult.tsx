import ReactMarkdown from 'react-markdown';
import type { QueryResponse } from '@/types/query';

interface QueryResultProps {
    result: QueryResponse;
    onClose?: () => void;
}

const QueryResult = ({ result, onClose }: QueryResultProps) => {
    return (
        <div className="space-y-4">
            {/* Header with close button */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800">Query Result</h3>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
                        aria-label="Close result"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
            </div>

            {/* Execution time badge */}
            <div className="flex items-center gap-2">
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                    ⚡ {result.executionTime.toFixed(2)}s
                </span>
                <span className="text-xs text-gray-500">
                    {result.queryPath.nodes.length} nodes, {result.queryPath.edges.length} edges
                </span>
            </div>

            {/* Answer section */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <h4 className="font-semibold text-gray-800">Answer</h4>
                </div>
                <div className="prose prose-sm max-w-none text-gray-700">
                    <ReactMarkdown
                        components={{
                            // Custom styling for markdown elements
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                            li: ({ children }) => <li className="text-sm">{children}</li>,
                            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                            em: ({ children }) => <em className="italic">{children}</em>,
                            code: ({ children }) => (
                                <code className="px-1.5 py-0.5 bg-gray-100 text-gray-800 rounded text-xs font-mono">
                                    {children}
                                </code>
                            ),
                            pre: ({ children }) => (
                                <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto text-xs">
                                    {children}
                                </pre>
                            ),
                        }}
                    >
                        {result.answer}
                    </ReactMarkdown>
                </div>
            </div>

            {/* Context used section */}
            {result.contextUsed && result.contextUsed.length > 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <h4 className="font-semibold text-gray-800">Context Used</h4>
                        <span className="text-xs text-gray-500">({result.contextUsed.length} chunks)</span>
                    </div>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                        {result.contextUsed.map((context, index) => (
                            <div
                                key={index}
                                className="bg-white p-3 rounded border border-gray-200 text-sm text-gray-700"
                            >
                                <div className="flex items-start gap-2">
                                    <span className="flex-shrink-0 w-5 h-5 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-medium">
                                        {index + 1}
                                    </span>
                                    <p className="flex-1 text-xs leading-relaxed line-clamp-3">
                                        {context}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Query path info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    <h4 className="font-semibold text-gray-800">Query Path Visualization</h4>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                    <div className="bg-white p-2 rounded border border-blue-200">
                        <div className="text-xs text-gray-500 mb-1">Nodes Visited</div>
                        <div className="text-lg font-semibold text-blue-600">
                            {result.queryPath.nodes.length}
                        </div>
                    </div>
                    <div className="bg-white p-2 rounded border border-blue-200">
                        <div className="text-xs text-gray-500 mb-1">Edges Traversed</div>
                        <div className="text-lg font-semibold text-blue-600">
                            {result.queryPath.edges.length}
                        </div>
                    </div>
                </div>

                {/* Path highlighting legend */}
                <div className="bg-white p-3 rounded border border-blue-200 mb-3">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Path Highlighting Legend:</div>
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#f59e0b] border-2 border-[#ea580c]"></div>
                            <span className="text-gray-700">High relevance (score ≥ 0.7) - Larger size, full opacity</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#fbbf24] border-2 border-[#f59e0b]"></div>
                            <span className="text-gray-700">Medium relevance (0.4 ≤ score &lt; 0.7) - Medium size</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#fef3c7] border-2 border-[#fbbf24]"></div>
                            <span className="text-gray-700">Low relevance (score &lt; 0.4) - Smaller size, reduced opacity</span>
                        </div>
                    </div>
                </div>

                {/* Top scored nodes */}
                {Object.keys(result.queryPath.scores).length > 0 && (
                    <div className="mt-3">
                        <div className="text-xs text-gray-600 mb-2 font-medium">Top Relevant Nodes:</div>
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                            {Object.entries(result.queryPath.scores)
                                .sort(([, a], [, b]) => b - a)
                                .slice(0, 10)
                                .map(([nodeId, score], index) => {
                                    // Determine color based on score
                                    let bgColor = 'bg-amber-50';
                                    let textColor = 'text-amber-700';
                                    let borderColor = 'border-amber-200';

                                    if (score >= 0.7) {
                                        bgColor = 'bg-orange-100';
                                        textColor = 'text-orange-700';
                                        borderColor = 'border-orange-300';
                                    } else if (score >= 0.4) {
                                        bgColor = 'bg-amber-100';
                                        textColor = 'text-amber-700';
                                        borderColor = 'border-amber-300';
                                    }

                                    return (
                                        <div
                                            key={nodeId}
                                            className={`flex items-center justify-between ${bgColor} px-2 py-1.5 rounded border ${borderColor} text-xs`}
                                        >
                                            <div className="flex items-center gap-2 flex-1 min-w-0">
                                                <span className={`flex-shrink-0 w-5 h-5 ${textColor} rounded-full flex items-center justify-center text-xs font-medium`}>
                                                    {index + 1}
                                                </span>
                                                <span className="text-gray-700 truncate flex-1" title={nodeId}>
                                                    {nodeId.replace(/"/g, '')}
                                                </span>
                                            </div>
                                            <span className={`${textColor} font-semibold ml-2`}>
                                                {score.toFixed(3)}
                                            </span>
                                        </div>
                                    );
                                })}
                        </div>
                    </div>
                )}
            </div>

            {/* Helpful tips */}
            <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded border border-gray-200">
                <p className="font-medium text-gray-700 mb-1">💡 Next Steps:</p>
                <ul className="list-disc list-inside space-y-1">
                    <li>The query path is highlighted in the graph visualization</li>
                    <li>Click on nodes to see their details and relevance scores</li>
                    <li>Try different query modes to compare results</li>
                </ul>
            </div>
        </div>
    );
};

export default QueryResult;

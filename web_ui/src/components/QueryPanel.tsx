import { useState } from 'react';
import QueryInterface, { type QueryConfig } from './QueryInterface';
import QueryResult from './QueryResult';
import { Button } from '@/components/ui/button';
import { useQueryStore } from '@/stores/queryStore';
import { queryService } from '@/services/queryService';
import type { QueryMode, QueryResponse } from '@/types/query';

interface QueryPanelProps {
    onQueryExecuted?: (response: QueryResponse) => void;
    onModeChange?: (mode: QueryMode) => void;
}

const QueryPanel = ({ onQueryExecuted, onModeChange }: QueryPanelProps) => {
    const [activeTab, setActiveTab] = useState<'query' | 'result' | 'history'>('query');

    const {
        currentResponse,
        setCurrentResponse,
        history,
        isQuerying,
        setQuerying,
        setError,
        error,
        addToHistory,
        removeFromHistory,
        clearHistory,
    } = useQueryStore();

    const handleQuerySubmit = async (query: string, mode: QueryMode, config: QueryConfig) => {
        try {
            setQuerying(true);
            setError(null);

            // 通知父组件查询模式变化
            if (onModeChange) {
                onModeChange(mode);
            }

            const response = await queryService.executeQuery({
                query,
                mode,
                topK: config.topK,
                maxTokenForTextUnit: config.maxTokenForTextUnit,
                maxTokenForLocalContext: config.maxTokenForLocalContext,
                maxTokenForGlobalContext: config.maxTokenForGlobalContext,
            });

            setCurrentResponse(response);

            // 添加到历史记录
            addToHistory({
                query,
                mode,
                answer: response.answer,
                executionTime: response.executionTime,
            });

            // 切换到结果标签
            setActiveTab('result');

            // 通知父组件
            if (onQueryExecuted) {
                onQueryExecuted(response);
            }
        } catch (err) {
            console.error('Query failed:', err);
            setError(err instanceof Error ? err.message : 'Query execution failed');
        } finally {
            setQuerying(false);
        }
    };

    const handleHistoryItemClick = async (item: typeof history[0]) => {
        try {
            setQuerying(true);
            setError(null);

            const response = await queryService.executeQuery({
                query: item.query,
                mode: item.mode,
            });

            setCurrentResponse(response);
            setActiveTab('result');

            if (onQueryExecuted) {
                onQueryExecuted(response);
            }
        } catch (err) {
            console.error('Re-execution failed:', err);
            setError(err instanceof Error ? err.message : 'Query re-execution failed');
        } finally {
            setQuerying(false);
        }
    };

    const handleClearHistory = () => {
        if (window.confirm('Are you sure you want to clear all query history?')) {
            clearHistory();
        }
    };

    return (
        <div className="flex flex-col h-full">
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200 bg-white">
                <button
                    onClick={() => setActiveTab('query')}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'query'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                        }`}
                >
                    <div className="flex items-center justify-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Query
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('result')}
                    disabled={!currentResponse}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'result'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed'
                        }`}
                >
                    <div className="flex items-center justify-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Result
                    </div>
                </button>
                <button
                    onClick={() => setActiveTab('history')}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'history'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                        }`}
                >
                    <div className="flex items-center justify-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        History
                        {history.length > 0 && (
                            <span className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded-full text-xs">
                                {history.length}
                            </span>
                        )}
                    </div>
                </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                        <div className="flex items-start gap-2">
                            <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div>
                                <div className="font-medium">Query Error</div>
                                <div className="mt-1">{error}</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Query Tab */}
                {activeTab === 'query' && (
                    <QueryInterface
                        onQuerySubmit={handleQuerySubmit}
                        isLoading={isQuerying}
                    />
                )}

                {/* Result Tab */}
                {activeTab === 'result' && currentResponse && (
                    <QueryResult
                        result={currentResponse}
                        onClose={() => setCurrentResponse(null)}
                    />
                )}

                {activeTab === 'result' && !currentResponse && (
                    <div className="text-center text-gray-500 py-12">
                        <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-sm">No query result yet</p>
                        <p className="text-xs mt-2">Execute a query to see results here</p>
                    </div>
                )}

                {/* History Tab */}
                {activeTab === 'history' && (
                    <div className="space-y-3">
                        {history.length > 0 && (
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-sm font-medium text-gray-700">
                                    Recent Queries ({history.length})
                                </h3>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleClearHistory}
                                    className="text-xs"
                                >
                                    Clear All
                                </Button>
                            </div>
                        )}

                        {history.length === 0 ? (
                            <div className="text-center text-gray-500 py-12">
                                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <p className="text-sm">No query history</p>
                                <p className="text-xs mt-2">Your executed queries will appear here</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {history.map((item) => (
                                    <div
                                        key={item.id}
                                        className="bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-300 hover:shadow-sm transition-all"
                                    >
                                        <div className="flex items-start justify-between gap-2 mb-2">
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-gray-800 line-clamp-2">
                                                    {item.query}
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => removeFromHistory(item.id)}
                                                className="flex-shrink-0 text-gray-400 hover:text-red-600 transition-colors"
                                                aria-label="Remove from history"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </div>

                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                                                {item.mode}
                                            </span>
                                            <span className="text-xs text-gray-500">
                                                {item.executionTime.toFixed(2)}s
                                            </span>
                                            <span className="text-xs text-gray-400">
                                                {new Date(item.timestamp).toLocaleString()}
                                            </span>
                                        </div>

                                        <p className="text-xs text-gray-600 line-clamp-2 mb-3">
                                            {item.answer}
                                        </p>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleHistoryItemClick(item)}
                                            disabled={isQuerying}
                                            className="w-full text-xs"
                                        >
                                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                            </svg>
                                            Re-execute
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default QueryPanel;

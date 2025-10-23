import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import type { QueryMode } from '@/types/query';

interface QueryInterfaceProps {
    onQuerySubmit: (query: string, mode: QueryMode, config: QueryConfig) => void;
    isLoading?: boolean;
}

export interface QueryConfig {
    topK: number;
    maxTokenForTextUnit: number;
    maxTokenForLocalContext: number;
    maxTokenForGlobalContext: number;
}

const QueryInterface = ({ onQuerySubmit, isLoading = false }: QueryInterfaceProps) => {
    const [query, setQuery] = useState('');
    const [mode, setMode] = useState<QueryMode>('hybrid');
    const [showAdvanced, setShowAdvanced] = useState(false);

    // 高级参数配置
    const [config, setConfig] = useState<QueryConfig>({
        topK: 60,
        maxTokenForTextUnit: 4000,
        maxTokenForLocalContext: 4000,
        maxTokenForGlobalContext: 4000,
    });

    const handleSubmit = () => {
        if (!query.trim() || isLoading) return;
        onQuerySubmit(query, mode, config);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Ctrl/Cmd + Enter to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="space-y-4">
            {/* 查询输入框 */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Query
                </label>
                <Textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter your question here... (Ctrl+Enter to submit)"
                    className="min-h-[100px] resize-y"
                    disabled={isLoading}
                />
            </div>

            {/* 查询模式选择器 */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Query Mode
                </label>
                <Select value={mode} onValueChange={(value) => setMode(value as QueryMode)} disabled={isLoading}>
                    <SelectTrigger>
                        <SelectValue placeholder="Select query mode" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="hybrid">
                            <div className="flex flex-col items-start">
                                <span className="font-medium">Hybrid</span>
                                <span className="text-xs text-gray-500">Combines local and global context</span>
                            </div>
                        </SelectItem>
                        <SelectItem value="local">
                            <div className="flex flex-col items-start">
                                <span className="font-medium">Local</span>
                                <span className="text-xs text-gray-500">Uses nearby entities and relationships</span>
                            </div>
                        </SelectItem>
                        <SelectItem value="global">
                            <div className="flex flex-col items-start">
                                <span className="font-medium">Global</span>
                                <span className="text-xs text-gray-500">Uses graph-wide context</span>
                            </div>
                        </SelectItem>
                        <SelectItem value="naive">
                            <div className="flex flex-col items-start">
                                <span className="font-medium">Naive</span>
                                <span className="text-xs text-gray-500">Simple text-based retrieval</span>
                            </div>
                        </SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* 高级参数配置 */}
            <div>
                <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                    disabled={isLoading}
                >
                    <svg
                        className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-90' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    Advanced Parameters
                </button>

                {showAdvanced && (
                    <div className="mt-3 space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Top K
                                <span className="text-xs text-gray-500 ml-2">Number of results to retrieve</span>
                            </label>
                            <Input
                                type="number"
                                value={config.topK}
                                onChange={(e) => setConfig({ ...config, topK: parseInt(e.target.value) || 60 })}
                                min={1}
                                max={200}
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Max Token for Text Unit
                                <span className="text-xs text-gray-500 ml-2">Maximum tokens per text chunk</span>
                            </label>
                            <Input
                                type="number"
                                value={config.maxTokenForTextUnit}
                                onChange={(e) => setConfig({ ...config, maxTokenForTextUnit: parseInt(e.target.value) || 4000 })}
                                min={100}
                                max={8000}
                                step={100}
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Max Token for Local Context
                                <span className="text-xs text-gray-500 ml-2">Maximum tokens for local retrieval</span>
                            </label>
                            <Input
                                type="number"
                                value={config.maxTokenForLocalContext}
                                onChange={(e) => setConfig({ ...config, maxTokenForLocalContext: parseInt(e.target.value) || 4000 })}
                                min={100}
                                max={8000}
                                step={100}
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Max Token for Global Context
                                <span className="text-xs text-gray-500 ml-2">Maximum tokens for global retrieval</span>
                            </label>
                            <Input
                                type="number"
                                value={config.maxTokenForGlobalContext}
                                onChange={(e) => setConfig({ ...config, maxTokenForGlobalContext: parseInt(e.target.value) || 4000 })}
                                min={100}
                                max={8000}
                                step={100}
                                disabled={isLoading}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* 查询按钮 */}
            <Button
                onClick={handleSubmit}
                disabled={!query.trim() || isLoading}
                className="w-full"
                size="lg"
            >
                {isLoading ? (
                    <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                        Querying...
                    </>
                ) : (
                    <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        Execute Query
                    </>
                )}
            </Button>

            {/* 提示信息 */}
            <div className="text-xs text-gray-500 space-y-1">
                <p>💡 Tip: Press Ctrl+Enter (Cmd+Enter on Mac) to submit quickly</p>
                <p>🔍 Different modes provide different perspectives on the knowledge graph</p>
            </div>
        </div>
    );
};

export default QueryInterface;

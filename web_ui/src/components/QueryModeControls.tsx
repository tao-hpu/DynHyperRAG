import { useState } from 'react';
import type { QueryMode } from '@/types/query';

interface QueryModeControlsProps {
    currentMode: QueryMode;
    onModeFilterChange?: (showLocal: boolean, showGlobal: boolean) => void;
}

const QueryModeControls = ({ currentMode, onModeFilterChange }: QueryModeControlsProps) => {
    const [showLocal, setShowLocal] = useState(true);
    const [showGlobal, setShowGlobal] = useState(true);

    const handleLocalToggle = () => {
        const newShowLocal = !showLocal;
        setShowLocal(newShowLocal);
        if (onModeFilterChange) {
            onModeFilterChange(newShowLocal, showGlobal);
        }
    };

    const handleGlobalToggle = () => {
        const newShowGlobal = !showGlobal;
        setShowGlobal(newShowGlobal);
        if (onModeFilterChange) {
            onModeFilterChange(showLocal, newShowGlobal);
        }
    };

    // Only show controls for hybrid mode
    if (currentMode !== 'hybrid') {
        return (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                    </svg>
                    Query Mode Legend
                </h4>

                <div className="space-y-3">
                    {/* Current mode indicator */}
                    <div className="bg-blue-50 border border-blue-200 rounded p-3">
                        <div className="text-xs text-gray-600 mb-1">Current Mode:</div>
                        <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${currentMode === 'local' ? 'bg-blue-100 text-blue-700' :
                                    currentMode === 'global' ? 'bg-purple-100 text-purple-700' :
                                        currentMode === 'naive' ? 'bg-gray-100 text-gray-700' :
                                            'bg-green-100 text-green-700'
                                }`}>
                                {currentMode.charAt(0).toUpperCase() + currentMode.slice(1)}
                            </span>
                        </div>
                    </div>

                    {/* Mode description */}
                    <div className="text-xs text-gray-600 space-y-2">
                        {currentMode === 'local' && (
                            <p>🔵 Local mode retrieves information from nearby entities and their direct relationships in the knowledge graph.</p>
                        )}
                        {currentMode === 'global' && (
                            <p>🟣 Global mode retrieves information from graph-wide patterns and community structures.</p>
                        )}
                        {currentMode === 'naive' && (
                            <p>⚪ Naive mode uses simple text-based retrieval without leveraging graph structure.</p>
                        )}
                    </div>

                    {/* Path highlighting legend */}
                    <div className="border-t border-gray-200 pt-3">
                        <div className="text-xs text-gray-600 mb-2 font-medium">Path Highlighting:</div>
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-2 text-xs">
                                <div className="w-4 h-4 rounded-full bg-[#f59e0b] border-2 border-[#ea580c]"></div>
                                <span className="text-gray-700">High relevance (score ≥ 0.7)</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs">
                                <div className="w-4 h-4 rounded-full bg-[#fbbf24] border-2 border-[#f59e0b]"></div>
                                <span className="text-gray-700">Medium relevance (0.4 ≤ score &lt; 0.7)</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs">
                                <div className="w-4 h-4 rounded-full bg-[#fef3c7] border-2 border-[#fbbf24]"></div>
                                <span className="text-gray-700">Low relevance (score &lt; 0.4)</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Hybrid mode - show mode filtering controls
    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
                Hybrid Mode Controls
            </h4>

            <div className="space-y-3">
                {/* Mode description */}
                <div className="bg-green-50 border border-green-200 rounded p-3">
                    <div className="text-xs text-gray-600 mb-1">Current Mode:</div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">
                            Hybrid
                        </span>
                    </div>
                    <p className="text-xs text-gray-600">
                        Combines both local and global retrieval strategies for comprehensive results.
                    </p>
                </div>

                {/* Mode filtering toggles */}
                <div className="space-y-2">
                    <div className="text-xs text-gray-600 font-medium mb-2">Show Paths From:</div>

                    {/* Local toggle */}
                    <label className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showLocal}
                            onChange={handleLocalToggle}
                            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                        <div className="flex items-center gap-2 flex-1">
                            <div className="w-4 h-4 rounded-full bg-blue-400 border-2 border-blue-600"></div>
                            <span className="text-sm text-gray-700">Local Retrieval</span>
                        </div>
                    </label>

                    {/* Global toggle */}
                    <label className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={showGlobal}
                            onChange={handleGlobalToggle}
                            className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                        />
                        <div className="flex items-center gap-2 flex-1">
                            <div className="w-4 h-4 rounded-full bg-purple-400 border-2 border-purple-600"></div>
                            <span className="text-sm text-gray-700">Global Retrieval</span>
                        </div>
                    </label>
                </div>

                {/* Legend */}
                <div className="border-t border-gray-200 pt-3">
                    <div className="text-xs text-gray-600 mb-2 font-medium">Node Colors:</div>
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#60a5fa] border-2 border-[#3b82f6]"></div>
                            <span className="text-gray-700">Local retrieval only</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#a78bfa] border-2 border-[#8b5cf6]"></div>
                            <span className="text-gray-700">Global retrieval only</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <div className="w-4 h-4 rounded-full bg-[#34d399] border-2 border-[#10b981]"></div>
                            <span className="text-gray-700">Both local and global</span>
                        </div>
                    </div>
                </div>

                {/* Help text */}
                <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                    💡 Toggle to compare how different retrieval strategies contribute to the answer
                </div>
            </div>
        </div>
    );
};

export default QueryModeControls;

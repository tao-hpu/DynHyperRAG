import { useState } from 'react';

export type ExportFormat = 'png' | 'svg' | 'json';

interface ExportPanelProps {
    onExport: (format: ExportFormat, options?: ExportOptions) => void;
    onImport?: (data: string) => void;
}

export interface ExportOptions {
    // 图像导出选项
    scale?: number;
    quality?: number;
    backgroundColor?: string;

    // JSON 导出选项
    includeLayout?: boolean;
    includeStyles?: boolean;
}

const ExportPanel = ({ onExport, onImport }: ExportPanelProps) => {
    const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('png');
    const [scale, setScale] = useState(2);
    const [quality, setQuality] = useState(0.95);
    const [backgroundColor, setBackgroundColor] = useState('#ffffff');
    const [includeLayout, setIncludeLayout] = useState(true);
    const [includeStyles, setIncludeStyles] = useState(false);
    const [isExporting, setIsExporting] = useState(false);

    const handleExport = async () => {
        setIsExporting(true);

        try {
            const options: ExportOptions = {
                scale,
                quality,
                backgroundColor,
                includeLayout,
                includeStyles,
            };

            await onExport(selectedFormat, options);
        } finally {
            setIsExporting(false);
        }
    };

    const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !onImport) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;
            if (content) {
                onImport(content);
            }
        };
        reader.readAsText(file);
    };

    return (
        <div className="bg-white rounded-lg shadow-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Export Graph</h2>

            <div className="space-y-4">
                {/* 格式选择 */}
                <div>
                    <h3 className="font-medium text-gray-700 mb-2 text-sm">Export Format</h3>
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            onClick={() => setSelectedFormat('png')}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${selectedFormat === 'png'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            PNG
                        </button>
                        <button
                            onClick={() => setSelectedFormat('svg')}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${selectedFormat === 'svg'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            SVG
                        </button>
                        <button
                            onClick={() => setSelectedFormat('json')}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${selectedFormat === 'json'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            JSON
                        </button>
                    </div>
                </div>

                {/* 图像导出选项 */}
                {(selectedFormat === 'png' || selectedFormat === 'svg') && (
                    <div className="space-y-3 pt-2 border-t border-gray-200">
                        <h3 className="font-medium text-gray-700 text-sm">Image Options</h3>

                        {/* 分辨率/缩放 */}
                        <div>
                            <label className="text-xs text-gray-600 block mb-1">
                                Scale: {scale}x ({scale === 1 ? 'Standard' : scale === 2 ? 'High' : 'Ultra High'})
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="4"
                                step="1"
                                value={scale}
                                onChange={(e) => setScale(parseInt(e.target.value))}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>1x</span>
                                <span>2x</span>
                                <span>3x</span>
                                <span>4x</span>
                            </div>
                        </div>

                        {/* PNG 质量 */}
                        {selectedFormat === 'png' && (
                            <div>
                                <label className="text-xs text-gray-600 block mb-1">
                                    Quality: {Math.round(quality * 100)}%
                                </label>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="1"
                                    step="0.05"
                                    value={quality}
                                    onChange={(e) => setQuality(parseFloat(e.target.value))}
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                />
                            </div>
                        )}

                        {/* 背景颜色 */}
                        <div>
                            <label className="text-xs text-gray-600 block mb-1">Background Color</label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="color"
                                    value={backgroundColor}
                                    onChange={(e) => setBackgroundColor(e.target.value)}
                                    className="w-12 h-8 rounded cursor-pointer border border-gray-300"
                                />
                                <input
                                    type="text"
                                    value={backgroundColor}
                                    onChange={(e) => setBackgroundColor(e.target.value)}
                                    className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded"
                                    placeholder="#ffffff"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* JSON 导出选项 */}
                {selectedFormat === 'json' && (
                    <div className="space-y-2 pt-2 border-t border-gray-200">
                        <h3 className="font-medium text-gray-700 text-sm">JSON Options</h3>

                        <label className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                            <input
                                type="checkbox"
                                checked={includeLayout}
                                onChange={(e) => setIncludeLayout(e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span className="text-sm">Include layout positions</span>
                        </label>

                        <label className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                            <input
                                type="checkbox"
                                checked={includeStyles}
                                onChange={(e) => setIncludeStyles(e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span className="text-sm">Include node styles</span>
                        </label>
                    </div>
                )}

                {/* 导出按钮 */}
                <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className={`w-full py-2 px-4 rounded-lg font-medium transition-colors cursor-pointer ${isExporting
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                >
                    {isExporting ? (
                        <div className="flex items-center justify-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Exporting...</span>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            <span>Export as {selectedFormat.toUpperCase()}</span>
                        </div>
                    )}
                </button>

                {/* 导入功能（仅 JSON） */}
                {onImport && (
                    <div className="pt-3 border-t border-gray-200">
                        <h3 className="font-medium text-gray-700 text-sm mb-2">Import Graph</h3>
                        <label className="block">
                            <input
                                type="file"
                                accept=".json"
                                onChange={handleImport}
                                className="hidden"
                                id="import-file"
                            />
                            <div className="w-full py-2 px-4 rounded-lg font-medium border-2 border-dashed border-gray-300 hover:border-blue-500 text-gray-700 hover:text-blue-600 transition-colors cursor-pointer text-center">
                                <div className="flex items-center justify-center gap-2">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                    <span className="text-sm">Import JSON</span>
                                </div>
                            </div>
                        </label>
                    </div>
                )}

                {/* 说明文字 */}
                <div className="pt-2 border-t border-gray-200">
                    <div className="text-xs text-gray-500 space-y-1">
                        <p><strong>PNG:</strong> Raster image, best for presentations</p>
                        <p><strong>SVG:</strong> Vector image, scalable and editable</p>
                        <p><strong>JSON:</strong> Graph data with layout, can be re-imported</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExportPanel;

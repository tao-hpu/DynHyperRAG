/**
 * Loading Indicator Component
 * 显示数据加载状态的指示器
 */

import { Loader2 } from 'lucide-react';

export interface LoadingIndicatorProps {
    isLoading: boolean;
    progress?: number; // 0-100
    message?: string;
    position?: 'top' | 'bottom' | 'center';
    size?: 'sm' | 'md' | 'lg';
}

export function LoadingIndicator({
    isLoading,
    progress,
    message = 'Loading...',
    position = 'top',
    size = 'md',
}: LoadingIndicatorProps) {
    if (!isLoading) return null;

    const positionClasses = {
        top: 'top-4 left-1/2 -translate-x-1/2',
        bottom: 'bottom-4 left-1/2 -translate-x-1/2',
        center: 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
    };

    const sizeClasses = {
        sm: 'text-sm py-2 px-3',
        md: 'text-base py-3 px-4',
        lg: 'text-lg py-4 px-6',
    };

    const iconSizes = {
        sm: 16,
        md: 20,
        lg: 24,
    };

    return (
        <div
            className={`fixed ${positionClasses[position]} z-50 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200 ${sizeClasses[size]} flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300`}
        >
            <Loader2 className="animate-spin text-blue-600" size={iconSizes[size]} />

            <div className="flex flex-col gap-1">
                <span className="font-medium text-gray-900">{message}</span>

                {progress !== undefined && (
                    <div className="flex items-center gap-2">
                        <div className="w-32 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-blue-600 transition-all duration-300 ease-out"
                                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                            />
                        </div>
                        <span className="text-xs text-gray-600 font-mono">
                            {Math.round(progress)}%
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * Mini Loading Indicator (for inline use)
 */
export function MiniLoadingIndicator({
    message = 'Loading...',
}: {
    message?: string;
}) {
    return (
        <div className="flex items-center gap-2 text-sm text-gray-600">
            <Loader2 className="animate-spin" size={14} />
            <span>{message}</span>
        </div>
    );
}

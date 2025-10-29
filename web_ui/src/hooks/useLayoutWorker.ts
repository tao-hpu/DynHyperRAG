/**
 * useLayoutWorker Hook
 * React Hook for using the layout worker
 */

import { useRef, useCallback, useEffect } from 'react';
import type { LayoutWorkerMessage, LayoutWorkerResponse, LayoutOptions } from '@/workers/layoutWorker';

export interface UseLayoutWorkerResult {
  calculateLayout: (
    nodes: Array<{ id: string; x?: number; y?: number }>,
    edges: Array<{ source: string; target: string; weight?: number }>,
    options: LayoutOptions,
    callbacks?: {
      onProgress?: (progress: number) => void;
      onComplete?: (positions: Record<string, { x: number; y: number }>) => void;
      onError?: (error: string) => void;
    }
  ) => void;
  stopLayout: () => void;
  isCalculating: boolean;
}

export function useLayoutWorker(): UseLayoutWorkerResult {
  const workerRef = useRef<Worker | null>(null);
  const isCalculatingRef = useRef(false);
  const callbacksRef = useRef<{
    onProgress?: (progress: number) => void;
    onComplete?: (positions: Record<string, { x: number; y: number }>) => void;
    onError?: (error: string) => void;
  }>({});

  // 初始化 Worker
  useEffect(() => {
    // 创建 Worker
    try {
      workerRef.current = new Worker(
        new URL('../workers/layoutWorker.ts', import.meta.url),
        { type: 'module' }
      );

      // 设置消息处理器
      workerRef.current.onmessage = (event: MessageEvent<LayoutWorkerResponse>) => {
        const { type, data } = event.data;

        if (type === 'progress' && data?.progress !== undefined) {
          callbacksRef.current.onProgress?.(data.progress);
        } else if (type === 'complete' && data?.positions) {
          isCalculatingRef.current = false;
          callbacksRef.current.onComplete?.(data.positions);
        } else if (type === 'error' && data?.error) {
          isCalculatingRef.current = false;
          callbacksRef.current.onError?.(data.error);
        }
      };

      workerRef.current.onerror = (error) => {
        isCalculatingRef.current = false;
        callbacksRef.current.onError?.(error.message);
      };
    } catch (error) {
      console.error('Failed to create layout worker:', error);
    }

    // 清理函数
    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
        workerRef.current = null;
      }
    };
  }, []);

  const calculateLayout = useCallback(
    (
      nodes: Array<{ id: string; x?: number; y?: number }>,
      edges: Array<{ source: string; target: string; weight?: number }>,
      options: LayoutOptions,
      callbacks?: {
        onProgress?: (progress: number) => void;
        onComplete?: (positions: Record<string, { x: number; y: number }>) => void;
        onError?: (error: string) => void;
      }
    ) => {
      if (!workerRef.current) {
        callbacks?.onError?.('Worker not initialized');
        return;
      }

      if (isCalculatingRef.current) {
        console.warn('Layout calculation already in progress');
        return;
      }

      // 保存回调
      callbacksRef.current = callbacks || {};
      isCalculatingRef.current = true;

      // 发送计算消息
      const message: LayoutWorkerMessage = {
        type: 'calculate',
        data: { nodes, edges, options },
      };
      workerRef.current.postMessage(message);
    },
    []
  );

  const stopLayout = useCallback(() => {
    if (workerRef.current && isCalculatingRef.current) {
      const message: LayoutWorkerMessage = { type: 'stop' };
      workerRef.current.postMessage(message);
      isCalculatingRef.current = false;
    }
  }, []);

  return {
    calculateLayout,
    stopLayout,
    isCalculating: isCalculatingRef.current,
  };
}

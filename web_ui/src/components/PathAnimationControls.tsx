import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import type { QueryPath } from '@/types/query';

interface PathAnimationControlsProps {
    queryPath: QueryPath | null;
    onAnimationStep?: (currentStep: number, nodeId: string) => void;
    onAnimationComplete?: () => void;
}

const PathAnimationControls = ({
    queryPath,
    onAnimationStep,
    onAnimationComplete,
}: PathAnimationControlsProps) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [speed, setSpeed] = useState(1000); // milliseconds per step
    const [isPaused, setIsPaused] = useState(false);

    const totalSteps = queryPath?.nodes.length || 0;

    // Reset animation when query path changes
    useEffect(() => {
        setCurrentStep(0);
        setIsPlaying(false);
        setIsPaused(false);
    }, [queryPath]);

    // Animation loop
    useEffect(() => {
        if (!isPlaying || isPaused || !queryPath || currentStep >= totalSteps) {
            if (currentStep >= totalSteps && isPlaying) {
                setIsPlaying(false);
                if (onAnimationComplete) {
                    onAnimationComplete();
                }
            }
            return;
        }

        const timer = setTimeout(() => {
            const nextStep = currentStep + 1;
            setCurrentStep(nextStep);

            if (onAnimationStep && nextStep < totalSteps) {
                const nodeId = queryPath.nodes[nextStep];
                onAnimationStep(nextStep, nodeId);
            }

            if (nextStep >= totalSteps) {
                setIsPlaying(false);
                if (onAnimationComplete) {
                    onAnimationComplete();
                }
            }
        }, speed);

        return () => clearTimeout(timer);
    }, [isPlaying, isPaused, currentStep, speed, totalSteps, queryPath, onAnimationStep, onAnimationComplete]);

    const handlePlay = useCallback(() => {
        if (currentStep >= totalSteps) {
            setCurrentStep(0);
        }
        setIsPlaying(true);
        setIsPaused(false);
    }, [currentStep, totalSteps]);

    const handlePause = useCallback(() => {
        setIsPaused(true);
    }, []);

    const handleResume = useCallback(() => {
        setIsPaused(false);
    }, []);

    const handleReset = useCallback(() => {
        setCurrentStep(0);
        setIsPlaying(false);
        setIsPaused(false);
    }, []);

    const handleStepForward = useCallback(() => {
        if (currentStep < totalSteps - 1) {
            const nextStep = currentStep + 1;
            setCurrentStep(nextStep);
            if (onAnimationStep && queryPath) {
                const nodeId = queryPath.nodes[nextStep];
                onAnimationStep(nextStep, nodeId);
            }
        }
    }, [currentStep, totalSteps, queryPath, onAnimationStep]);

    const handleStepBackward = useCallback(() => {
        if (currentStep > 0) {
            const prevStep = currentStep - 1;
            setCurrentStep(prevStep);
            if (onAnimationStep && queryPath) {
                const nodeId = queryPath.nodes[prevStep];
                onAnimationStep(prevStep, nodeId);
            }
        }
    }, [currentStep, queryPath, onAnimationStep]);

    const handleSliderChange = useCallback((value: number[]) => {
        const newStep = value[0];
        setCurrentStep(newStep);
        if (onAnimationStep && queryPath && newStep < totalSteps) {
            const nodeId = queryPath.nodes[newStep];
            onAnimationStep(newStep, nodeId);
        }
    }, [queryPath, totalSteps, onAnimationStep]);

    if (!queryPath || totalSteps === 0) {
        return null;
    }

    const currentNodeId = currentStep < totalSteps ? queryPath.nodes[currentStep] : '';
    const currentScore = currentNodeId ? queryPath.scores[currentNodeId] : 0;

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between">
                <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Path Animation
                </h4>
                <div className="text-xs text-gray-500">
                    Step {currentStep + 1} / {totalSteps}
                </div>
            </div>

            {/* Progress bar */}
            <div className="space-y-2">
                <Slider
                    value={[currentStep]}
                    onValueChange={handleSliderChange}
                    max={totalSteps - 1}
                    step={1}
                    className="w-full"
                    disabled={isPlaying && !isPaused}
                />
                <div className="flex justify-between text-xs text-gray-500">
                    <span>Start</span>
                    <span>End</span>
                </div>
            </div>

            {/* Current step info */}
            {currentStep < totalSteps && (
                <div className="bg-purple-50 border border-purple-200 rounded p-3">
                    <div className="text-xs text-gray-600 mb-1">Current Node:</div>
                    <div className="font-mono text-sm text-gray-800 truncate" title={currentNodeId}>
                        {currentNodeId.replace(/"/g, '')}
                    </div>
                    {currentScore > 0 && (
                        <div className="mt-2 flex items-center gap-2">
                            <span className="text-xs text-gray-600">Relevance Score:</span>
                            <span className="text-sm font-semibold text-purple-600">
                                {currentScore.toFixed(3)}
                            </span>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-purple-600 h-2 rounded-full transition-all"
                                    style={{ width: `${currentScore * 100}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Control buttons */}
            <div className="flex items-center gap-2">
                {/* Step backward */}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStepBackward}
                    disabled={currentStep === 0 || (isPlaying && !isPaused)}
                    title="Step backward"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" />
                    </svg>
                </Button>

                {/* Play/Pause/Resume */}
                {!isPlaying || isPaused ? (
                    <Button
                        variant="default"
                        size="sm"
                        onClick={isPaused ? handleResume : handlePlay}
                        disabled={currentStep >= totalSteps && !isPaused}
                        className="flex-1"
                    >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {isPaused ? 'Resume' : currentStep >= totalSteps ? 'Replay' : 'Play'}
                    </Button>
                ) : (
                    <Button
                        variant="default"
                        size="sm"
                        onClick={handlePause}
                        className="flex-1"
                    >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Pause
                    </Button>
                )}

                {/* Step forward */}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStepForward}
                    disabled={currentStep >= totalSteps - 1 || (isPlaying && !isPaused)}
                    title="Step forward"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
                    </svg>
                </Button>

                {/* Reset */}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={handleReset}
                    disabled={currentStep === 0 && !isPlaying}
                    title="Reset"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </Button>
            </div>

            {/* Speed control */}
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-gray-700">Animation Speed</label>
                    <span className="text-xs text-gray-500">{(1000 / speed).toFixed(1)}x</span>
                </div>
                <Slider
                    value={[speed]}
                    onValueChange={(value) => setSpeed(value[0])}
                    min={200}
                    max={2000}
                    step={100}
                    className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                    <span>Fast (5x)</span>
                    <span>Slow (0.5x)</span>
                </div>
            </div>

            {/* Help text */}
            <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
                💡 Use the animation to see how the query traverses the knowledge graph step by step
            </div>
        </div>
    );
};

export default PathAnimationControls;

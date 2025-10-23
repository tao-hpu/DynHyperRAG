import { useState } from 'react';
import { useSettingsStore } from '@/stores/settingsStore';
import { colorSchemePresets } from '@/types/settings';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface SettingsPanelProps {
    onApply?: () => void;
}

export default function SettingsPanel({ onApply }: SettingsPanelProps) {
    const { settings, updateLayoutSettings, updateNodeSettings, applyColorSchemePreset, resetSettings } = useSettingsStore();
    const [isExpanded, setIsExpanded] = useState(false);

    const handleLayoutChange = (key: keyof typeof settings.layout, value: number) => {
        updateLayoutSettings({ [key]: value });
        if (onApply) {
            onApply();
        }
    };

    const handleNodeChange = (key: keyof typeof settings.node, value: number) => {
        updateNodeSettings({ [key]: value });
        if (onApply) {
            onApply();
        }
    };

    const handleColorSchemeChange = (presetName: string) => {
        applyColorSchemePreset(presetName as keyof typeof colorSchemePresets);
        if (onApply) {
            onApply();
        }
    };

    const handleReset = () => {
        resetSettings();
        if (onApply) {
            onApply();
        }
    };

    return (
        <Card className="bg-white rounded-lg shadow-lg">
            <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Settings
                    </h2>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                    >
                        <svg
                            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                </div>

                {isExpanded && (
                    <div className="space-y-6">
                        {/* Color Scheme */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Color Scheme
                            </label>
                            <Select
                                value={Object.keys(colorSchemePresets).find(
                                    key => JSON.stringify(colorSchemePresets[key as keyof typeof colorSchemePresets]) === JSON.stringify(settings.colorScheme)
                                ) || 'default'}
                                onValueChange={handleColorSchemeChange}
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue placeholder="Select color scheme" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="default">Default</SelectItem>
                                    <SelectItem value="vibrant">Vibrant</SelectItem>
                                    <SelectItem value="pastel">Pastel</SelectItem>
                                    <SelectItem value="monochrome">Monochrome</SelectItem>
                                </SelectContent>
                            </Select>

                            {/* Color Preview */}
                            <div className="mt-3 grid grid-cols-3 gap-2">
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.person }}
                                    />
                                    <span className="text-xs text-gray-600">Person</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.organization }}
                                    />
                                    <span className="text-xs text-gray-600">Org</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.location }}
                                    />
                                    <span className="text-xs text-gray-600">Location</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.event }}
                                    />
                                    <span className="text-xs text-gray-600">Event</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.concept }}
                                    />
                                    <span className="text-xs text-gray-600">Concept</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded"
                                        style={{ backgroundColor: settings.colorScheme.hyperedge }}
                                    />
                                    <span className="text-xs text-gray-600">Hyperedge</span>
                                </div>
                            </div>
                        </div>

                        {/* Node Settings */}
                        <div className="space-y-4">
                            <h3 className="text-sm font-medium text-gray-700">Node Appearance</h3>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Font Size: {settings.node.fontSize}px
                                </label>
                                <Slider
                                    value={[settings.node.fontSize]}
                                    onValueChange={([value]) => handleNodeChange('fontSize', value)}
                                    min={8}
                                    max={20}
                                    step={1}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Font Weight: {settings.node.fontWeight}
                                </label>
                                <Slider
                                    value={[settings.node.fontWeight]}
                                    onValueChange={([value]) => handleNodeChange('fontWeight', value)}
                                    min={300}
                                    max={700}
                                    step={100}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Min Node Size: {settings.node.minSize}px
                                </label>
                                <Slider
                                    value={[settings.node.minSize]}
                                    onValueChange={([value]) => handleNodeChange('minSize', value)}
                                    min={10}
                                    max={40}
                                    step={5}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Max Node Size: {settings.node.maxSize}px
                                </label>
                                <Slider
                                    value={[settings.node.maxSize]}
                                    onValueChange={([value]) => handleNodeChange('maxSize', value)}
                                    min={40}
                                    max={100}
                                    step={5}
                                    className="w-full"
                                />
                            </div>
                        </div>

                        {/* Layout Settings */}
                        <div className="space-y-4">
                            <h3 className="text-sm font-medium text-gray-700">Layout Parameters</h3>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Edge Length: {settings.layout.idealEdgeLength}
                                </label>
                                <Slider
                                    value={[settings.layout.idealEdgeLength]}
                                    onValueChange={([value]) => handleLayoutChange('idealEdgeLength', value)}
                                    min={50}
                                    max={300}
                                    step={10}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Node Repulsion: {settings.layout.nodeRepulsion}
                                </label>
                                <Slider
                                    value={[settings.layout.nodeRepulsion]}
                                    onValueChange={([value]) => handleLayoutChange('nodeRepulsion', value)}
                                    min={1000}
                                    max={15000}
                                    step={500}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Gravity: {settings.layout.gravity.toFixed(2)}
                                </label>
                                <Slider
                                    value={[settings.layout.gravity * 100]}
                                    onValueChange={([value]) => handleLayoutChange('gravity', value / 100)}
                                    min={0}
                                    max={100}
                                    step={5}
                                    className="w-full"
                                />
                            </div>

                            <div>
                                <label className="block text-xs text-gray-600 mb-2">
                                    Iterations: {settings.layout.numIter}
                                </label>
                                <Slider
                                    value={[settings.layout.numIter]}
                                    onValueChange={([value]) => handleLayoutChange('numIter', value)}
                                    min={500}
                                    max={5000}
                                    step={250}
                                    className="w-full"
                                />
                            </div>
                        </div>

                        {/* Reset Button */}
                        <div className="pt-4 border-t">
                            <Button
                                onClick={handleReset}
                                variant="outline"
                                className="w-full"
                            >
                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                Reset to Defaults
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </Card>
    );
}

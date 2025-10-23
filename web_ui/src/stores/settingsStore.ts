import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { VisualizationSettings, ColorScheme } from '@/types/settings';
import { defaultSettings, colorSchemePresets } from '@/types/settings';

interface SettingsState {
  settings: VisualizationSettings;
  
  // Actions
  updateLayoutSettings: (layout: Partial<VisualizationSettings['layout']>) => void;
  updateNodeSettings: (node: Partial<VisualizationSettings['node']>) => void;
  updateColorScheme: (colorScheme: Partial<ColorScheme>) => void;
  applyColorSchemePreset: (presetName: keyof typeof colorSchemePresets) => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      
      updateLayoutSettings: (layout) => set((state) => ({
        settings: {
          ...state.settings,
          layout: { ...state.settings.layout, ...layout },
        },
      })),
      
      updateNodeSettings: (node) => set((state) => ({
        settings: {
          ...state.settings,
          node: { ...state.settings.node, ...node },
        },
      })),
      
      updateColorScheme: (colorScheme) => set((state) => ({
        settings: {
          ...state.settings,
          colorScheme: { ...state.settings.colorScheme, ...colorScheme },
        },
      })),
      
      applyColorSchemePreset: (presetName) => set((state) => ({
        settings: {
          ...state.settings,
          colorScheme: colorSchemePresets[presetName],
        },
      })),
      
      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'visualization-settings',
    }
  )
);

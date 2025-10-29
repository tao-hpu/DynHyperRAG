import { useState } from 'react';
import type { GraphFilter } from '@/types/graph';

interface FilterPanelProps {
  onFilterChange: (filter: GraphFilter) => void;
  availableTypes: string[];
}

const FilterPanel = ({ onFilterChange, availableTypes }: FilterPanelProps) => {
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [minWeight, setMinWeight] = useState(0);
  const [maxWeight, setMaxWeight] = useState(20);  // 调整为 20 以适应实际数据范围

  const handleTypeToggle = (type: string) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter(t => t !== type)
      : [...selectedTypes, type];

    setSelectedTypes(newTypes);
    onFilterChange({
      entityTypes: newTypes,
      minWeight,
      maxWeight
    });
  };

  const handleWeightChange = (min: number, max: number) => {
    setMinWeight(min);
    setMaxWeight(max);
    onFilterChange({
      entityTypes: selectedTypes,
      minWeight: min,
      maxWeight: max
    });
  };

  const handleReset = () => {
    setSelectedTypes([]);
    setMinWeight(0);
    setMaxWeight(20);
    onFilterChange({
      entityTypes: [],
      minWeight: 0,
      maxWeight: 20
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium text-gray-700">Entity Types</h3>
          {selectedTypes.length > 0 && (
            <button
              onClick={handleReset}
              className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
          {availableTypes.map((type) => (
            <label
              key={type}
              className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
            >
              <input
                type="checkbox"
                checked={selectedTypes.includes(type)}
                onChange={() => handleTypeToggle(type)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm capitalize">{type.toLowerCase()}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-medium text-gray-700 mb-2">Edge Weight</h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600">Min: {minWeight.toFixed(1)}</label>
            <input
              type="range"
              min="0"
              max="20"
              step="0.5"
              value={minWeight}
              onChange={(e) => handleWeightChange(parseFloat(e.target.value), maxWeight)}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <div>
            <label className="text-xs text-gray-600">Max: {maxWeight.toFixed(1)}</label>
            <input
              type="range"
              min="0"
              max="20"
              step="0.5"
              value={maxWeight}
              onChange={(e) => handleWeightChange(minWeight, parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>
      </div>

      {(selectedTypes.length > 0 || minWeight > 0 || maxWeight < 20) && (
        <div className="pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-600">
            Active filters: {selectedTypes.length > 0 && `${selectedTypes.length} types`}
            {selectedTypes.length > 0 && (minWeight > 0 || maxWeight < 20) && ', '}
            {(minWeight > 0 || maxWeight < 20) && `weight ${minWeight.toFixed(1)}-${maxWeight.toFixed(1)}`}
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;

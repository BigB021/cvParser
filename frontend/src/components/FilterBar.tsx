import { useState } from 'react';
import type { FilterOptions } from '../api/resume';
import {
  Search,
  Plus,
  Minus,
  X,
  MapPin,
  GraduationCap,
  BadgeInfo,
  SlidersHorizontal,
  FilterX,
  Pickaxe
} from 'lucide-react';

interface FilterBarProps {
  onFilter: (filters: FilterOptions) => void;
}

const degrees = [
  '',
  'Baccalaureate',
  'DUT',
  'BTS',
  'Licence',
  'Master',
  'Doctorate',
  'Engineer',
  'Technician',
];

const FilterBar: React.FC<FilterBarProps> = ({ onFilter }) => {
  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');
  const [degree, setDegree] = useState('');
  const [skill, setSkill] = useState('');
  const [minExp, setMinExp] = useState<number | ''>('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilter({
      keyword: keyword.trim() || undefined,
      city: city.trim() || undefined,
      degree: degree || undefined,
      skill: skill.trim() || undefined,
      min_exp: minExp === '' ? undefined : Number(minExp),
    });
  };

  const handleClear = () => {
    setKeyword('');
    setCity('');
    setDegree('');
    setSkill('');
    setMinExp('');
    onFilter({});
  };

  const hasActiveFilters = keyword || city || degree || skill || minExp !== '';

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-lg overflow-hidden mb-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Search className="text-white mr-3" size={28} />
            <div>
              <h3 className="text-xl font-bold text-white">Search & Filter</h3>
              <p className="text-indigo-100 text-sm">Find the perfect candidate</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="bg-white/20 text-white px-3 py-2 rounded-lg hover:bg-white/30 transition-colors duration-200 flex items-center"
          >
            {isExpanded ? <Minus className="mr-2" /> : <Plus className="mr-2" />}
            {isExpanded ? 'Less' : 'More'}
          </button>
        </div>
      </div>

      {/* Filter Form */}
      <form onSubmit={handleSubmit} className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          {/* Keyword */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center">
              <BadgeInfo className="mr-2" size={24} />
              Keyword
            </label>
            <div className="relative">
              <input
                type="text"
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                placeholder="Name, occupation, status..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 bg-gray-50 hover:bg-white"
              />
              {keyword && (
                <button
                  type="button"
                  onClick={() => setKeyword('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-red-500"
                >
                  <X />
                </button>
              )}
            </div>
          </div>

          {/* Location */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center">
              <MapPin className="mr-2" size={24} />
              Location
            </label>
            <div className="relative">
              <input
                type="text"
                value={city}
                onChange={e => setCity(e.target.value)}
                placeholder="Enter city name"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 bg-gray-50 hover:bg-white"
              />
              {city && (
                <button
                  type="button"
                  onClick={() => setCity('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-red-500"
                >
                  <X />
                </button>
              )}
            </div>
          </div>

          {/* Experience */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center">
              <SlidersHorizontal className="mr-2" size={24} />
              Min. Experience
            </label>
            <div className="relative">
              <input
                type="number"
                min={0}
                value={minExp}
                onChange={e =>
                  setMinExp(e.target.value === '' ? '' : Number(e.target.value))
                }
                placeholder="Years"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 bg-gray-50 hover:bg-white"
              />
              <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 text-sm">
                years
              </span>
            </div>
          </div>
        </div>

        {/* Advanced Filters (Always toggleable) */}
        <div
          className={`grid grid-cols-1 md:grid-cols-2 gap-4 transition-all duration-300 ${
            isExpanded ? 'mb-6' : 'max-h-0 overflow-hidden'
          }`}
        >
          {/* Degree */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center">
              <GraduationCap className="mr-2" size={24} />
              Education Level
            </label>
            <div className="relative">
              <select
                value={degree}
                onChange={e => setDegree(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 bg-gray-50 hover:bg-white appearance-none"
              >
                {degrees.map(d => (
                  <option key={d} value={d}>
                    {d || 'Any Degree'}
                  </option>
                ))}
              </select>
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 pointer-events-none">
                ⌄
              </div>
            </div>
          </div>

          {/* Skill */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700 flex items-center">
              <Pickaxe className="mr-2" size={24} />
              <span className="ml-2">Skill</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={skill}
                onChange={e => setSkill(e.target.value)}
                placeholder="Enter skill name"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 bg-gray-50 hover:bg-white"
              />
              {skill && (
                <button
                  type="button"
                  onClick={() => setSkill('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-red-500"
                >
                  <X />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="submit"
            className="flex-1 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 focus:ring-2 focus:ring-indigo-500 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 flex items-center justify-center"
          >
            <Search className="mr-2" size={18} />
            Search Resumes
          </button>

          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClear}
              className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:border-red-300 hover:text-red-600 hover:bg-red-50 focus:ring-2 focus:ring-red-500 flex items-center justify-center"
            >
              <FilterX className="mr-2" size={18} />
              Clear All
            </button>
          )}
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-700 mb-2 flex items-center">
              <BadgeInfo className="mr-2" size={24} />
              Active Filters:
            </p>
            <div className="flex flex-wrap gap-2">
              {keyword && (
                <FilterTag label="Keyword" value={keyword} onRemove={() => setKeyword('')} />
              )}
              {city && (
                <FilterTag label="City" value={city} onRemove={() => setCity('')} />
              )}
              {degree && (
                <FilterTag label="Degree" value={degree} onRemove={() => setDegree('')} />
              )}
              {skill && (
                <FilterTag label="Skill" value={skill} onRemove={() => setSkill('')} />
              )}
              {minExp !== '' && (
                <FilterTag
                  label="Min Experience"
                  value={`${minExp} years`}
                  onRemove={() => setMinExp('')}
                />
              )}
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

const FilterTag: React.FC<{ label: string; value: string; onRemove: () => void }> = ({
  label,
  value,
  onRemove,
}) => (
  <span className="inline-flex items-center bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-medium border border-indigo-200">
    <span className="mr-1">{label}:</span>
    <span className="font-semibold">{value}</span>
    <button
      onClick={onRemove}
      className="ml-2 text-indigo-600 hover:text-red-600 transition-colors duration-200"
    >
      <X size={14} />
    </button>
  </span>
);

export default FilterBar;

import { useState } from 'react';
import type { FilterOptions } from '../api/resume';

interface FilterBarProps {
    onFilter: (filters: FilterOptions) => void;
}

const degrees = [
    '',
    'High School',
    'Associate',
    'Bachelor',
    'Master',
    'PhD',
];

const FilterBar: React.FC<FilterBarProps> = ({ onFilter }) => {
    const [keyword, setKeyword] = useState('');
    const [city, setCity] = useState('');
    const [degree, setDegree] = useState('');
    const [minExp, setMinExp] = useState<number | ''>('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onFilter({
            keyword: keyword.trim() || undefined,
            city: city.trim() || undefined,
            degree: degree || undefined,
            min_exp: minExp === '' ? undefined : Number(minExp),
        });
    };

    return (
        <form
            className="flex flex-wrap gap-4 items-end bg-white p-4 rounded shadow"
            onSubmit={handleSubmit}
        >
            <div>
                <label className="block text-sm font-medium mb-1">Keyword</label>
                <input
                    type="text"
                    value={keyword}
                    onChange={e => setKeyword(e.target.value)}
                    placeholder="Name, occupation..."
                    className="border rounded px-2 py-1 w-40"
                />
            </div>
            <div>
                <label className="block text-sm font-medium mb-1">City</label>
                <input
                    type="text"
                    value={city}
                    onChange={e => setCity(e.target.value)}
                    placeholder="City"
                    className="border rounded px-2 py-1 w-32"
                />
            </div>
            <div>
                <label className="block text-sm font-medium mb-1">Degree</label>
                <select
                    value={degree}
                    onChange={e => setDegree(e.target.value)}
                    className="border rounded px-2 py-1 w-32"
                >
                    {degrees.map(d => (
                        <option key={d} value={d}>
                            {d || 'Any'}
                        </option>
                    ))}
                </select>
            </div>
            <div>
                <label className="block text-sm font-medium mb-1">Min. Experience (years)</label>
                <input
                    type="number"
                    min={0}
                    value={minExp}
                    onChange={e =>
                        setMinExp(e.target.value === '' ? '' : Number(e.target.value))
                    }
                    placeholder="0"
                    className="border rounded px-2 py-1 w-20"
                />
            </div>
            <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
                Filter
            </button>
        </form>
    );
};

export default FilterBar;

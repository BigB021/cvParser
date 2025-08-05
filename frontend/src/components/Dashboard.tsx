// Dashboard.tsx
import { useEffect, useState } from 'react';
import { fetchAllResumes, filterResumes } from '../api/resume';
import type { Resume} from '../types/resume';
import type{ FilterOptions } from '../api/resume';
import ResumeCard from './ResumeCard';
import UploadForm from './UploadForm';
import FilterBar from './FilterBar';

const Dashboard = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [allResumes, setAllResumes] = useState<Resume[]>([]);

  useEffect(() => {
    fetchAllResumes().then(data => {
      setResumes(data);
      setAllResumes(data);
    }).catch(console.error);
  }, []);

  const handleFilter = async (filters: FilterOptions) => {
    try {
      const filtered = await filterResumes(filters);
      setResumes(filtered);
    } catch (err) {
      console.error('Filter error:', err);
    }
  };

  const handleAddResume = (newResume: Resume) => {
    setResumes(prev => [newResume, ...prev]);
    setAllResumes(prev => [newResume, ...prev]);
  };

  const handleDeleteResume = (id: number) => {
    setResumes(prev => prev.filter(r => r.id !== id));
    setAllResumes(prev => prev.filter(r => r.id !== id));
  };

  // Calculate stats
  const totalResumes = allResumes.length;
  const filteredCount = resumes.length;
  const uniqueCities = new Set(allResumes.map(r => r.city).filter(Boolean)).size;
  const uniqueSkills = new Set(allResumes.flatMap(r => r.skills || [])).size;

  return (
    <div className="p-4 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
          <div className="text-2xl font-bold text-blue-600">{totalResumes}</div>
          <div className="text-sm text-blue-700">Total Resumes</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-100">
          <div className="text-2xl font-bold text-green-600">{filteredCount}</div>
          <div className="text-sm text-green-700">Showing</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-100">
          <div className="text-2xl font-bold text-purple-600">{uniqueCities}</div>
          <div className="text-sm text-purple-700">Cities</div>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
          <div className="text-2xl font-bold text-orange-600">{uniqueSkills}</div>
          <div className="text-sm text-orange-700">Skills</div>
        </div>
      </div>

      <FilterBar onFilter={handleFilter} />
      <UploadForm onUploadSuccess={handleAddResume}/>
      
      <div className="grid gap-4 justify-center">
        {resumes.map(resume => (
          <ResumeCard key={resume.id} resume={resume} onDelete={handleDeleteResume} />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
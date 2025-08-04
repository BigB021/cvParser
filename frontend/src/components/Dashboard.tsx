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

  useEffect(() => {
    fetchAllResumes().then(setResumes).catch(console.error);
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
  };

  const handleDeleteResume = (id: number) => {
    setResumes(prev => prev.filter(r => r.id !== id));
  };

  return (
    <div className="p-4 space-y-4">
      <FilterBar onFilter={handleFilter} />
      <UploadForm  onUploadSuccess={handleAddResume}/>
      <div className="grid gap-4 justify-center">
        {resumes.map(resume => (
          
          <ResumeCard key={resume.id} resume={resume} onDelete={handleDeleteResume} />
        ))}
      </div>
    </div>
  );
};

export default Dashboard;

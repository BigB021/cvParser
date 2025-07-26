import './App.css'
import { useState, useEffect } from 'react'
import type { Resume } from './types/resume';

const API_BASE = import.meta.env.VITE_API_BASE;

function App() {
  const [datas, setData] = useState<Resume[]>([])

  useEffect(() => {
    fetch(`${API_BASE}/resumes/`)
      .then(res => res.json())
      .then(data => {
      setData(data.data); // assuming backend returns { data: [...] }
      console.log("data:", data);
      })
      .catch(err => console.error("Fetch error:", err));
  }, []);

  return (
    <div>
      <h1>Resume List</h1>
      <pre>{JSON.stringify(datas, null, 2)}</pre>
    </div>
  );
}

export default App

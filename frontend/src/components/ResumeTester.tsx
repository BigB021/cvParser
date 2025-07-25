import { useState, type ChangeEvent, useEffect } from "react";
import axios from "axios";

interface Resume {
  id: number;
  name: string;
  email: string;
  city: string;
  degree: string;
  experience: number;
  // Add other fields as needed
}

interface FilterParams {
  keyword: string;
  city: string;
  degree: string;
  min_exp: string;
}

const API_BASE = "http://127.0.0.1:5000/resumes";

const ResumeTester = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [filterParams, setFilterParams] = useState<FilterParams>({
    keyword: "",
    city: "",
    degree: "",
    min_exp: "",
  });
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  // Fetch all resumes on mount
  useEffect(() => {
    fetchAllResumes();
  }, []);

  const fetchAllResumes = async () => {
    try {
      const res = await axios.get(`${API_BASE}/`);
      setResumes(res.data.data || []);
      setStatus("Fetched all resumes");
      setError("");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err));
      }
      setStatus("");
    }
  };

  const handleFilterChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFilterParams((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const filterResumes = async () => {
    try {
      const params = new URLSearchParams();

      if (filterParams.keyword) params.append("keyword", filterParams.keyword);
      if (filterParams.city) params.append("city", filterParams.city);
      if (filterParams.degree) params.append("degree", filterParams.degree);
      if (filterParams.min_exp) params.append("min_exp", filterParams.min_exp);

      const res = await axios.get(`${API_BASE}/filter`, { params });
      setResumes(res.data.data || []);
      setStatus("Filtered resumes fetched");
      setError("");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err));
      }
      setStatus("");
    }
  };

  return (
    <div>
      <h2>Resume Filter Test</h2>

      <div style={{ marginBottom: 12 }}>
        <input
          name="keyword"
          placeholder="Keyword"
          value={filterParams.keyword}
          onChange={handleFilterChange}
          style={{ marginRight: 6 }}
        />
        <input
          name="city"
          placeholder="City"
          value={filterParams.city}
          onChange={handleFilterChange}
          style={{ marginRight: 6 }}
        />
        <input
          name="degree"
          placeholder="Degree"
          value={filterParams.degree}
          onChange={handleFilterChange}
          style={{ marginRight: 6 }}
        />
        <input
          name="min_exp"
          placeholder="Min Experience"
          value={filterParams.min_exp}
          onChange={handleFilterChange}
          type="number"
          style={{ width: 120 }}
        />
        <button onClick={filterResumes} style={{ marginLeft: 10 }}>
          Filter
        </button>
      </div>

      {status && <p style={{ color: "green" }}>{status}</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <ul>
        {resumes.length === 0 && <li>No resumes found</li>}
        {resumes.map((resume) => (
          <li key={resume.id}>
            {resume.name} — {resume.email} — {resume.city} — {resume.degree} —{" "}
            {resume.experience} yrs
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ResumeTester;

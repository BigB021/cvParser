import React, { useState } from 'react';
import { uploadResume } from '../api/resume';
import type { Resume } from '../types/resume';

const UploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedResume, setUploadedResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(e.target.files?.[0] || null);
    setUploadedResume(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a PDF resume to upload.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const resume = await uploadResume(selectedFile);
      setUploadedResume(resume);
      setSelectedFile(null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to upload resume.');
      } else {
        setError('Failed to upload resume.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded-xl shadow-md max-w-lg mx-auto bg-white">
      <h2 className="text-xl font-semibold mb-3">Upload New Resume</h2>
      <input
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        className="mb-2"
      />
      <button
        onClick={handleUpload}
        disabled={loading || !selectedFile}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Uploading...' : 'Upload'}
      </button>

      {error && <p className="text-red-500 mt-3">{error}</p>}

      {uploadedResume && (
        <div className="mt-4 text-sm text-left">
          <h3 className="font-medium text-green-600">Upload Successful!</h3>
          <p><strong>Name:</strong> {uploadedResume.name}</p>
          <p><strong>Email:</strong> {uploadedResume.email}</p>
          <p><strong>Phone:</strong> {uploadedResume.phone}</p>
          <p><strong>City:</strong> {uploadedResume.city}</p>
          <p><strong>Occupation:</strong> {uploadedResume.occupation}</p>
          <p><strong>Experience:</strong> {uploadedResume.exp_years} years</p>
          <p><strong>Status:</strong> {uploadedResume.status}</p>
          <p><strong>Degrees:</strong> {uploadedResume.degrees.join(', ')}</p>
          <p><strong>Skills:</strong> {uploadedResume.skills.join(', ')}</p>
          <a
            href={uploadedResume.pdf_path}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline"
          >
            View PDF
          </a>
        </div>
      )}
    </div>
  );
};

export default UploadForm;

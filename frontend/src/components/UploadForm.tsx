import React, { useState } from 'react';
import { uploadResume } from '../api/resume';
import type { Resume } from '../types/resume';
import {
  FilePlus, Upload, Trash2, FileCheck, FileDown, FolderOpen,
  User, Briefcase, MapPin, Clock, Mail, Phone, GraduationCap, Wrench
} from 'lucide-react';

interface UploadFormProps {
  onUploadSuccess?: (resume: Resume) => void;
}

const UploadForm: React.FC<UploadFormProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedResume, setUploadedResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(e.target.files?.[0] || null);
    setUploadedResume(null);
    setError(null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setUploadedResume(null);
      setError(null);
    } else {
      setError('Please select a PDF file only.');
    }
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
      if (onUploadSuccess) onUploadSuccess(resume);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-xl max-w-2xl mx-auto overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FilePlus className="mr-3 w-6 h-6" />
          Upload New Resume
        </h2>
        <p className="text-blue-100 mt-1">Drag and drop or browse to upload a PDF resume</p>
      </div>

      <div className="p-6 space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
            dragActive
              ? 'border-blue-500 bg-blue-50 scale-105'
              : selectedFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
          }`}
        >
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="file-upload"
          />

          <div className="space-y-4 text-gray-600">
            <div className="flex justify-center text-5xl">
              {selectedFile ? <FileCheck className="text-green-500 w-10 h-10" /> : dragActive ? <FileDown className="w-10 h-10" /> : <FolderOpen className="w-10 h-10" />}
            </div>

            {selectedFile ? (
              <div className="space-y-2">
                <p className="text-lg font-semibold text-green-700">File Selected!</p>
                <div className="bg-white rounded-lg p-3 border border-green-200 inline-block">
                  <p className="text-sm font-medium text-gray-800">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-lg font-semibold">
                  {dragActive ? 'Drop your file here' : 'Choose your PDF resume'}
                </p>
                <p className="text-sm text-gray-500">
                  Drag and drop or{' '}
                  <label htmlFor="file-upload" className="text-blue-600 hover:text-blue-800 cursor-pointer underline">
                    browse files
                  </label>
                </p>
                <p className="text-xs text-gray-400">PDF files only, max 10MB</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleUpload}
            disabled={loading || !selectedFile}
            className={`flex-1 flex items-center justify-center px-6 py-4 rounded-xl font-semibold text-white transition-all duration-300 transform ${
              loading || !selectedFile
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:scale-105 shadow-lg hover:shadow-xl'
            }`}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5 mr-2" />
                Upload Resume
              </>
            )}
          </button>

          {selectedFile && (
            <button
              onClick={() => {
                setSelectedFile(null);
                setError(null);
                setUploadedResume(null);
              }}
              className="px-4 py-4 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors duration-200"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start">
            <Trash2 className="text-red-500 w-5 h-5 mr-3" />
            <div>
              <p className="text-red-800 font-medium">Upload Failed</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {uploadedResume && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 space-y-4">
            <div className="flex items-center">
              <FileCheck className="text-green-600 w-6 h-6 mr-3" />
              <div>
                <h3 className="font-bold text-green-800 text-lg">Upload Successful!</h3>
                <p className="text-green-600 text-sm">Resume has been processed and added to the system</p>
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border border-green-200 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <InfoItem label="Name" value={uploadedResume.name} icon={<User className="w-4 h-4" />} />
                <InfoItem label="Occupation" value={uploadedResume.occupation} icon={<Briefcase className="w-4 h-4" />} />
                <InfoItem label="City" value={uploadedResume.city} icon={<MapPin className="w-4 h-4" />} />
                <InfoItem label="Experience" value={`${uploadedResume.exp_years} years`} icon={<Clock className="w-4 h-4" />} />
              </div>

              <div className="space-y-3">
                <InfoItem label="Email" value={uploadedResume.email} icon={<Mail className="w-4 h-4" />} />
                <InfoItem label="Phone" value={uploadedResume.phone} icon={<Phone className="w-4 h-4" />} />

                {uploadedResume.degrees.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                      <GraduationCap className="w-4 h-4 mr-2" />
                      Education
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {uploadedResume.degrees.map((degree, index) => (
                        <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                          {typeof degree === 'object' ? `${degree.degree_type} in ${degree.degree_subject}` : degree}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {uploadedResume.skills.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                      <Wrench className="w-4 h-4 mr-2" />
                      Skills
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {uploadedResume.skills.map((skill, index) => (
                        <span key={index} className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const InfoItem: React.FC<{ label: string; value: string; icon: React.ReactNode }> = ({ label, value, icon }) => (
  <div className="flex items-center space-x-2">
    <div className="text-gray-500">{icon}</div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium text-gray-600">{label}</p>
      <p className="text-sm font-semibold text-gray-900 truncate">{value}</p>
    </div>
  </div>
);

export default UploadForm;

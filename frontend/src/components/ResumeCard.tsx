import React from 'react';
import type { Resume } from '../types/resume';
import { getPdfUrl } from '../api/resume';
import axios from 'axios';

interface ResumeCardProps {
    resume: Resume;
    onDelete?: (id: number) => void;
}

const statusStyles: Record<string, string> = {
    accepted: 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-green-200',
    rejected: 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-red-200',
    pending: 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-amber-200',
};

export const ResumeCard: React.FC<ResumeCardProps> = ({ resume, onDelete }) => {
    const {
        id,
        name,
        email,
        phone,
        occupation,
        exp_years,
        city,
        status,
        pdf_path,
        degrees,
        skills
    } = resume;

    const canAccessPDF = pdf_path && pdf_path.trim() !== '';
    const pdfUrl = canAccessPDF ? getPdfUrl(pdf_path) : '';
    
    const handleDelete = async () => {
        if (!window.confirm(`Are you sure you want to delete ${name}'s resume?`)) return;

        try {
            await axios.delete(`http://localhost:5000/resumes/${id}`);
            if (onDelete) onDelete(id);
        } catch (error) {
            alert('Failed to delete resume.');
            console.error(error);
        }
    };

    return (
        <div className="group bg-white border border-gray-200 rounded-2xl p-6 my-4 shadow-lg hover:shadow-2xl transition-all duration-300 max-w-md mx-auto sm:mx-0 hover:-translate-y-1 relative overflow-hidden">
            {/* Decorative gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-transparent to-purple-50/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            
            {/* Content */}
            <div className="relative z-10">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-6">
                    <div className="flex-1">
                        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight mb-1 group-hover:text-blue-900 transition-colors duration-300">
                            {name}
                        </h2>
                        <p className="text-gray-600 font-medium text-lg">{occupation}</p>
                    </div>
                    <span
                        className={`px-4 py-2 rounded-full text-sm font-semibold capitalize inline-block self-start shadow-lg ${
                            statusStyles[status] || 'bg-gray-500 text-white shadow-gray-200'
                        } ${statusStyles[status]?.includes('shadow-') ? 'shadow-lg' : ''}`}
                    >
                        {status}
                    </span>
                </div>

                {/* Key Info Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                    <InfoCard 
                        icon="📍"
                        label="Location"
                        value={city}
                    />
                    <InfoCard 
                        icon="⏱️"
                        label="Experience"
                        value={`${exp_years} ${exp_years === 1 ? 'year' : 'years'}`}
                    />
                </div>

                {/* Contact Information */}
                <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-4 mb-6 border border-gray-100">
                    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3 flex items-center">
                        <span className="mr-2">📞</span>
                        Contact Information
                    </h3>
                    <div className="space-y-3">
                        <ContactDetail
                            icon="✉️"
                            value={
                                <a
                                    href={`mailto:${email}`}
                                    className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200 break-all font-medium"
                                >
                                    {email}
                                </a>
                            }
                        />
                        <ContactDetail
                            icon="📱"
                            value={
                                <a
                                    href={`tel:${phone}`}
                                    className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200 font-medium"
                                >
                                    {phone}
                                </a>
                            }
                        />
                    </div>
                </div>
                
                {/* Degrees */}
                {degrees.length > 0 && (
                    <div className="mb-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                            <span className="mr-2">🎓</span>
                            Education
                        </h3>
                        <div className="space-y-2">
                            {degrees.map((degree, index) => (
                                <div key={index} className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-3 border-l-4 border-indigo-400">
                                    <span className="text-gray-800 font-medium">
                                        {degree.degree_type} in {degree.degree_subject}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Skills */}
                {skills.length > 0 && (
                    <div className="mb-6">
                        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                            <span className="mr-2">🛠️</span>
                            Skills
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {skills.map((skill, index) => (
                                <span
                                    key={index}
                                    className="inline-block bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium border border-blue-200 hover:from-blue-200 hover:to-indigo-200 transition-colors duration-200"
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="pt-6 border-t border-gray-200 flex gap-3 flex-wrap">
                    {canAccessPDF ? (
                        <>
                            <a
                                href={pdfUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex-1 sm:flex-none inline-flex items-center justify-center px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                            >
                                <span className="mr-2">👀</span>
                                View PDF
                            </a>
                            <a
                                href={pdfUrl}
                                download
                                className="flex-1 sm:flex-none inline-flex items-center justify-center px-6 py-3 text-sm font-semibold text-blue-700 bg-white border-2 border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                            >
                                <span className="mr-2">💾</span>
                                Download
                            </a>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center px-4 py-3 bg-red-50 border border-red-200 rounded-lg">
                            <span className="text-red-600 text-sm font-medium flex items-center">
                                <span className="mr-2">❌</span>
                                No PDF available
                            </span>
                        </div>
                    )}

                    <button
                        onClick={handleDelete}
                        className="inline-flex items-center justify-center px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-red-600 to-red-700 rounded-lg hover:from-red-700 hover:to-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    >
                        <span className="mr-2">🗑️</span>
                        Delete
                    </button>
                </div>
            </div>
        </div>
    );
};

const InfoCard: React.FC<{ icon: string; label: string; value: string }> = ({ icon, label, value }) => (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
        <div className="flex items-center">
            <span className="text-2xl mr-3">{icon}</span>
            <div>
                <p className="text-sm font-medium text-gray-600">{label}</p>
                <p className="text-lg font-semibold text-gray-900">{value}</p>
            </div>
        </div>
    </div>
);

const ContactDetail: React.FC<{ icon: string; value: React.ReactNode }> = ({ icon, value }) => (
    <div className="flex items-center">
        <span className="text-lg mr-3">{icon}</span>
        <div className="flex-1">{value}</div>
    </div>
);

export default ResumeCard;
import React from 'react';
import type { Resume } from '../types/resume';
import { getPdfUrl } from '../api/resume';

interface ResumeCardProps {
    resume: Resume;
}

const statusStyles: Record<string, string> = {
    accepted: 'bg-green-500 text-white',
    rejected: 'bg-red-500 text-white',
    pending: 'bg-orange-500 text-white',
};

export const ResumeCard: React.FC<ResumeCardProps> = ({ resume }) => {
    const {
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

    return (
        <div className="bg-white border border-gray-200 rounded-xl p-4 sm:p-6 my-4 shadow-sm hover:shadow-md transition-shadow duration-200 max-w-md mx-auto sm:mx-0">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 mb-4">
                <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 leading-tight">
                    {name}
                </h2>
                <span
                    className={`px-3 py-1 rounded-full text-sm font-medium capitalize inline-block self-start ${
                        statusStyles[status] || 'bg-gray-500 text-white'
                    }`}
                >
                    {status}
                </span>
            </div>

            {/* Details */}
            <div className="space-y-3 text-sm sm:text-base">
                <Detail label="Occupation" value={occupation} />
                <Detail
                    label="Experience"
                    value={`${exp_years} ${exp_years === 1 ? 'year' : 'years'}`}
                />
                <Detail label="City" value={city} />
                <Detail
                    label="Email"
                    value={
                        <a
                            href={`mailto:${email}`}
                            className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200 break-all"
                        >
                            {email}
                        </a>
                    }
                />
                <Detail
                    label="Phone"
                    value={
                        <a
                            href={`tel:${phone}`}
                            className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200"
                        >
                            {phone}
                        </a>
                    }
                />
            </div>
            
            {/* Degrees */}
            {degrees.length > 0 && (
                <div className="mt-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Degrees</h3>
                    <ul className="list-disc list-inside space-y-1">
                        {degrees.map((degree, index) => (
                            <li key={index} className="text-gray-700">
                                {degree.degree_type} in {degree.degree_subject}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Skills */}
            {skills.length > 0 && (
                <div className="mt-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Skills</h3>
                    <ul className="list-disc list-inside space-y-1">
                        {skills.map((skill, index) => (
                            <li key={index} className="text-gray-700">
                                {skill}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* PDF Actions */}
            <div className="mt-6 pt-4 border-t border-gray-100 flex gap-3 flex-wrap">
                {canAccessPDF ? (
                    <>
                        <a
                            href={pdfUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                            View PDF
                        </a>
                        <a
                            href={pdfUrl}
                            download
                            className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-400 rounded-lg hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                        >
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1M12 12v6m0 0l-3-3m3 3l3-3M12 4v8"
                                />
                            </svg>
                            Download PDF
                        </a>
                    </>
                ) : (
                    <span className="text-red-500 text-sm italic">No PDF available</span>
                )}
            </div>
        </div>
    );
};

const Detail: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
    <div className="flex flex-col sm:flex-row sm:items-center">
        <span className="font-semibold text-gray-700 min-w-fit pr-2">{label}:</span>
        <span className="text-gray-600">{value}</span>
    </div>
);

export default ResumeCard;

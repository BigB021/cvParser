// src/api/resume.ts
import type { Resume } from '../types/resume';

const API_BASE = import.meta.env.VITE_API_BASE;

export async function fetchAllResumes(): Promise<Resume[]> {
  const res = await fetch(`${API_BASE}/resumes/`);
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function fetchResumeById(id: number): Promise<Resume> {
  const res = await fetch(`${API_BASE}/resumes/${id}`);
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function fetchResumeByEmail(email: string): Promise<Resume> {
  const res = await fetch(`${API_BASE}/resumes/email/${encodeURIComponent(email)}`);
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function searchResumeByName(name: string): Promise<Resume[]> {
  const res = await fetch(`${API_BASE}/resumes/search?name=${encodeURIComponent(name)}`);
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function createResume(resume: Omit<Resume, 'id'>): Promise<Resume> {
  const res = await fetch(`${API_BASE}/resumes/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resume),
  });
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function deleteResume(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/resumes/${id}`, {
    method: 'DELETE',
  });
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
}

export interface FilterOptions {
  keyword?: string;
  city?: string;
  degree?: string;
  min_exp?: number;
}

export async function filterResumes(options: FilterOptions): Promise<Resume[]> {
  const params = new URLSearchParams();
  if (options.keyword) params.append('keyword', options.keyword);
  if (options.city) params.append('city', options.city);
  if (options.degree) params.append('degree', options.degree);
  if (options.min_exp !== undefined) params.append('min_exp', String(options.min_exp));

  const res = await fetch(`${API_BASE}/resumes/filter?${params.toString()}`);
  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export async function uploadResume(file: File): Promise<Resume> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/resumes/upload`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (data.status !== 'success') throw new Error(data.message);
  return data.data;
}

export function getPdfUrl(pdfFilename: string): string {
  return `${API_BASE}/resumes/pdfs/${encodeURIComponent(pdfFilename)}`;
}

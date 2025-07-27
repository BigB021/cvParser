export interface Resume {
  id: number;
  name: string;
  email: string;
  phone: string;
  occupation: string;
  exp_years: number;
  city: string;
  status: string;
  pdf_path: string;
  degrees: {
    degree_type: string;
    degree_subject: string;
  }[];
  skills: string[];
}

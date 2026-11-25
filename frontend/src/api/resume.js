import api from './client';

export const resumeApi = {
  uploadResume: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listResumes: async () => {
    const response = await api.get('/resumes/');
    return response.data;
  },

  getResume: async (resumeId) => {
    const response = await api.get(`/resumes/${resumeId}`);
    return response.data;
  },

  deleteResume: async (resumeId) => {
    const response = await api.delete(`/resumes/${resumeId}`);
    return response.data;
  },
};

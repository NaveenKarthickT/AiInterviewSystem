import api from './client';

export const reportApi = {
  getReport: async (sessionId) => {
    const response = await api.get(`/reports/${sessionId}`);
    return response.data;
  },

  listReports: async () => {
    const response = await api.get('/reports/history');
    return response.data;
  },
};

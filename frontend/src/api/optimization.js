import api from './client';

export const optimizationApi = {
  getOptimization: async (sessionId) => {
    const response = await api.get(`/optimization/${sessionId}`);
    return response.data;
  },

  approveAndCompile: async (optimizationId, items, customSummary = null) => {
    const response = await api.post(`/optimization/${optimizationId}/approve`, {
      items,
      custom_summary: customSummary,
    });
    return response.data;
  },

  downloadExportedFile: async (optimizationId, format = 'pdf') => {
    const response = await api.get(`/optimization/${optimizationId}/export/${format}`, {
      responseType: 'blob',
    });
    const mimeType =
      format === 'pdf'
        ? 'application/pdf'
        : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    const blob = new Blob([response.data], { type: mimeType });
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `ATS_Resume_${optimizationId.slice(0, 8)}.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => window.URL.revokeObjectURL(downloadUrl), 1000);
  },

  getExportUrl: (optimizationId, format = 'pdf') => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const token = localStorage.getItem('token');
    const query = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${baseUrl}/optimization/${optimizationId}/export/${format}${query}`;
  },
};

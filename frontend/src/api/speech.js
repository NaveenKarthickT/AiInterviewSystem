import api from './client';

export const speechApi = {
  transcribeAudio: async (audioBlob, filename = 'recording.webm') => {
    const formData = new FormData();
    formData.append('file', audioBlob, filename);
    const response = await api.post('/speech/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  synthesizeAudio: async (text, voice = 'alloy') => {
    const response = await api.post(
      '/speech/synthesize',
      { text, voice },
      { responseType: 'blob' }
    );
    return response.data;
  },
};

import api from './client';

export const interviewApi = {
  createSession: async (data) => {
    const response = await api.post('/interviews/', data);
    return response.data;
  },

  listSessions: async () => {
    const response = await api.get('/interviews/');
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/interviews/${sessionId}`);
    return response.data;
  },

  getCurrentTurn: async (sessionId) => {
    const response = await api.get(`/interviews/${sessionId}/current-turn`);
    return response.data;
  },

  submitAnswer: async (sessionId, turnId, candidateAnswer, audioUrl = null) => {
    const response = await api.post(`/interviews/${sessionId}/turns/${turnId}/submit`, {
      candidate_answer: candidateAnswer,
      audio_answer_url: audioUrl,
    });
    return response.data;
  },

  getTurnEvaluation: async (sessionId, turnId) => {
    const response = await api.get(`/interviews/${sessionId}/turns/${turnId}/evaluation`);
    return response.data;
  },
};

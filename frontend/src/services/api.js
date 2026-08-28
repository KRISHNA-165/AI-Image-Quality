import axios from 'axios';

const API_BASE = '/api/v1';

export const api = {
  async healthCheck() {
    const res = await axios.get(`${API_BASE}/health`);
    return res.data;
  },

  async getModelInfo() {
    const res = await axios.get(`${API_BASE}/model-info`);
    return res.data;
  },

  async analyzeImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post(`${API_BASE}/analyze`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async analyzeBatch(files) {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const res = await axios.post(`${API_BASE}/analyze/batch`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async getAnalyses(page = 1, limit = 10, label = null, search = null) {
    const params = { page, limit };
    if (label) params.label = label;
    if (search) params.search = search;
    const res = await axios.get(`${API_BASE}/analyses`, { params });
    return res.data;
  },

  async getAnalysisById(id) {
    const res = await axios.get(`${API_BASE}/analyses/${id}`);
    return res.data;
  },

  async deleteAnalysis(id) {
    await axios.delete(`${API_BASE}/analyses/${id}`);
  }
};

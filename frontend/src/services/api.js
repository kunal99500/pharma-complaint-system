/**
 * api.js — Centralized API service layer
 * Creates a pre-configured axios instance, handles errors centrally,
 * and exports named functions for every backend endpoint.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
});

// Unwrap .data and convert errors to human-readable messages
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'Unexpected error';
    return Promise.reject(new Error(message));
  }
);

// ── Complaints ───────────────────────────────────────────────────────────────
export const complaintsApi = {
  create:     (data)          => api.post('/complaints/', data),
  uploadFile: (file)          => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/complaints/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },
  list:   (filters = {}) => {
    const params = new URLSearchParams(
      Object.entries(filters).filter(([, v]) => v != null)
    );
    return api.get(`/complaints/?${params}`);
  },
  getById: (id)      => api.get(`/complaints/${id}`),
  update:  (id, upd) => api.patch(`/complaints/${id}`, upd),
  delete:  (id)      => api.delete(`/complaints/${id}`),
};

// ── Analysis ─────────────────────────────────────────────────────────────────
export const analysisApi = {
  analyze:   (complaintId, force = false) =>
    api.post('/analysis/analyze', { complaint_id: complaintId, force_reanalyze: force }),
  getResult: (complaintId) => api.get(`/analysis/${complaintId}`),
};

export default api;
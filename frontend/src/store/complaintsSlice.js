/**
 * complaintsSlice.js — Redux Toolkit slice for all complaint state
 *
 * What this file does:
 * - Defines the shape of the complaints state in the Redux store
 * - Creates async thunks (fetchComplaints, createComplaint, analyzeComplaint, etc.)
 *   Thunks are functions that make async API calls and dispatch actions automatically
 * - Creates reducers (pure functions) that update state in response to actions
 * - Exports actions and selectors for use in components
 *
 * Why Redux?
 * - Multiple components need the same complaint data (list + form + copilot panel)
 * - Complaint state is complex (loading states, errors, selected complaint, analysis)
 * - Redux keeps all of this in one predictable place instead of prop-drilling
 *
 * Redux Toolkit (RTK) simplifies Redux:
 * - createAsyncThunk handles pending/fulfilled/rejected states automatically
 * - createSlice generates actions and reducers from one object
 * - Immer (built into RTK) lets us write "mutating" state updates safely
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { complaintsApi, analysisApi } from '../services/api';

// ── Async Thunks ─────────────────────────────────────────────────────────────
// Each thunk = one API call
// RTK auto-creates action types: "complaints/fetch/pending", "fulfilled", "rejected"

export const fetchComplaints = createAsyncThunk(
  'complaints/fetchAll',
  async (filters, { rejectWithValue }) => {
    try {
      return await complaintsApi.list(filters);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const fetchComplaint = createAsyncThunk(
  'complaints/fetchOne',
  async (id, { rejectWithValue }) => {
    try {
      return await complaintsApi.getById(id);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const createComplaint = createAsyncThunk(
  'complaints/create',
  async (data, { rejectWithValue }) => {
    try {
      return await complaintsApi.create(data);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const uploadComplaintFile = createAsyncThunk(
  'complaints/uploadFile',
  async (file, { rejectWithValue }) => {
    try {
      return await complaintsApi.uploadFile(file);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const updateComplaint = createAsyncThunk(
  'complaints/update',
  async ({ id, updates }, { rejectWithValue }) => {
    try {
      return await complaintsApi.update(id, updates);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const analyzeComplaint = createAsyncThunk(
  'complaints/analyze',
  async ({ complaintId, force = false }, { rejectWithValue }) => {
    try {
      return await analysisApi.analyze(complaintId, force);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const deleteComplaint = createAsyncThunk(
  'complaints/delete',
  async (id, { rejectWithValue }) => {
    try {
      await complaintsApi.delete(id);
      return id; // Return the ID so we can remove it from state
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);


// ── Initial State ─────────────────────────────────────────────────────────────

const initialState = {
  // List view state
  complaints:      [],          // Array of ComplaintListItem objects
  listLoading:     false,
  listError:       null,

  // Selected complaint (detail view / edit form)
  selectedComplaint: null,      // Full ComplaintResponse object
  detailLoading:     false,
  detailError:       null,

  // Form state (for the "Log Complaint" form)
  formLoading:  false,
  formError:    null,

  // AI analysis state
  analyzing:       false,       // True while LangGraph agent is running
  analysisError:   null,
  lastAnalysis:    null,        // Latest AnalyzeResponse

  // Filters for the list view
  filters: {
    status:     null,
    risk_level: null,
  },
};


// ── Slice ─────────────────────────────────────────────────────────────────────

const complaintsSlice = createSlice({
  name: 'complaints',
  initialState,

  reducers: {
    // Synchronous actions (no API calls)

    setFilters: (state, action) => {
      // Update filter values and reset to first page
      state.filters = { ...state.filters, ...action.payload };
    },

    clearSelectedComplaint: (state) => {
      state.selectedComplaint = null;
      state.lastAnalysis      = null;
      state.detailError       = null;
    },

    clearErrors: (state) => {
      state.listError     = null;
      state.detailError   = null;
      state.formError     = null;
      state.analysisError = null;
    },

    // Optimistically update a field in the selected complaint
    // (used when user edits form fields before saving)
    updateSelectedField: (state, action) => {
      if (state.selectedComplaint) {
        const { field, value } = action.payload;
        state.selectedComplaint[field] = value;
      }
    },
  },

  // extraReducers handle the actions from async thunks
  extraReducers: (builder) => {

    // ── Fetch all complaints ──
    builder
      .addCase(fetchComplaints.pending, (state) => {
        state.listLoading = true;
        state.listError   = null;
      })
      .addCase(fetchComplaints.fulfilled, (state, action) => {
        state.listLoading = false;
        state.complaints  = action.payload;
      })
      .addCase(fetchComplaints.rejected, (state, action) => {
        state.listLoading = false;
        state.listError   = action.payload;
      });

    // ── Fetch single complaint ──
    builder
      .addCase(fetchComplaint.pending, (state) => {
        state.detailLoading = true;
        state.detailError   = null;
      })
      .addCase(fetchComplaint.fulfilled, (state, action) => {
        state.detailLoading    = false;
        state.selectedComplaint = action.payload;
      })
      .addCase(fetchComplaint.rejected, (state, action) => {
        state.detailLoading = false;
        state.detailError   = action.payload;
      });

    // ── Create complaint ──
    builder
      .addCase(createComplaint.pending, (state) => {
        state.formLoading = true;
        state.formError   = null;
      })
      .addCase(createComplaint.fulfilled, (state, action) => {
        state.formLoading      = false;
        state.selectedComplaint = action.payload;
        // Add to top of list
        state.complaints.unshift({
          id:               action.payload.id,
          complaint_number: action.payload.complaint_number,
          customer_name:    action.payload.customer_name,
          product_name:     action.payload.product_name,
          status:           action.payload.status,
          risk_level:       action.payload.risk_level,
          ai_processed:     action.payload.ai_processed,
          created_at:       action.payload.created_at,
        });
      })
      .addCase(createComplaint.rejected, (state, action) => {
        state.formLoading = false;
        state.formError   = action.payload;
      });

    // ── Upload file ──
    builder
      .addCase(uploadComplaintFile.pending, (state) => {
        state.formLoading = true;
        state.formError   = null;
      })
      .addCase(uploadComplaintFile.fulfilled, (state, action) => {
        state.formLoading      = false;
        state.selectedComplaint = action.payload;
      })
      .addCase(uploadComplaintFile.rejected, (state, action) => {
        state.formLoading = false;
        state.formError   = action.payload;
      });

    // ── Update complaint ──
    builder
      .addCase(updateComplaint.fulfilled, (state, action) => {
        state.selectedComplaint = action.payload;
        // Update in list too
        const idx = state.complaints.findIndex(c => c.id === action.payload.id);
        if (idx !== -1) {
          state.complaints[idx] = {
            ...state.complaints[idx],
            status:      action.payload.status,
            risk_level:  action.payload.risk_level,
            product_name: action.payload.product_name,
            customer_name: action.payload.customer_name,
          };
        }
      });

    // ── AI Analysis ──
    builder
      .addCase(analyzeComplaint.pending, (state) => {
        state.analyzing     = true;
        state.analysisError = null;
      })
      .addCase(analyzeComplaint.fulfilled, (state, action) => {
        state.analyzing  = false;
        state.lastAnalysis = action.payload;

        // Update the selected complaint with AI-filled fields
        if (state.selectedComplaint && action.payload.analysis) {
          const analysis = action.payload.analysis;
          // Only fill fields that were empty
          if (!state.selectedComplaint.product_name && analysis.extracted_product_name) {
            state.selectedComplaint.product_name = analysis.extracted_product_name;
          }
          if (!state.selectedComplaint.batch_number && analysis.extracted_batch_number) {
            state.selectedComplaint.batch_number = analysis.extracted_batch_number;
          }
          if (!state.selectedComplaint.customer_name && analysis.extracted_customer_name) {
            state.selectedComplaint.customer_name = analysis.extracted_customer_name;
          }
          if (!state.selectedComplaint.complaint_description && analysis.extracted_description) {
            state.selectedComplaint.complaint_description = analysis.extracted_description;
          }
          // Always set risk level from AI
          state.selectedComplaint.risk_level  = analysis.classified_risk || state.selectedComplaint.risk_level;
          state.selectedComplaint.ai_processed = true;
          state.selectedComplaint.analysis     = analysis;
          state.selectedComplaint.capa_actions = action.payload.capa_actions || [];
        }
      })
      .addCase(analyzeComplaint.rejected, (state, action) => {
        state.analyzing     = false;
        state.analysisError = action.payload;
      });

    // ── Delete complaint ──
    builder
      .addCase(deleteComplaint.fulfilled, (state, action) => {
        state.complaints = state.complaints.filter(c => c.id !== action.payload);
        if (state.selectedComplaint?.id === action.payload) {
          state.selectedComplaint = null;
        }
      });
  },
});

export const {
  setFilters,
  clearSelectedComplaint,
  clearErrors,
  updateSelectedField,
} = complaintsSlice.actions;

// ── Selectors ─────────────────────────────────────────────────────────────────
// Selectors are functions that extract specific data from the Redux store
// Keeping them here means components don't need to know the state shape

export const selectComplaints       = (state) => state.complaints.complaints;
export const selectListLoading      = (state) => state.complaints.listLoading;
export const selectListError        = (state) => state.complaints.listError;
export const selectSelectedComplaint = (state) => state.complaints.selectedComplaint;
export const selectDetailLoading    = (state) => state.complaints.detailLoading;
export const selectAnalyzing        = (state) => state.complaints.analyzing;
export const selectAnalysisError    = (state) => state.complaints.analysisError;
export const selectLastAnalysis     = (state) => state.complaints.lastAnalysis;
export const selectFormLoading      = (state) => state.complaints.formLoading;
export const selectFilters          = (state) => state.complaints.filters;

export default complaintsSlice.reducer;
/**
 * ComplaintList.jsx — Tabular view of all complaints
 *
 * Features:
 * - Filterable by status and risk level
 * - Color-coded risk badges (Critical = red, Major = orange, Minor = yellow)
 * - AI processed indicator
 * - Clickable rows to open complaint detail / edit form
 * - Auto-loads on mount, re-fetches when filters change
 */
import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  FileText, AlertTriangle, CheckCircle, Loader2,
  Filter, ChevronRight, Sparkles
} from 'lucide-react';

import {
  fetchComplaints,
  setFilters,
  selectComplaints,
  selectListLoading,
  selectListError,
  selectFilters,
} from '../store/complaintsSlice';

const RISK_STYLES = {
  critical: 'bg-red-500/20 text-red-300 border-red-500/30',
  major:    'bg-orange-500/20 text-orange-300 border-orange-500/30',
  minor:    'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  unknown:  'bg-slate-700 text-slate-400 border-slate-600',
};

const STATUS_STYLES = {
  received:     'bg-blue-500/20 text-blue-300 border-blue-500/30',
  under_review: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  capa_open:    'bg-orange-500/20 text-orange-300 border-orange-500/30',
  closed:       'bg-green-500/20 text-green-300 border-green-500/30',
  rejected:     'bg-slate-700 text-slate-400 border-slate-600',
};

export default function ComplaintList() {
  const dispatch    = useDispatch();
  const navigate    = useNavigate();
  const complaints  = useSelector(selectComplaints);
  const loading     = useSelector(selectListLoading);
  const error       = useSelector(selectListError);
  const filters     = useSelector(selectFilters);

  // Load complaints on mount + when filters change
  useEffect(() => {
    dispatch(fetchComplaints(filters));
  }, [dispatch, filters]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    dispatch(setFilters({ [name]: value || null }));
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 size={20} className="animate-spin" />
          <span>Loading complaints...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
        <div>
          <h1 className="text-lg font-semibold text-white">Complaint Register</h1>
          <p className="text-xs text-slate-400 mt-0.5">{complaints.length} complaints total</p>
        </div>
        {/* Filters */}
        <div className="flex items-center gap-3">
          <Filter size={14} className="text-slate-400" />
          <select
            name="status"
            value={filters.status || ''}
            onChange={handleFilterChange}
            className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="received">Received</option>
            <option value="under_review">Under Review</option>
            <option value="capa_open">CAPA Open</option>
            <option value="closed">Closed</option>
          </select>
          <select
            name="risk_level"
            value={filters.risk_level || ''}
            onChange={handleFilterChange}
            className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Risk Levels</option>
            <option value="critical">Critical</option>
            <option value="major">Major</option>
            <option value="minor">Minor</option>
          </select>
          <button
            onClick={() => navigate('/complaints/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            + New Complaint
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto p-6">
        {complaints.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <FileText size={32} className="text-slate-600 mb-3" />
            <p className="text-slate-400 font-medium">No complaints found</p>
            <p className="text-slate-500 text-sm mt-1">Create your first complaint to get started</p>
            <button
              onClick={() => navigate('/complaints/new')}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Log New Complaint
            </button>
          </div>
        ) : (
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-800/50">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Complaint #</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Customer</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Product</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Category</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Risk</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">AI</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {complaints.map((c, idx) => (
                  <tr
                    key={c.id}
                    onClick={() => navigate(`/complaints/${c.id}`)}
                    className={`border-b border-slate-800/50 hover:bg-slate-800/40 cursor-pointer transition-colors ${
                      idx % 2 === 0 ? 'bg-transparent' : 'bg-slate-800/20'
                    }`}
                  >
                    <td className="px-4 py-3">
                      <span className="text-blue-400 text-sm font-mono">{c.complaint_number}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">{c.customer_name || '—'}</td>
                    <td className="px-4 py-3 text-sm text-slate-300 max-w-[160px] truncate">{c.product_name || '—'}</td>
                    <td className="px-4 py-3 text-xs text-slate-400">{(c.category || 'other').replace('_', ' ')}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase border ${RISK_STYLES[c.risk_level] || RISK_STYLES.unknown}`}>
                        {c.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_STYLES[c.status] || STATUS_STYLES.received}`}>
                        {c.status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {c.ai_processed
                        ? <Sparkles size={13} className="text-purple-400" />
                        : <span className="text-slate-600 text-xs">—</span>
                      }
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <ChevronRight size={14} className="text-slate-600" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
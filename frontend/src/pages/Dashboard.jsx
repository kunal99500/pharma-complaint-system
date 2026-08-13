/**
 * Dashboard.jsx — Overview stats page
 * Shows KPI cards: total complaints, by risk level, and recent activity.
 */
import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { FileText, ShieldAlert, AlertTriangle, AlertCircle, Sparkles, Plus } from 'lucide-react';
import { fetchComplaints, selectComplaints, selectListLoading } from '../store/complaintsSlice';

function StatCard({ icon: Icon, label, value, color, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`bg-slate-900 border border-slate-800 rounded-xl p-5 cursor-pointer hover:border-slate-700 transition-colors ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-slate-400">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={16} className="text-white" />
        </div>
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const dispatch    = useDispatch();
  const navigate    = useNavigate();
  const complaints  = useSelector(selectComplaints);
  const loading     = useSelector(selectListLoading);

  useEffect(() => {
    dispatch(fetchComplaints({}));
  }, [dispatch]);

  const critical = complaints.filter(c => c.risk_level === 'critical').length;
  const major    = complaints.filter(c => c.risk_level === 'major').length;
  const minor    = complaints.filter(c => c.risk_level === 'minor').length;
  const aiDone   = complaints.filter(c => c.ai_processed).length;
  const recent   = [...complaints].slice(0, 5);

  return (
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">QMS Dashboard</h1>
          <p className="text-sm text-slate-400 mt-0.5">Pharmaceutical complaint management overview</p>
        </div>
        <button
          onClick={() => navigate('/complaints/new')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <Plus size={14} />
          Log Complaint
        </button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText}      label="Total Complaints"     value={complaints.length} color="bg-blue-600"   onClick={() => navigate('/complaints')} />
        <StatCard icon={ShieldAlert}   label="Critical Risk"        value={critical}          color="bg-red-600"    onClick={() => navigate('/complaints?risk=critical')} />
        <StatCard icon={AlertTriangle} label="Major Risk"           value={major}             color="bg-orange-600" />
        <StatCard icon={Sparkles}      label="AI Analyzed"          value={aiDone}            color="bg-purple-600" />
      </div>

      {/* Recent complaints */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300">Recent Complaints</h2>
          <button onClick={() => navigate('/complaints')} className="text-xs text-blue-400 hover:text-blue-300">
            View all →
          </button>
        </div>
        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Loading...</div>
        ) : recent.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">No complaints yet</div>
        ) : (
          <div className="divide-y divide-slate-800">
            {recent.map(c => (
              <div
                key={c.id}
                onClick={() => navigate(`/complaints/${c.id}`)}
                className="px-5 py-3 hover:bg-slate-800/40 cursor-pointer flex items-center gap-4 transition-colors"
              >
                <span className="text-blue-400 font-mono text-sm w-32 shrink-0">{c.complaint_number}</span>
                <span className="text-slate-300 text-sm flex-1">{c.product_name || 'Unknown product'}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase border ${
                  c.risk_level === 'critical' ? 'bg-red-500/20 text-red-300 border-red-500/30' :
                  c.risk_level === 'major'    ? 'bg-orange-500/20 text-orange-300 border-orange-500/30' :
                  c.risk_level === 'minor'    ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' :
                  'bg-slate-700 text-slate-400 border-slate-600'
                }`}>
                  {c.risk_level}
                </span>
                {c.ai_processed && <Sparkles size={12} className="text-purple-400 shrink-0" />}
                <span className="text-slate-500 text-xs shrink-0">{new Date(c.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
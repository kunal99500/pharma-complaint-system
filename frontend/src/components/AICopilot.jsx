/**
 * AICopilot.jsx — Left panel showing all AI analysis results
 *
 * Redesigned for the left column (300px wide):
 * - Compact risk badge at the top — most important info first
 * - Collapsible sections for summary, root cause, CAPA
 * - Tighter spacing to fit more content in the narrower column
 * - Duplicate warning and completeness check always visible (not collapsible)
 */
import React, { useState } from 'react';
import {
  Sparkles, AlertTriangle, CheckCircle, XCircle,
  Loader2, ShieldAlert, Brain, AlertCircle,
  Info, ClipboardCheck, ChevronDown, ChevronRight,
} from 'lucide-react';

// ── Risk config ───────────────────────────────────────────────────────────────
const RISK_CONFIG = {
  critical: {
    color:  'text-red-300',
    bg:     'bg-red-500/10 border-red-500/30',
    bar:    'bg-red-500',
    icon:   ShieldAlert,
    label:  'CRITICAL',
    desc:   'Patient safety risk — act immediately',
  },
  major: {
    color:  'text-orange-300',
    bg:     'bg-orange-500/10 border-orange-500/30',
    bar:    'bg-orange-500',
    icon:   AlertTriangle,
    label:  'MAJOR',
    desc:   'Quality impact — investigate within 30 days',
  },
  minor: {
    color:  'text-yellow-300',
    bg:     'bg-yellow-500/10 border-yellow-500/30',
    bar:    'bg-yellow-500',
    icon:   AlertCircle,
    label:  'MINOR',
    desc:   'Low risk — administrative action',
  },
  unknown: {
    color:  'text-slate-400',
    bg:     'bg-slate-800/60 border-slate-700',
    bar:    'bg-slate-600',
    icon:   Info,
    label:  'NOT ASSESSED',
    desc:   'Run AI analysis to classify',
  },
};

const PRIORITY_COLORS = {
  immediate:  'bg-red-500/20 text-red-300 border-red-500/30',
  short_term: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  long_term:  'bg-blue-500/20 text-blue-300 border-blue-500/30',
};

// ── Collapsible Section ───────────────────────────────────────────────────────
function Section({ title, icon: Icon, iconColor, children, defaultOpen = true, count }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={13} className={iconColor} />
          <span className="text-xs font-semibold text-slate-300">{title}</span>
          {count != null && (
            <span className="px-1.5 py-0.5 rounded-full bg-slate-700 text-slate-400 text-[10px]">
              {count}
            </span>
          )}
        </div>
        {open
          ? <ChevronDown size={12} className="text-slate-500" />
          : <ChevronRight size={12} className="text-slate-500" />
        }
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}


// ── Main Component ────────────────────────────────────────────────────────────
export default function AICopilot({ complaint, analyzing, error }) {
  const analysis    = complaint?.analysis;
  const capaActions = complaint?.capa_actions || [];

  // Safely parse JSON string fields from DB
  const missingFields  = (() => { try { return JSON.parse(analysis?.missing_fields || '[]'); } catch { return []; } })();
  const probableCauses = (() => { try { return JSON.parse(analysis?.probable_causes || '[]');  } catch { return []; } })();

  const correctiveActions = capaActions.filter(c => c.action_type === 'corrective');
  const preventiveActions = capaActions.filter(c => c.action_type === 'preventive');

  // ── Panel header (always shown) ─────────────────────────────────────────
  const PanelHeader = () => (
    <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
      <Sparkles size={14} className="text-purple-400" />
      <span className="text-sm font-semibold text-slate-300">AI Copilot</span>
      {analysis?.analyzed_at && (
        <span className="ml-auto text-[10px] text-slate-600">
          {new Date(analysis.analyzed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      )}
    </div>
  );

  // ── Empty state ─────────────────────────────────────────────────────────
  if (!analysis && !analyzing && !error) {
    return (
      <div className="h-full flex flex-col">
        <PanelHeader />
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4">
            <Sparkles size={24} className="text-purple-400" />
          </div>
          <h3 className="text-slate-300 text-sm font-semibold mb-2">Ready to Analyze</h3>
          <p className="text-slate-500 text-xs leading-relaxed mb-5">
            Enter complaint details on the right, then click{' '}
            <span className="text-purple-400 font-medium">Analyze with AI</span>
          </p>
          <div className="w-full space-y-2 text-left">
            {[
              'Extract fields from text or PDF',
              'Classify risk per ICH Q10',
              'Identify probable root causes',
              'Generate CAPA action plan',
              'Detect duplicate complaints',
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-slate-500">
                <CheckCircle size={11} className="text-purple-500 shrink-0" />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Loading state ───────────────────────────────────────────────────────
  if (analyzing) {
    return (
      <div className="h-full flex flex-col">
        <PanelHeader />
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="relative mb-4">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <Sparkles size={22} className="text-purple-400" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-slate-900 rounded-full flex items-center justify-center border border-slate-700">
              <Loader2 size={10} className="text-purple-400 animate-spin" />
            </div>
          </div>
          <p className="text-slate-300 text-sm font-semibold mb-4">Analyzing...</p>
          <div className="w-full space-y-2">
            {[
              'Extracting information...',
              'Classifying risk level...',
              'Checking completeness...',
              'Analyzing root cause...',
              'Generating CAPA...',
            ].map((step, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs text-slate-500 animate-pulse"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <Loader2 size={9} className="animate-spin shrink-0" />
                {step}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Error state ─────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="h-full flex flex-col">
        <PanelHeader />
        <div className="p-4">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3">
            <div className="flex items-center gap-2 mb-1.5">
              <XCircle size={13} className="text-red-400" />
              <span className="text-xs font-semibold text-red-300">Analysis Failed</span>
            </div>
            <p className="text-xs text-red-400/80 leading-relaxed">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  // ── Results state ───────────────────────────────────────────────────────
  const riskLevel  = analysis?.classified_risk || complaint?.risk_level || 'unknown';
  const riskConfig = RISK_CONFIG[riskLevel] || RISK_CONFIG.unknown;
  const RiskIcon   = riskConfig.icon;

  return (
    <div className="h-full flex flex-col">
      <PanelHeader />

      <div className="flex-1 overflow-y-auto p-3 space-y-3">

        {/* Risk Assessment Card */}
        <div className={`rounded-xl border p-3 ${riskConfig.bg}`}>
          {/* Color bar at top */}
          <div className={`h-1 rounded-full ${riskConfig.bar} mb-3 opacity-60`} />

          <div className="flex items-start gap-2.5">
            <RiskIcon size={18} className={`${riskConfig.color} shrink-0 mt-0.5`} />
            <div className="flex-1 min-w-0">
              <div className={`text-sm font-bold ${riskConfig.color}`}>{riskConfig.label}</div>
              <div className="text-xs text-slate-400 mt-0.5">{riskConfig.desc}</div>
            </div>
            {analysis?.extraction_confidence != null && (
              <div className="text-right shrink-0">
                <div className="text-[10px] text-slate-500">Confidence</div>
                <div className="text-sm font-bold text-slate-300">
                  {Math.round((analysis.extraction_confidence || 0) * 100)}%
                </div>
              </div>
            )}
          </div>

          {analysis?.classification_reasoning && (
            <p className="mt-2.5 text-xs text-slate-400 leading-relaxed border-t border-white/10 pt-2.5">
              {analysis.classification_reasoning}
            </p>
          )}
        </div>

        {/* Duplicate Warning */}
        {(analysis?.duplicate_score || 0) > 0.6 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-2.5">
            <div className="flex items-center gap-2">
              <AlertTriangle size={12} className="text-yellow-400 shrink-0" />
              <span className="text-xs font-medium text-yellow-300">
                {Math.round((analysis.duplicate_score || 0) * 100)}% similarity with existing complaint
              </span>
            </div>
          </div>
        )}

        {/* Completeness Check */}
        {analysis?.is_complete != null && (
          <div className={`rounded-xl border p-2.5 ${
            analysis.is_complete
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-orange-500/10 border-orange-500/30'
          }`}>
            <div className="flex items-center gap-2 mb-1">
              {analysis.is_complete
                ? <CheckCircle size={12} className="text-green-400" />
                : <AlertCircle size={12} className="text-orange-400" />
              }
              <span className={`text-xs font-semibold ${analysis.is_complete ? 'text-green-300' : 'text-orange-300'}`}>
                {analysis.is_complete ? 'Complete' : 'Missing fields'}
              </span>
            </div>
            {!analysis.is_complete && missingFields.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {missingFields.map(f => (
                  <span key={f} className="px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-300 text-[10px] border border-orange-500/20">
                    {f.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Executive Summary */}
        {analysis?.ai_summary && (
          <Section title="Summary" icon={Brain} iconColor="text-purple-400">
            <p className="text-xs text-slate-400 leading-relaxed">{analysis.ai_summary}</p>
          </Section>
        )}

        {/* Root Cause Analysis */}
        {analysis?.root_cause_analysis && (
          <Section title="Root Cause" icon={Brain} iconColor="text-blue-400">
            <p className="text-xs text-slate-400 leading-relaxed mb-3">
              {analysis.root_cause_analysis}
            </p>
            {probableCauses.length > 0 && (
              <div className="space-y-2">
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  Probable Causes
                </p>
                {probableCauses.map((cause, i) => (
                  <div key={i} className="bg-slate-800/60 rounded-lg p-2.5 border border-slate-700/60">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-slate-300">
                        {cause.category || 'Factor'}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                        cause.likelihood === 'high'
                          ? 'bg-red-500/20 text-red-300 border-red-500/20'
                          : cause.likelihood === 'medium'
                            ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/20'
                            : 'bg-slate-700 text-slate-400 border-slate-600'
                      }`}>
                        {cause.likelihood}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{cause.cause}</p>
                    {cause.investigation_step && (
                      <p className="text-[10px] text-slate-500 mt-1">→ {cause.investigation_step}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Section>
        )}

        {/* CAPA Actions */}
        {capaActions.length > 0 && (
          <Section
            title="CAPA Actions"
            icon={ClipboardCheck}
            iconColor="text-green-400"
            count={capaActions.length}
          >
            {/* Corrective */}
            {correctiveActions.length > 0 && (
              <div className="mb-3">
                <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">
                  Corrective
                </p>
                <div className="space-y-2">
                  {correctiveActions.map((action, i) => (
                    <div key={i} className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-2.5">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="text-xs font-medium text-slate-200 leading-tight">
                          {action.title}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${
                          PRIORITY_COLORS[action.priority] || 'bg-slate-700 text-slate-400 border-slate-600'
                        }`}>
                          {(action.priority || 'tbd').replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed mb-1.5">
                        {action.description}
                      </p>
                      <div className="text-[10px] text-slate-500 space-y-0.5">
                        <div>👤 {action.assigned_to || 'QA Department'}</div>
                        <div>📅 {action.due_date_suggestion || 'TBD'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Preventive */}
            {preventiveActions.length > 0 && (
              <div>
                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-wider mb-2">
                  Preventive
                </p>
                <div className="space-y-2">
                  {preventiveActions.map((action, i) => (
                    <div key={i} className="bg-slate-800/60 border border-slate-700/60 rounded-lg p-2.5">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <span className="text-xs font-medium text-slate-200 leading-tight">
                          {action.title}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${
                          PRIORITY_COLORS[action.priority] || 'bg-slate-700 text-slate-400 border-slate-600'
                        }`}>
                          {(action.priority || 'tbd').replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed mb-1.5">
                        {action.description}
                      </p>
                      <div className="text-[10px] text-slate-500 space-y-0.5">
                        <div>👤 {action.assigned_to || 'QA Department'}</div>
                        <div>📅 {action.due_date_suggestion || 'TBD'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Section>
        )}

      </div>
    </div>
  );
}
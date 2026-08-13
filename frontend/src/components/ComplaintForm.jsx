
import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Upload, Sparkles, Loader2, CheckCircle, FileText,
  User, Package, ClipboardList, Brain, Save,
  ChevronDown, ChevronUp, Hash, Send, Bot, Paperclip,
} from 'lucide-react';

import {
  createComplaint,
  uploadComplaintFile,
  analyzeComplaint,
  fetchComplaint,
  updateComplaint,
  selectSelectedComplaint,
  selectAnalyzing,
  selectAnalysisError,
  selectFormLoading,
  clearSelectedComplaint,
} from '../store/complaintsSlice';
import AICopilot from './AICopilot';

// ── Risk badge config ────────────────────────────────────────────────────────
const RISK_COLORS = {
  critical: 'bg-red-500/20 text-red-300 border-red-500/40',
  major:    'bg-orange-500/20 text-orange-300 border-orange-500/40',
  minor:    'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
  unknown:  'bg-slate-700 text-slate-400 border-slate-600',
};

// ── Reusable Field ───────────────────────────────────────────────────────────
function Field({ label, name, value, onChange, type = 'text', placeholder, className = '', required = false, aiField = false }) {
  return (
    <div className={className}>
      <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-1.5">
        {label}
        {required && <span className="text-red-400">*</span>}
        {aiField && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/20">
            AI
          </span>
        )}
      </label>
      <input
        type={type}
        name={name}
        value={value || ''}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full bg-slate-800/60 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-colors"
      />
    </div>
  );
}

// ── Reusable Select ──────────────────────────────────────────────────────────
function Select({ label, name, value, onChange, options, className = '' }) {
  return (
    <div className={className}>
      <label className="block text-xs font-medium text-slate-400 mb-1.5">{label}</label>
      <select
        name={name}
        value={value || ''}
        onChange={onChange}
        className="w-full bg-slate-800/60 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-colors appearance-none cursor-pointer"
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── Collapsible Section ──────────────────────────────────────────────────────
function FormSection({ icon: Icon, title, iconColor = 'text-slate-400', children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-slate-900/80 rounded-xl border border-slate-800 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={14} className={iconColor} />
          <span className="text-sm font-semibold text-slate-300">{title}</span>
        </div>
        {open
          ? <ChevronUp size={13} className="text-slate-500" />
          : <ChevronDown size={13} className="text-slate-500" />
        }
      </button>
      {open && <div className="px-4 pb-4 pt-1">{children}</div>}
    </div>
  );
}

// ── Chat Message Bubble ──────────────────────────────────────────────────────
function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isFile = message.type === 'file';

  return (
    <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mb-1 ${
        isUser ? 'bg-blue-600' : 'bg-purple-600'
      }`}>
        {isUser
          ? <User size={12} className="text-white" />
          : <Bot size={12} className="text-white" />
        }
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] rounded-2xl px-3 py-2 ${
        isUser
          ? 'bg-blue-600 text-white rounded-br-sm'
          : message.type === 'analyzing'
            ? 'bg-slate-800 border border-slate-700 text-slate-300 rounded-bl-sm'
            : message.type === 'success'
              ? 'bg-purple-500/20 border border-purple-500/30 text-purple-200 rounded-bl-sm'
              : message.type === 'error'
                ? 'bg-red-500/20 border border-red-500/30 text-red-300 rounded-bl-sm'
                : 'bg-slate-800 border border-slate-700 text-slate-300 rounded-bl-sm'
      }`}>
        {message.type === 'analyzing' ? (
          <div className="flex items-center gap-2">
            <Loader2 size={12} className="animate-spin text-purple-400" />
            <span className="text-xs">{message.content}</span>
          </div>
        ) : isFile ? (
          <div className="flex items-center gap-2">
            <FileText size={12} className="text-blue-200 shrink-0" />
            <span className="text-xs">{message.content}</span>
          </div>
        ) : (
          <p className="text-xs leading-relaxed">{message.content}</p>
        )}
        <p className={`text-[10px] mt-1 ${isUser ? 'text-blue-200' : 'text-slate-500'} text-right`}>
          {message.time}
        </p>
      </div>
    </div>
  );
}


// ── Main Component ───────────────────────────────────────────────────────────
export default function ComplaintForm() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { id }   = useParams();
  const fileRef  = useRef(null);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  const selectedComplaint = useSelector(selectSelectedComplaint);
  const analyzing         = useSelector(selectAnalyzing);
  const analysisError     = useSelector(selectAnalysisError);
  const formLoading       = useSelector(selectFormLoading);

  // Chat messages state
  const [messages, setMessages] = useState([
    {
      id:      1,
      role:    'assistant',
      type:    'normal',
      content: 'Hello! Describe the complaint or paste the full complaint email below. I\'ll extract all details and assess the risk automatically.',
      time:    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [inputText, setInputText]   = useState('');
  const [dragOver, setDragOver]     = useState(false);

  const [formData, setFormData] = useState({
    source_type:           'manual',
    raw_input:             '',
    customer_name:         '',
    customer_email:        '',
    customer_phone:        '',
    customer_company:      '',
    customer_country:      '',
    product_name:          '',
    batch_number:          '',
    manufacturing_date:    '',
    expiry_date:           '',
    quantity_affected:     '',
    complaint_description: '',
    date_of_complaint:     '',
    category:              'other',
  });

  // Auto scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load existing complaint
  useEffect(() => {
  if (id) {
    dispatch(fetchComplaint(id));
  } else {
    // Clear Redux state
    dispatch(clearSelectedComplaint());

    // Clear local form state
    setFormData({
      source_type: 'manual', raw_input: '',
      customer_name: '', customer_email: '', customer_phone: '',
      customer_company: '', customer_country: '',
      product_name: '', batch_number: '', manufacturing_date: '',
      expiry_date: '', quantity_affected: '',
      complaint_description: '', date_of_complaint: '', category: 'other',
    });

    // Reset chat to initial welcome message
    setMessages([{
      id:      1,
      role:    'assistant',
      type:    'normal',
      content: 'Hello! Describe the complaint or paste the full complaint email below. I\'ll extract all details and assess the risk automatically.',
      time:    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);

    // Clear text input
    setInputText('');
  }
}, [id, dispatch]);

  // Sync Redux state to form
  useEffect(() => {
    if (selectedComplaint) {
      setFormData(prev => ({
        ...prev,
        raw_input:             selectedComplaint.raw_input             || '',
        customer_name:         selectedComplaint.customer_name         || '',
        customer_email:        selectedComplaint.customer_email        || '',
        customer_phone:        selectedComplaint.customer_phone        || '',
        customer_company:      selectedComplaint.customer_company      || '',
        customer_country:      selectedComplaint.customer_country      || '',
        product_name:          selectedComplaint.product_name          || '',
        batch_number:          selectedComplaint.batch_number          || '',
        manufacturing_date:    selectedComplaint.manufacturing_date    || '',
        expiry_date:           selectedComplaint.expiry_date           || '',
        quantity_affected:     selectedComplaint.quantity_affected     || '',
        complaint_description: selectedComplaint.complaint_description || '',
        date_of_complaint:     selectedComplaint.date_of_complaint     || '',
        category:              selectedComplaint.category              || 'other',
      }));
    }
  }, [selectedComplaint]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const addMessage = (role, content, type = 'normal') => {
    setMessages(prev => [...prev, {
      id:      Date.now(),
      role,
      type,
      content,
      time:    new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  };

  // Send chat message and trigger analysis
  const handleSend = async () => {
    const text = inputText.trim();
    if (!text) return;

    // Add user message bubble
    addMessage('user', text);
    setInputText('');

    // Update raw_input in form
    setFormData(prev => ({ ...prev, raw_input: text }));

    // Add analyzing bubble
    addMessage('assistant', 'Analyzing your complaint...', 'analyzing');

    // Save complaint first if needed
    let complaintId = selectedComplaint?.id || id;
    if (!complaintId) {
      const saveResult = await dispatch(createComplaint({ ...formData, raw_input: text }));
      if (!createComplaint.fulfilled.match(saveResult)) {
        addMessage('assistant', 'Failed to save complaint. Please try again.', 'error');
        return;
      }
      complaintId = saveResult.payload.id;
      navigate(`/complaints/${complaintId}`);
    }

    // Run AI analysis
    const result = await dispatch(analyzeComplaint({ complaintId }));

    // Remove the analyzing message and add result
    setMessages(prev => prev.filter(m => m.type !== 'analyzing'));

    if (analyzeComplaint.fulfilled.match(result)) {
      const analysis = result.payload?.analysis;
      const risk     = analysis?.classified_risk || 'unknown';
      const product  = analysis?.extracted_product_name || 'the product';

      addMessage(
        'assistant',
        `Analysis complete. ${product} complaint classified as ${risk.toUpperCase()} risk. Form fields have been auto-filled. Check the left panel for full risk assessment, root cause, and CAPA actions.`,
        'success'
      );

      // Re-fetch to get latest data
      dispatch(fetchComplaint(complaintId));
      toast.success('Analysis complete');
    } else {
      addMessage('assistant', `Analysis failed: ${result.payload || 'Unknown error'}`, 'error');
      toast.error('Analysis failed');
    }
  };

  // Handle Enter key
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // File upload
  const handleFileDrop = async (file) => {
    if (!file) return;
    addMessage('user', `📎 ${file.name}`, 'file');
    addMessage('assistant', 'Processing file...', 'analyzing');

    const result = await dispatch(uploadComplaintFile(file));

    setMessages(prev => prev.filter(m => m.type !== 'analyzing'));

    if (uploadComplaintFile.fulfilled.match(result)) {
      const extractedText = result.payload.raw_input || '';
      setFormData(prev => ({ ...prev, raw_input: extractedText }));

      addMessage('assistant', `File processed successfully. Click Send or type a message to analyze.`, 'success');
      navigate(`/complaints/${result.payload.id}`);
      toast.success(`File uploaded: ${file.name}`);
    } else {
      addMessage('assistant', 'File upload failed. Please try again.', 'error');
      toast.error('Upload failed');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileDrop(file);
  };

  // Save complaint
  const handleSave = async () => {
    if (!formData.raw_input && !formData.complaint_description) {
      toast.error('Please enter complaint text first');
      return;
    }
    if (id && selectedComplaint) {
      const result = await dispatch(updateComplaint({ id, updates: formData }));
      if (updateComplaint.fulfilled.match(result)) toast.success('Complaint updated');
      else toast.error('Update failed: ' + result.payload);
    } else {
      const result = await dispatch(createComplaint(formData));
      if (createComplaint.fulfilled.match(result)) {
        toast.success('Saved: ' + result.payload.complaint_number);
        navigate(`/complaints/${result.payload.id}`);
      } else {
        toast.error('Save failed: ' + result.payload);
      }
    }
  };

  const isEditing = Boolean(id);
  const riskLevel = selectedComplaint?.risk_level || 'unknown';
  const analysis  = selectedComplaint?.analysis;

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-950">

      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="shrink-0 px-6 py-3 border-b border-slate-800 bg-slate-900/60 flex items-center gap-4">
        <div className="flex items-center gap-3 flex-1">
          {isEditing && selectedComplaint?.complaint_number && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 rounded-lg border border-slate-700">
              <Hash size={12} className="text-slate-400" />
              <span className="text-sm font-mono font-semibold text-blue-400">
                {selectedComplaint.complaint_number}
              </span>
            </div>
          )}
          <div>
            <h1 className="text-base font-semibold text-white leading-none">
              {isEditing ? 'Edit Complaint' : 'Log Customer Complaint'}
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              {isEditing ? 'Review and update complaint details' : 'Create a new QMS complaint record'}
            </p>
          </div>
        </div>

        {riskLevel !== 'unknown' && (
          <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase border tracking-wide ${RISK_COLORS[riskLevel]}`}>
            {riskLevel} Risk
          </span>
        )}

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={formLoading || analyzing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
          >
            {formLoading ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            {isEditing ? 'Update' : 'Save'}
          </button>
        </div>
      </div>

      {/* ── Three Column Body ─────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── LEFT: AI Copilot (300px) ────────────────────────────────────── */}
        <div className="w-[300px] shrink-0 border-r border-slate-800 overflow-y-auto bg-slate-900/20">
          <AICopilot
            complaint={selectedComplaint}
            analyzing={analyzing}
            error={analysisError}
          />
        </div>

        {/* ── CENTER: Complaint Form ───────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">

          <FormSection icon={User} title="Customer Information">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Customer Name"  name="customer_name"    value={formData.customer_name}    onChange={handleChange} placeholder="John Smith"           aiField={Boolean(analysis?.extracted_customer_name)} />
              <Field label="Email"          name="customer_email"   value={formData.customer_email}   onChange={handleChange} placeholder="john@company.com" type="email" />
              <Field label="Phone"          name="customer_phone"   value={formData.customer_phone}   onChange={handleChange} placeholder="+91 98765 43210" />
              <Field label="Company"        name="customer_company" value={formData.customer_company} onChange={handleChange} placeholder="Pharma Corp Ltd" />
              <Field label="Country"        name="customer_country" value={formData.customer_country} onChange={handleChange} placeholder="India" className="col-span-2" />
            </div>
          </FormSection>

          <FormSection icon={Package} title="Product Information" iconColor="text-blue-400">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Product Name"       name="product_name"       value={formData.product_name}       onChange={handleChange} placeholder="Amoxicillin 500mg" required aiField={Boolean(analysis?.extracted_product_name)} />
              <Field label="Batch / Lot Number" name="batch_number"       value={formData.batch_number}       onChange={handleChange} placeholder="BN-2025-001234"    required aiField={Boolean(analysis?.extracted_batch_number)} />
              <Field label="Manufacturing Date" name="manufacturing_date" value={formData.manufacturing_date} onChange={handleChange} placeholder="Jan 2025" />
              <Field label="Expiry Date"        name="expiry_date"        value={formData.expiry_date}        onChange={handleChange} placeholder="Jan 2028" />
              <Field label="Quantity Affected"  name="quantity_affected"  value={formData.quantity_affected}  onChange={handleChange} placeholder="50 bottles" className="col-span-2" />
            </div>
          </FormSection>

          <FormSection icon={ClipboardList} title="Complaint Details" iconColor="text-orange-400">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Select
                  label="Category" name="category"
                  value={formData.category} onChange={handleChange}
                  options={[
                    { value: 'other',           label: 'Other' },
                    { value: 'product_quality', label: 'Product Quality' },
                    { value: 'adverse_event',   label: 'Adverse Event' },
                    { value: 'labeling',        label: 'Labeling' },
                    { value: 'packaging',       label: 'Packaging' },
                    { value: 'delivery',        label: 'Delivery' },
                    { value: 'documentation',   label: 'Documentation' },
                  ]}
                />
                <Field label="Date of Complaint" name="date_of_complaint" value={formData.date_of_complaint} onChange={handleChange} placeholder="2025-06-01" />
              </div>
              <div>
                <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-1.5">
                  Complaint Description <span className="text-red-400">*</span>
                  {analysis?.extracted_description && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/20">AI</span>
                  )}
                </label>
                <textarea
                  name="complaint_description"
                  value={formData.complaint_description}
                  onChange={handleChange}
                  rows={4}
                  placeholder="Detailed description of the quality issue..."
                  className="w-full bg-slate-800/60 border border-slate-700/80 rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20 transition-colors resize-none"
                />
              </div>
            </div>
          </FormSection>

        </div>

        {/* ── RIGHT: Chat Interface (320px) ───────────────────────────────── */}
        <div className="w-[320px] shrink-0 border-l border-slate-800 flex flex-col bg-slate-900/30">

          {/* Chat header */}
          <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center">
              <Bot size={14} className="text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">AI Complaint Assistant</p>
              <div className="flex items-center gap-1">
                <div className={`w-1.5 h-1.5 rounded-full ${analyzing ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
                <span className="text-[10px] text-slate-500">{analyzing ? 'Analyzing...' : 'Online'}</span>
              </div>
            </div>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map(msg => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* File drop zone — compact */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`mx-3 mb-2 border border-dashed rounded-lg px-3 py-2 flex items-center gap-2 cursor-pointer transition-colors ${
              dragOver
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-slate-700 hover:border-slate-500'
            }`}
            onClick={() => fileRef.current?.click()}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.eml,.txt,.msg"
              className="hidden"
              onChange={(e) => handleFileDrop(e.target.files[0])}
            />
            <Paperclip size={13} className="text-slate-500 shrink-0" />
            <span className="text-xs text-slate-500">Drop PDF or email, or click to upload</span>
          </div>

          {/* Chat input */}
          <div className="p-3 border-t border-slate-800 shrink-0">
            <div className="flex items-end gap-2">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe the complaint or paste email..."
                rows={3}
                className="flex-1 bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/20 transition-colors resize-none"
              />
              <button
                onClick={handleSend}
                disabled={!inputText.trim() || analyzing}
                className="w-9 h-9 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-colors shrink-0"
              >
                {analyzing
                  ? <Loader2 size={15} className="text-white animate-spin" />
                  : <Send size={15} className="text-white" />
                }
              </button>
            </div>
            <p className="text-[10px] text-slate-600 mt-1.5 text-center">
              Press Enter to send · Shift+Enter for new line
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}
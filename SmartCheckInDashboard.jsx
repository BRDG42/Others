import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import {
  CheckCircle, Target, Clock, Shield, ChevronDown, ChevronRight,
  MessageSquare, Loader, Bot, Send, Mail, X, Minimize2, Maximize2,
  User, RotateCcw, AlertTriangle, Sparkles, ChevronUp, ArrowRight
} from 'lucide-react';

const C = {
  violet900: '#2A1D6E', violet700: '#3826A0', violet: '#4832B8', violet400: '#6B5CC7',
  violet200: '#A89EDE', violet100: '#D4CFEF', violet50: '#EEECF9',
  flamingo700: '#A62341', flamingo: '#CD3151', flamingo300: '#E06B85', flamingo100: '#F5CDD6', flamingo50: '#FDF0F3',
  palm700: '#147A53', palm: '#1C9667', palm300: '#5BB894', palm100: '#C8E8DC', palm50: '#EDF8F3',
  dark: '#1A1535', gray900: '#212033', gray700: '#44425A', gray500: '#7C7A8E',
  gray300: '#C5C4CF', gray200: '#E0DFE6', gray100: '#F0EFF4', gray50: '#F8F7FB', white: '#FFFFFF',
};

const phases = [
  {
    id: 'initiate', name: 'Initiate', start: '2026-01-16', end: '2026-01-22', progress: 100, status: 'Completed',
    tasks: [
      { name: 'Discussion Walkthrough for initial understanding', progress: 100 },
      { name: 'Grab the Stakeholder Register', progress: 100 },
      { name: 'Business problem / opportunity', progress: 100 },
    ]
  },
  {
    id: 'planning', name: 'Planning Phase', start: '2026-01-16', end: '2026-03-25', progress: 77, status: 'In Progress',
    tasks: [
      { name: 'Scope (BRD, Scope Statement, Charter)', progress: 100 },
      { name: 'Emergent Design (SDD) & Technical Discussion', progress: 57 },
      { name: 'SDD (HLD, LLD) Baselined & Signed off', progress: 40 },
      { name: 'LLD & Estimation Review & Sign off', progress: 15 },
      { name: 'Workshop: SDD decomposition & work packages', progress: 95 },
      { name: 'Exploration, Brainstorming & Groundwork', progress: 100 },
    ]
  },
  {
    id: 'phase1', name: 'Phase #1 — Pilot', start: '2026-02-02', end: '2026-04-30', progress: 26, status: 'In Progress',
    tasks: [
      { name: 'Development (UX/UI & App Changes)', progress: 95 },
      { name: 'Vendor Infra Provision (Azure)', progress: 33 },
      { name: 'Sovereign Cloud Prep', progress: 2 },
      { name: 'Infrastructure Provisioning (Dev/QA/UAT/Prod)', progress: 6 },
      { name: 'Integration — ICP SDK Prep', progress: 96 },
      { name: 'Integration — ICP Onboarding (Journey #0)', progress: 3 },
      { name: 'Integration — On-site Verification (Journey #4)', progress: 2 },
      { name: 'Integration — Arrival Confirmation (Journey #2)', progress: 2 },
      { name: 'Integration — AD Police', progress: 47 },
      { name: 'Integration — VICAS', progress: 0 },
      { name: 'Hotel Onboarding (Rotana)', progress: 31 },
      { name: 'Hotel Integration (PMS & MessageBox)', progress: 4 },
      { name: 'QA Prep', progress: 22 },
      { name: 'QA & UAT', progress: 0 },
      { name: 'Training Material', progress: 17 },
      { name: 'Communication', progress: 0 },
      { name: 'Training Delivery', progress: 0 },
      { name: 'Go-Live & CAB Approval', progress: 0 },
    ]
  },
  {
    id: 'phase2', name: 'Phase #2 — Hotel Scaling', start: '2026-05-01', end: '2026-06-30', progress: 0, status: 'Not Started',
    tasks: [
      { name: 'Engage candidate hotels', progress: 0 },
      { name: 'Complete list of hotels to scale', progress: 0 },
      { name: 'Integrate with additional PMS', progress: 0 },
      { name: 'Onboard hotels, rollout & training', progress: 0 },
    ]
  },
  {
    id: 'phase3', name: 'Phase #3 — Mobile Arrival', start: '2026-07-01', end: '2026-07-21', progress: 0, status: 'Not Started',
    tasks: [
      { name: 'Mobile Arrival Confirmation (Journey #1)', progress: 0 },
      { name: 'QA & UAT', progress: 0 },
      { name: 'Go-Live & CAB Approval', progress: 0 },
    ]
  },
  {
    id: 'phase4', name: 'Phase #4 — Expanded Rollout', start: '2026-07-22', end: '2026-10-27', progress: 0, status: 'Not Started',
    tasks: [
      { name: 'Engage & onboard additional hotels', progress: 0 },
      { name: 'Integrate with additional PMS', progress: 0 },
      { name: 'Rollout, implementation & support', progress: 0 },
    ]
  },
  {
    id: 'phase5', name: 'Phase #5 — Kiosk', start: '2026-10-14', end: '2026-11-30', progress: 0, status: 'Not Started',
    tasks: [
      { name: 'Kiosk Arrival Confirmation (Journey #3)', progress: 0 },
      { name: 'Kiosk Hardware Setup', progress: 0 },
      { name: 'Hotel Key Issuance Integration', progress: 0 },
      { name: 'QA & UAT', progress: 0 },
      { name: 'Go-Live & CAB Approval', progress: 0 },
    ]
  },
  {
    id: 'handover', name: 'Handover & Closure', start: '2026-05-01', end: '2026-06-23', progress: 0, status: 'Not Started',
    tasks: [
      { name: 'Post-Go-Live Stabilization (30 days)', progress: 0 },
      { name: 'Pilot Handover & Closure', progress: 0 },
    ]
  },
];

const milestones = [
  { name: 'Project Kickoff', date: 'Jan 16', done: true },
  { name: 'Scope Signed Off', date: 'Feb 13', done: true },
  { name: 'SDD Baselined', date: 'Feb 25', done: false },
  { name: 'Infra Complete', date: 'Mar 26', done: false },
  { name: 'Pilot Go-Live', date: 'Apr 30', done: false },
  { name: 'Phase 2 Done', date: 'Jun 30', done: false },
  { name: 'Phase 3 Live', date: 'Jul 21', done: false },
  { name: 'Phase 5 Live', date: 'Nov 30', done: false },
];

const STATUS_BG = { 'Completed': C.palm50, 'In Progress': C.violet50, 'Not Started': C.gray100 };
const STATUS_FG = { 'Completed': C.palm700, 'In Progress': C.violet, 'Not Started': C.gray500 };

const PROJECT_CONTEXT = `You are a CTO-level advisor for the Smart Check-In (Face Recognition) project at DCT Abu Dhabi (Department of Culture and Tourism). You have deep knowledge of this project and answer questions concisely and directly.

Project status as of March 4, 2026:
- Total duration: 215 days (Jan 16 – Nov 30, 2026)
- Overall progress: 25% baseline / 28% actual
- Initiate: 100% complete
- Planning: 77% (83% actual) — Scope 100%, SDD 57%, SDD sign-off 40%, LLD 15%, Workshop 95%, Exploration 100%
- Phase 1 Pilot (target Apr 30, 2026): 26% overall
  * Development (UX/UI): 95% ✅
  * ICP SDK Prep: 96% ✅  
  * AD Police Integration: 47%
  * Hotel Onboarding (Rotana): 31% — NDA 100%, DPA 50%, Service Agreement 20%
  * Vendor Infra (Azure): 33%
  * Sovereign Cloud Prep: 2% ⚠️ CRITICAL BLOCKER
  * Infrastructure Provisioning: 6% ⚠️ CRITICAL BLOCKER
  * VICAS Integration: 0% ⚠️ NOT STARTED
  * Hotel Integration (PMS/MessageBox): 4%
  * QA Prep: 22%
  * QA & UAT: 0%
  * Training Material: 17%
  * Go-Live & CAB Approval: 0%
- Phases 2–5 and Handover: Not started
- Key integrations: ICP (face recognition/KYC), AD Police, VICAS, Opera Cloud PMS, MessageBox
- Infrastructure: Azure sovereign cloud, Kubernetes across Dev/QA/UAT/Prod
- Pilot hotel: Rotana Abu Dhabi
- Pilot Go-Live target: April 30, 2026 (57 days away)

Answer questions about this project clearly and concisely. Be direct. Max 200 words per response unless asked for detail.`;

const SUGGESTED_QUESTIONS = [
  { label: 'What are the biggest risks to Go-Live?', icon: '⚠️' },
  { label: 'Is April 30 still realistic?', icon: '📅' },
  { label: 'What should we prioritise this week?', icon: '🎯' },
  { label: 'What is blocking infrastructure?', icon: '🔧' },
  { label: 'Status of Rotana onboarding?', icon: '🏨' },
  { label: 'Rate this project Red/Amber/Green', icon: '🚦' },
  { label: 'What is VICAS and why is it at 0%?', icon: '🔌' },
  { label: 'Summarise Phase 1 in 3 bullet points', icon: '📋' },
];

const Tip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: C.white, border: `1px solid ${C.violet100}`, borderRadius: 10, padding: '10px 14px', boxShadow: '0 4px 16px rgba(72,50,184,0.10)' }}>
      <p style={{ margin: 0, fontWeight: 700, color: C.dark, fontSize: 12 }}>{label}</p>
      {payload.filter(p => p.value > 0 && p.dataKey !== 'start').map((p, i) => (
        <p key={i} style={{ margin: '4px 0 0', fontSize: 11, color: C.gray700 }}>
          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: p.color, marginRight: 6 }} />
          {p.dataKey === 'done' ? 'Completed' : p.dataKey === 'rem' ? 'Remaining' : p.name}: {p.value}{p.dataKey === 'progress' ? '%' : ' days'}
        </p>
      ))}
    </div>
  );
};

// ─── EMAIL MODAL ────────────────────────────────────────────────────────────
function EmailModal({ onClose }) {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!form.name || !form.email || !form.message) return;
    setSending(true);
    await new Promise(r => setTimeout(r, 1200));
    setSending(false);
    setSent(true);
  };

  const inp = (field, placeholder, multiline = false) => {
    const style = {
      width: '100%', boxSizing: 'border-box',
      padding: multiline ? '10px 12px' : '9px 12px',
      background: C.gray50, border: `1.5px solid ${C.violet100}`,
      borderRadius: 8, fontSize: 12, color: C.dark, outline: 'none',
      fontFamily: 'inherit', resize: multiline ? 'vertical' : undefined,
      minHeight: multiline ? 90 : undefined,
      transition: 'border-color 0.2s',
    };
    return multiline
      ? <textarea value={form[field]} onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))}
          placeholder={placeholder} style={style} rows={4}
          onFocus={e => e.target.style.borderColor = C.violet}
          onBlur={e => e.target.style.borderColor = C.violet100} />
      : <input value={form[field]} onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))}
          placeholder={placeholder} style={style}
          onFocus={e => e.target.style.borderColor = C.violet}
          onBlur={e => e.target.style.borderColor = C.violet100} />;
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(26,21,53,0.65)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: C.white, borderRadius: 16, width: 460, maxWidth: '94vw', overflow: 'hidden', boxShadow: '0 24px 64px rgba(26,21,53,0.28)' }}>
        {/* Header */}
        <div style={{ background: `linear-gradient(135deg, ${C.violet900}, ${C.violet})`, padding: '18px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 8, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Mail size={16} color={C.white} />
            </div>
            <div>
              <p style={{ margin: 0, color: C.white, fontSize: 13, fontWeight: 700 }}>Contact Project Team</p>
              <p style={{ margin: 0, color: C.violet200, fontSize: 10 }}>Reach the DCT Smart Check-In team directly</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 6, padding: 6, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <X size={14} color={C.white} />
          </button>
        </div>

        <div style={{ padding: '20px' }}>
          {sent ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ width: 52, height: 52, borderRadius: '50%', background: C.palm50, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
                <CheckCircle size={26} color={C.palm} />
              </div>
              <p style={{ fontWeight: 700, fontSize: 15, color: C.dark, margin: '0 0 6px' }}>Message Sent!</p>
              <p style={{ fontSize: 12, color: C.gray500, margin: '0 0 18px' }}>The project team will get back to you shortly.</p>
              <button onClick={onClose} style={{ background: C.violet, border: 'none', borderRadius: 8, padding: '9px 24px', color: C.white, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>Close</button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ background: C.violet50, borderRadius: 8, padding: '10px 12px', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <AlertTriangle size={13} color={C.violet} style={{ marginTop: 1, flexShrink: 0 }} />
                <p style={{ margin: 0, fontSize: 11, color: C.violet700, lineHeight: 1.5 }}>
                  Send your question or update request to <strong>omar@dct.abudhabi</strong>. The project manager will respond within 1 business day.
                </p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div><label style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.6, display: 'block', marginBottom: 5 }}>Your Name *</label>{inp('name', 'Full name')}</div>
                <div><label style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.6, display: 'block', marginBottom: 5 }}>Email *</label>{inp('email', 'your@email.com')}</div>
              </div>
              <div><label style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.6, display: 'block', marginBottom: 5 }}>Subject</label>{inp('subject', 'e.g. Question about Sovereign Cloud status')}</div>
              <div><label style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.6, display: 'block', marginBottom: 5 }}>Message *</label>{inp('message', 'Describe your question or update request...', true)}</div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', paddingTop: 4 }}>
                <button onClick={onClose} style={{ background: C.gray100, border: 'none', borderRadius: 8, padding: '9px 18px', color: C.gray700, fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
                <button onClick={handleSend} disabled={sending || !form.name || !form.email || !form.message}
                  style={{ background: (!form.name || !form.email || !form.message) ? C.violet200 : C.violet, border: 'none', borderRadius: 8, padding: '9px 20px', color: C.white, fontSize: 12, fontWeight: 700, cursor: (!form.name || !form.email || !form.message) ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
                  {sending ? <><Loader size={13} className="spin" />Sending...</> : <><Send size={13} />Send Message</>}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── CTO ADVISOR CHATBOT ────────────────────────────────────────────────────
function CTOAdvisor() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm your CTO Advisory Agent for the Smart Check-In project. I have full visibility into the current project data as of March 4, 2026.\n\nAsk me anything about project health, risks, blockers, or specific work streams — or pick a suggested question below.",
      ts: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [showEmail, setShowEmail] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const userText = (text || input).trim();
    if (!userText || loading) return;
    setInput('');
    setShowSuggestions(false);

    const userMsg = { role: 'user', content: userText, ts: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    const history = [...messages, userMsg].map(m => ({ role: m.role, content: m.content }));

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: PROJECT_CONTEXT,
          messages: history,
        }),
      });
      const data = await res.json();
      const text = data.content?.filter(b => b.type === 'text').map(b => b.text).join('\n') || 'No response received.';
      setMessages(prev => [...prev, { role: 'assistant', content: text, ts: new Date() }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Connection error. Please try again.', ts: new Date() }]);
    }
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: "Chat cleared. I'm ready for your next question about the Smart Check-In project.",
      ts: new Date()
    }]);
    setShowSuggestions(true);
  };

  const renderMessage = (content) => {
    return content.split('\n').map((line, i) => {
      const clean = line.replace(/\*\*/g, '').replace(/^#+\s*/, '');
      if (line.match(/^#{1,3}\s/) || line.match(/^\*\*.+\*\*$/)) {
        return <p key={i} style={{ fontWeight: 700, color: C.violet, fontSize: 12, margin: '10px 0 3px' }}>{clean}</p>;
      }
      if (line.match(/^[-*]\s/)) {
        const txt = clean.replace(/^[-*]\s*/, '');
        return (
          <div key={i} style={{ display: 'flex', gap: 7, margin: '2px 0', paddingLeft: 2 }}>
            <span style={{ color: C.violet400, flexShrink: 0, marginTop: 1 }}>•</span>
            <span>{txt}</span>
          </div>
        );
      }
      if (line.trim() === '') return <div key={i} style={{ height: 5 }} />;
      return <p key={i} style={{ margin: '2px 0' }}>{clean}</p>;
    });
  };

  const fmt = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      {showEmail && <EmailModal onClose={() => setShowEmail(false)} />}

      <div style={{ background: C.white, borderRadius: 14, border: `1px solid ${C.violet100}`, boxShadow: '0 4px 24px rgba(72,50,184,0.10)', overflow: 'hidden' }}>
        {/* ── HEADER ── */}
        <div style={{ background: `linear-gradient(135deg, ${C.violet900} 0%, ${C.violet} 100%)`, padding: '14px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ position: 'relative' }}>
                <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={18} color={C.white} />
                </div>
                <div style={{ position: 'absolute', bottom: 1, right: 1, width: 9, height: 9, borderRadius: '50%', background: C.palm300, border: `2px solid ${C.violet}` }} />
              </div>
              <div>
                <p style={{ margin: 0, color: C.white, fontSize: 13, fontWeight: 700, letterSpacing: -0.2 }}>CTO Advisory Agent</p>
                <p style={{ margin: 0, color: C.violet200, fontSize: 10 }}>AI-powered · Smart Check-In · Live project data</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button onClick={() => setShowEmail(true)}
                style={{ background: 'rgba(205,49,81,0.85)', border: 'none', borderRadius: 7, padding: '6px 12px', color: C.white, fontSize: 11, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5 }}>
                <Mail size={12} /> Email Team
              </button>
              <button onClick={clearChat} title="Clear chat"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 7, padding: '6px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <RotateCcw size={13} color="rgba(255,255,255,0.7)" />
              </button>
              <button onClick={() => setExpanded(p => !p)} title={expanded ? 'Minimise' : 'Expand'}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 7, padding: '6px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                {expanded ? <Minimize2 size={13} color="rgba(255,255,255,0.7)" /> : <Maximize2 size={13} color="rgba(255,255,255,0.7)" />}
              </button>
            </div>
          </div>
        </div>

        {expanded && (
          <>
            {/* ── MESSAGES ── */}
            <div style={{ height: 340, overflowY: 'auto', padding: '16px 16px 8px', display: 'flex', flexDirection: 'column', gap: 12, background: C.gray50 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
                  {/* Avatar */}
                  <div style={{
                    width: 28, height: 28, borderRadius: msg.role === 'user' ? 8 : 10, flexShrink: 0, marginTop: 2,
                    background: msg.role === 'user' ? C.flamingo : `linear-gradient(135deg, ${C.violet900}, ${C.violet})`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    {msg.role === 'user' ? <User size={13} color={C.white} /> : <Bot size={13} color={C.white} />}
                  </div>
                  {/* Bubble */}
                  <div style={{ maxWidth: '80%' }}>
                    <div style={{
                      padding: '10px 13px', borderRadius: msg.role === 'user' ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
                      background: msg.role === 'user' ? C.flamingo : C.white,
                      border: msg.role === 'user' ? 'none' : `1px solid ${C.violet100}`,
                      boxShadow: msg.role === 'user' ? 'none' : '0 1px 4px rgba(72,50,184,0.06)',
                      fontSize: 12, color: msg.role === 'user' ? C.white : C.gray700,
                      lineHeight: 1.65,
                    }}>
                      {renderMessage(msg.content)}
                    </div>
                    <p style={{ fontSize: 9, color: C.gray300, margin: '3px 4px 0', textAlign: msg.role === 'user' ? 'right' : 'left' }}>{fmt(msg.ts)}</p>
                  </div>
                </div>
              ))}

              {loading && (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <div style={{ width: 28, height: 28, borderRadius: 10, background: `linear-gradient(135deg, ${C.violet900}, ${C.violet})`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                    <Bot size={13} color={C.white} />
                  </div>
                  <div style={{ padding: '10px 14px', borderRadius: '4px 12px 12px 12px', background: C.white, border: `1px solid ${C.violet100}`, display: 'flex', gap: 5, alignItems: 'center' }}>
                    {[0, 1, 2].map(j => (
                      <div key={j} style={{ width: 7, height: 7, borderRadius: '50%', background: C.violet200, animation: `bounce 1.2s ease-in-out ${j * 0.18}s infinite` }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* ── SUGGESTED QUESTIONS ── */}
            {showSuggestions && (
              <div style={{ padding: '10px 16px', borderTop: `1px solid ${C.violet50}`, background: C.white }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 8 }}>
                  <Sparkles size={11} color={C.violet400} />
                  <span style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.6 }}>Suggested Questions</span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {SUGGESTED_QUESTIONS.map((q, i) => (
                    <button key={i} onClick={() => sendMessage(q.label)} disabled={loading}
                      style={{
                        background: C.violet50, border: `1px solid ${C.violet100}`, borderRadius: 20,
                        padding: '5px 11px', fontSize: 11, color: C.violet700, cursor: loading ? 'not-allowed' : 'pointer',
                        fontFamily: 'inherit', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 5,
                        transition: 'all 0.15s',
                        opacity: loading ? 0.5 : 1,
                      }}
                      onMouseEnter={e => { if (!loading) { e.target.style.background = C.violet100; e.target.style.borderColor = C.violet200; }}}
                      onMouseLeave={e => { e.target.style.background = C.violet50; e.target.style.borderColor = C.violet100; }}>
                      <span>{q.icon}</span> {q.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* ── INPUT ── */}
            <div style={{ padding: '10px 14px 14px', background: C.white, borderTop: showSuggestions ? 'none' : `1px solid ${C.violet50}` }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                <div style={{ flex: 1, background: C.gray50, border: `1.5px solid ${C.violet100}`, borderRadius: 10, padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8, transition: 'border-color 0.2s' }}
                  onFocusCapture={e => e.currentTarget.style.borderColor = C.violet}
                  onBlurCapture={e => e.currentTarget.style.borderColor = C.violet100}>
                  <input
                    ref={inputRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Ask anything about this project…"
                    disabled={loading}
                    style={{ flex: 1, background: 'none', border: 'none', outline: 'none', fontSize: 12, color: C.dark, fontFamily: 'inherit' }}
                  />
                  {!showSuggestions && (
                    <button onClick={() => setShowSuggestions(true)} title="Show suggestions"
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}>
                      <Sparkles size={13} color={C.violet400} />
                    </button>
                  )}
                </div>
                <button onClick={() => sendMessage()} disabled={loading || !input.trim()}
                  style={{
                    width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                    background: loading || !input.trim() ? C.violet200 : `linear-gradient(135deg, ${C.violet}, ${C.flamingo})`,
                    border: 'none', cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'all 0.2s',
                  }}>
                  {loading ? <Loader size={15} color={C.white} className="spin" /> : <Send size={15} color={C.white} />}
                </button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 7 }}>
                <p style={{ margin: 0, fontSize: 9, color: C.gray300 }}>Press Enter to send · Shift+Enter for new line</p>
                <button onClick={() => setShowEmail(true)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 10, color: C.gray400, display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'inherit', padding: 0 }}>
                  <Mail size={10} color={C.gray400} /> Need a human response? Email the team
                  <ArrowRight size={9} color={C.gray400} />
                </button>
              </div>
            </div>
          </>
        )}

        {!expanded && (
          <div style={{ padding: '10px 18px', background: C.gray50, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, color: C.gray500 }}>{messages.length - 1} message{messages.length !== 2 ? 's' : ''} in conversation</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button onClick={() => setShowEmail(true)}
                style={{ background: C.flamingo50, border: `1px solid ${C.flamingo100}`, borderRadius: 6, padding: '5px 10px', color: C.flamingo, fontSize: 11, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'inherit' }}>
                <Mail size={11} /> Email Team
              </button>
              <button onClick={() => setExpanded(true)}
                style={{ background: C.violet50, border: `1px solid ${C.violet100}`, borderRadius: 6, padding: '5px 10px', color: C.violet, fontSize: 11, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'inherit' }}>
                <MessageSquare size={11} /> Open Chat
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-5px); }
        }
      `}</style>
    </>
  );
}

// ─── MAIN DASHBOARD ─────────────────────────────────────────────────────────
export default function Dashboard() {
  const [expanded, setExpanded] = useState({});
  const toggle = (id) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const overall = 25;
  const actual = 28;

  const allTasks = phases.flatMap(p => p.tasks);
  const taskStatusData = useMemo(() => [
    { name: 'Completed', value: allTasks.filter(t => t.progress === 100).length },
    { name: 'In Progress', value: allTasks.filter(t => t.progress > 0 && t.progress < 100).length },
    { name: 'Not Started', value: allTasks.filter(t => t.progress === 0).length },
  ], []);

  const gantt = useMemo(() => {
    const ps = new Date('2026-01-16');
    return phases.map(p => {
      const s = new Date(p.start);
      const e = new Date(p.end);
      const sd = Math.max(0, Math.floor((s - ps) / 864e5));
      const dur = Math.floor((e - s) / 864e5);
      const done = Math.floor(dur * p.progress / 100);
      return { name: p.name.length > 26 ? p.name.slice(0, 26) + '…' : p.name, start: sd, done, rem: dur - done, pct: p.progress };
    });
  }, []);

  const p1Detail = [
    { name: 'ICP SDK Prep', progress: 96 },
    { name: 'Development', progress: 95 },
    { name: 'AD Police', progress: 47 },
    { name: 'Vendor Infra', progress: 33 },
    { name: 'Hotel Onboard', progress: 31 },
    { name: 'QA Prep', progress: 22 },
    { name: 'Training', progress: 17 },
    { name: 'Infra Prov.', progress: 6 },
    { name: 'Hotel Integ.', progress: 4 },
    { name: 'Journey #0', progress: 3 },
    { name: 'Sov. Cloud', progress: 2 },
    { name: 'VICAS', progress: 0 },
    { name: 'QA & UAT', progress: 0 },
  ];

  const card = { background: C.white, borderRadius: 12, border: `1px solid ${C.violet100}`, boxShadow: '0 1px 4px rgba(72,50,184,0.04)' };
  const h2s = { fontSize: 14, fontWeight: 700, color: C.dark, letterSpacing: -0.2, margin: '0 0 16px' };

  return (
    <div style={{ background: C.gray50, minHeight: '100vh', fontFamily: "'Segoe UI', -apple-system, sans-serif" }}>
      {/* HEADER */}
      <div style={{ background: `linear-gradient(135deg, ${C.dark} 0%, ${C.violet900} 50%, ${C.violet} 100%)` }}>
        <div style={{ height: 3, background: `linear-gradient(90deg, ${C.flamingo}, ${C.violet}, ${C.palm})` }} />
        <div style={{ padding: '24px 32px 20px', maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
              <rect x="2" y="2" width="18" height="18" rx="2" fill="white" opacity="0.9"/>
              <rect x="24" y="2" width="18" height="18" rx="2" fill="white" opacity="0.7"/>
              <rect x="2" y="24" width="18" height="18" rx="2" fill="white" opacity="0.7"/>
              <rect x="24" y="24" width="18" height="18" rx="2" fill="white" opacity="0.5"/>
            </svg>
            <div style={{ display: 'flex', flexDirection: 'column', borderLeft: '1px solid rgba(255,255,255,0.25)', paddingLeft: 10 }}>
              <span style={{ color: C.white, fontSize: 11, fontWeight: 700, fontFamily: 'serif', letterSpacing: 0.5, lineHeight: 1.2 }}>دائرة الثقافة والسياحة</span>
              <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 8.5, fontWeight: 600, letterSpacing: 1.2, textTransform: 'uppercase', lineHeight: 1.3 }}>Department of Culture</span>
              <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 8.5, fontWeight: 600, letterSpacing: 1.2, textTransform: 'uppercase', lineHeight: 1.1 }}>and Tourism — Abu Dhabi</span>
            </div>
            <div style={{ width: 1, height: 44, background: 'rgba(255,255,255,0.15)', margin: '0 6px' }} />
            <div>
              <h1 style={{ color: C.white, fontSize: 26, fontWeight: 700, margin: 0, letterSpacing: -0.5 }}>Smart Check-In</h1>
              <p style={{ color: C.violet200, fontSize: 13, margin: '3px 0 0', fontWeight: 500 }}>Face Recognition System — Master Project Plan</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 20, marginTop: 14, fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
            <span>Duration: <strong style={{ color: 'rgba(255,255,255,0.8)' }}>215 days</strong></span>
            <span>Start: <strong style={{ color: 'rgba(255,255,255,0.8)' }}>Jan 16, 2026</strong></span>
            <span>End: <strong style={{ color: 'rgba(255,255,255,0.8)' }}>Nov 30, 2026</strong></span>
            <span>Updated: <strong style={{ color: C.flamingo300 }}>Mar 4, 2026</strong></span>
          </div>
        </div>
      </div>

      <div style={{ padding: '24px 32px', maxWidth: 1280, margin: '0 auto' }}>
        {/* KPI CARDS */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 20 }}>
          {[
            { label: 'Baseline Progress', val: `${overall}%`, sub: `${actual}% actual`, icon: <Target size={18} />, accent: C.violet, bar: overall },
            { label: 'Active Phases', val: phases.filter(p => p.status === 'In Progress').length, sub: `of ${phases.length} total`, icon: <Clock size={18} />, accent: C.flamingo },
            { label: 'Phases Done', val: `${phases.filter(p => p.status === 'Completed').length}/${phases.length}`, sub: 'completed', icon: <CheckCircle size={18} />, accent: C.palm },
            { label: 'Pilot Go-Live', val: 'Apr 30', sub: '57 days remaining', icon: <Shield size={18} />, accent: C.violet },
          ].map((k, i) => (
            <div key={i} style={{ ...card, padding: '18px 20px', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: k.accent }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: C.gray500, textTransform: 'uppercase', letterSpacing: 0.8 }}>{k.label}</span>
                <span style={{ color: k.accent, opacity: 0.7 }}>{k.icon}</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: C.dark }}>{k.val}</div>
              <div style={{ fontSize: 11, color: C.gray500, marginTop: 2 }}>{k.sub}</div>
              {k.bar !== undefined && (
                <div style={{ marginTop: 10, height: 5, background: C.violet100, borderRadius: 3 }}>
                  <div style={{ height: 5, borderRadius: 3, background: `linear-gradient(90deg, ${C.violet}, ${C.flamingo})`, width: `${k.bar}%`, transition: 'width 0.6s ease' }} />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* PHASE TABLE */}
        <div style={{ ...card, padding: '20px', marginBottom: 20 }}>
          <h2 style={h2s}>Project Phases</h2>
          <div style={{ fontSize: 12 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2.2fr 0.8fr 0.8fr 0.7fr 1.2fr', gap: 8, padding: '8px 10px', borderBottom: `2px solid ${C.violet}` }}>
              {['Phase', 'Start', 'End', 'Status', 'Progress'].map(h => (
                <span key={h} style={{ fontSize: 10, fontWeight: 700, color: C.violet700, textTransform: 'uppercase', letterSpacing: 0.6 }}>{h}</span>
              ))}
            </div>
            {phases.map((p, i) => (
              <React.Fragment key={p.id}>
                <div onClick={() => toggle(p.id)}
                  style={{ display: 'grid', gridTemplateColumns: '2.2fr 0.8fr 0.8fr 0.7fr 1.2fr', gap: 8, padding: '12px 10px', borderBottom: `1px solid ${C.violet50}`, background: i % 2 === 0 ? C.white : C.gray50, cursor: 'pointer', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {expanded[p.id] ? <ChevronDown size={14} color={C.violet} /> : <ChevronRight size={14} color={C.violet400} />}
                    <span style={{ fontWeight: 700, color: C.dark }}>{p.name}</span>
                  </div>
                  <span style={{ color: C.gray700 }}>{p.start.slice(5)}</span>
                  <span style={{ color: C.gray700 }}>{p.end.slice(5)}</span>
                  <span style={{ padding: '2px 8px', borderRadius: 20, fontSize: 10, fontWeight: 700, background: STATUS_BG[p.status], color: STATUS_FG[p.status], textAlign: 'center', whiteSpace: 'nowrap' }}>{p.status}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 6, background: C.violet50, borderRadius: 3 }}>
                      <div style={{ height: 6, borderRadius: 3, width: `${p.progress}%`, background: p.progress === 100 ? C.palm : `linear-gradient(90deg, ${C.violet}, ${C.violet400})`, transition: 'width 0.4s' }} />
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 700, color: p.progress === 100 ? C.palm700 : C.violet, minWidth: 32, textAlign: 'right' }}>{p.progress}%</span>
                  </div>
                </div>
                {expanded[p.id] && (
                  <div style={{ background: C.violet50, borderBottom: `1px solid ${C.violet100}` }}>
                    {p.tasks.map((t, ti) => (
                      <div key={ti} style={{ display: 'grid', gridTemplateColumns: '2.2fr 0.8fr 0.8fr 0.7fr 1.2fr', gap: 8, padding: '8px 10px 8px 36px', borderBottom: `1px solid ${C.violet100}` }}>
                        <span style={{ fontSize: 11, color: C.gray700 }}>{t.name}</span>
                        <span /><span />
                        <span style={{ fontSize: 10, color: t.progress === 100 ? C.palm700 : t.progress > 0 ? C.violet : C.gray500, fontWeight: 600 }}>
                          {t.progress === 100 ? '✓ Done' : t.progress > 0 ? 'Active' : 'Pending'}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ flex: 1, height: 4, background: C.violet100, borderRadius: 2 }}>
                            <div style={{ height: 4, borderRadius: 2, width: `${t.progress}%`, background: t.progress === 100 ? C.palm : C.violet400 }} />
                          </div>
                          <span style={{ fontSize: 10, color: t.progress === 100 ? C.palm700 : C.violet, minWidth: 28, textAlign: 'right', fontWeight: 600 }}>{t.progress}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* CHARTS ROW */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 0.6fr', gap: 16, marginBottom: 20 }}>
          <div style={{ ...card, padding: '20px' }}>
            <h2 style={h2s}>Phase Timeline (Days from Jan 16)</h2>
            <ResponsiveContainer width="100%" height={310}>
              <BarChart data={gantt} layout="vertical" margin={{ top: 4, right: 50, left: 4, bottom: 4 }} barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.violet50} horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: C.gray500 }} axisLine={{ stroke: C.violet100 }} tickLine={false} />
                <YAxis dataKey="name" type="category" width={160} tick={{ fontSize: 10, fill: C.gray700 }} axisLine={false} tickLine={false} />
                <Tooltip content={<Tip />} />
                <Bar dataKey="start" stackId="a" fill="transparent" />
                <Bar dataKey="done" stackId="a" fill={C.violet} name="Completed" />
                <Bar dataKey="rem" stackId="a" fill={C.violet100} radius={[0, 4, 4, 0]} name="Remaining"
                  label={({ x, y, width, height, index }) => (
                    <text x={x + width + 8} y={y + height / 2 + 4}
                      fill={gantt[index]?.pct === 100 ? C.palm700 : gantt[index]?.pct > 0 ? C.violet : C.gray500}
                      fontSize={10} fontWeight={700}>{gantt[index]?.pct}%</text>
                  )} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ ...card, padding: '20px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={h2s}>Task Status ({allTasks.length} tasks)</h2>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={taskStatusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" paddingAngle={3} cornerRadius={4}>
                    {taskStatusData.map((_, i) => <Cell key={i} fill={[C.palm, C.violet, C.violet100][i]} />)}
                  </Pie>
                  <Tooltip content={<Tip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {taskStatusData.map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: C.gray700 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: [C.palm, C.violet, C.violet100][i] }} />
                  <span style={{ flex: 1 }}>{s.name}</span>
                  <span style={{ fontWeight: 700, color: C.dark }}>{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* MILESTONES */}
        <div style={{ ...card, padding: '24px', marginBottom: 20 }}>
          <h2 style={{ ...h2s, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={15} color={C.flamingo} /> Key Milestones
          </h2>
          <div style={{ display: 'flex', alignItems: 'flex-start', position: 'relative' }}>
            <div style={{ position: 'absolute', top: 14, left: 20, right: 20, height: 3, background: C.violet100, zIndex: 0 }} />
            {milestones.map((m, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', zIndex: 1 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: m.done ? C.violet : C.white, border: `3px solid ${m.done ? C.violet : C.violet200}`, marginBottom: 8
                }}>{m.done && <CheckCircle size={12} color={C.white} />}</div>
                <span style={{ fontSize: 10, fontWeight: 700, color: m.done ? C.violet : C.gray700, textAlign: 'center', lineHeight: 1.3, maxWidth: 80 }}>{m.name}</span>
                <span style={{ fontSize: 10, color: C.gray500, marginTop: 3 }}>{m.date}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PHASE 1 DETAIL */}
        <div style={{ ...card, padding: '20px', marginBottom: 20 }}>
          <h2 style={h2s}>Phase #1 (Pilot) — Work Stream Progress</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={p1Detail} layout="vertical" margin={{ top: 4, right: 50, left: 4, bottom: 4 }} barSize={16}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.violet50} horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: C.gray500 }} axisLine={{ stroke: C.violet100 }} tickLine={false} />
              <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 10, fill: C.gray700 }} axisLine={false} tickLine={false} />
              <Tooltip content={<Tip />} />
              <Bar dataKey="progress" radius={[0, 4, 4, 0]} name="Progress %"
                label={({ x, y, width, height, index }) => (
                  <text x={x + width + 8} y={y + height / 2 + 4}
                    fill={p1Detail[index]?.progress >= 60 ? C.palm700 : p1Detail[index]?.progress >= 30 ? C.violet : p1Detail[index]?.progress > 0 ? C.flamingo : C.gray500}
                    fontSize={10} fontWeight={700}>{p1Detail[index]?.progress}%</text>
                )}>
                {p1Detail.map((d, i) => (
                  <Cell key={i} fill={d.progress === 0 ? C.violet100 : d.progress >= 60 ? C.palm : d.progress >= 30 ? C.violet : C.flamingo} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 8, fontSize: 10, color: C.gray500 }}>
            <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: C.palm, marginRight: 4 }} />60%+ On Track</span>
            <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: C.violet, marginRight: 4 }} />30–59% Monitor</span>
            <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: C.flamingo, marginRight: 4 }} />&lt;30% At Risk</span>
            <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: 2, background: C.violet100, marginRight: 4 }} />Not Started</span>
          </div>
        </div>

        {/* CTO ADVISOR */}
        <div style={{ marginBottom: 20 }}><CTOAdvisor /></div>

        {/* FOOTER */}
        <div style={{ textAlign: 'center', padding: '16px 0 8px' }}>
          <div style={{ height: 2, background: `linear-gradient(90deg, transparent, ${C.flamingo300}, ${C.violet400}, ${C.palm300}, transparent)`, marginBottom: 12 }} />
          <p style={{ color: C.gray500, fontSize: 10, fontWeight: 500, letterSpacing: 0.5 }}>
            Smart Check-In Project Dashboard &nbsp;•&nbsp; DCT Abu Dhabi &nbsp;•&nbsp; Updated: March 4, 2026
          </p>
        </div>
      </div>
    </div>
  );
}

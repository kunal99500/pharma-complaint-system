/**
 * App.jsx — Redesigned with top navbar instead of sidebar
 *
 * Layout:
 *   TOP: Fixed navbar with logo, nav links, and action buttons
 *   BODY: Full-width content area below the navbar
 *
 * Why top navbar:
 * - Only 3 nav items — sidebar would waste 230px of horizontal space
 * - Gives the three-column form layout maximum width to work with
 * - Standard pattern for enterprise data-entry platforms (Salesforce, Jira)
 */
import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import {
  FlaskConical,
  LayoutDashboard,
  FileText,
  PlusCircle,
  Shield,
} from 'lucide-react';

import ComplaintList from './components/ComplaintList';
import ComplaintForm from './components/ComplaintForm';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
          },
        }}
      />

      <div className="flex flex-col h-screen bg-slate-950 font-inter overflow-hidden">

        {/* ── Top Navbar ─────────────────────────────────────────────────── */}
        <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center px-6 gap-6 shrink-0 z-50">

          {/* Brand */}
          <div className="flex items-center gap-2.5 mr-4">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
              <FlaskConical size={14} className="text-white" />
            </div>
            <div className="leading-none">
              <p className="text-white text-sm font-bold">AIVOA</p>
              <p className="text-slate-500 text-[10px]">Pharma QMS</p>
            </div>
          </div>

          {/* Divider */}
          <div className="h-6 w-px bg-slate-700" />

          {/* Nav links */}
          <nav className="flex items-center gap-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              <LayoutDashboard size={15} />
              Dashboard
            </NavLink>

            <NavLink
              to="/complaints"
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              <FileText size={15} />
              Complaints
            </NavLink>

            <NavLink
              to="/complaints/new"
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              <PlusCircle size={15} />
              Log Complaint
            </NavLink>
          </nav>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Right side info */}
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Shield size={12} />
            <span>v1.0.0</span>
          </div>
        </header>

        {/* ── Page Content ───────────────────────────────────────────────── */}
        <main className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/"               element={<Dashboard />} />
            <Route path="/complaints"     element={<ComplaintList />} />
            <Route path="/complaints/new" element={<ComplaintForm />} />
            <Route path="/complaints/:id" element={<ComplaintForm />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  );
}
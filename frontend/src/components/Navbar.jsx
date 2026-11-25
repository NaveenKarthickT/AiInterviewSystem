import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  BrainCircuit,
  FileText,
  PlayCircle,
  BarChart3,
  Sparkles,
  LogOut,
  User as UserIcon,
  Sun,
  Moon,
} from 'lucide-react';

export const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
    { name: 'Resumes', path: '/resumes', icon: FileText },
    { name: 'Practice Interview', path: '/interview/setup', icon: PlayCircle },
    { name: 'Resume Optimizer', path: '/optimizer', icon: Sparkles },
  ];

  return (
    <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-brand-300 bg-clip-text text-transparent">
                InterviewAI
              </span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
                Adaptive
              </span>
            </div>
          </Link>

          {/* Navigation Links (when authenticated) */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname.startsWith(item.path);
                return (
                  <Link
                    key={item.name}
                    to={item.path}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-brand-600/15 text-brand-400 border border-brand-500/30'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          )}

          {/* Right actions */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Dark / Bright Mode Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
              title={isDark ? "Switch to Bright mode" : "Switch to Dark mode"}
              aria-label="Toggle theme mode"
            >
              {isDark ? (
                <Sun className="w-4 h-4 text-amber-400 transition-transform duration-300 hover:rotate-90" />
              ) : (
                <Moon className="w-4 h-4 text-brand-500 transition-transform duration-300 hover:-rotate-12" />
              )}
            </button>

            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <div className="hidden sm:flex items-center space-x-2 text-sm text-slate-300 bg-slate-800/80 py-1.5 px-3 rounded-full border border-slate-700/60">
                  <UserIcon className="w-4 h-4 text-brand-400" />
                  <span className="font-medium text-slate-200">{user?.full_name || 'Candidate'}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1.5 px-3 py-1.5 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors border border-transparent hover:border-red-500/20"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-300 hover:text-white px-3 py-2 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="text-sm font-medium bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded-lg shadow-sm shadow-brand-500/25 transition-colors"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

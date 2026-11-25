import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { ResumeUpload } from './pages/ResumeUpload';
import { InterviewSetup } from './pages/InterviewSetup';
import { LiveInterview } from './pages/LiveInterview';
import { ReportDetail } from './pages/ReportDetail';
import { ResumeOptimizer } from './pages/ResumeOptimizer';

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <div className="min-h-screen bg-slate-950 flex flex-col font-sans transition-colors duration-200">
            <Navbar />
            <main className="flex-1">
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Routes */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/resumes"
                  element={
                    <ProtectedRoute>
                      <ResumeUpload />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interview/setup"
                  element={
                    <ProtectedRoute>
                      <InterviewSetup />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interview/live/:sessionId"
                  element={
                    <ProtectedRoute>
                      <LiveInterview />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports/:sessionId"
                  element={
                    <ProtectedRoute>
                      <ReportDetail />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/optimizer"
                  element={
                    <ProtectedRoute>
                      <ResumeOptimizer />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/optimizer/:sessionId"
                  element={
                    <ProtectedRoute>
                      <ResumeOptimizer />
                    </ProtectedRoute>
                  }
                />

                {/* Default Redirect */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </main>
          </div>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;

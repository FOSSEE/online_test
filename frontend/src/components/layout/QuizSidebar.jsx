import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaHome, FaChevronRight, FaTimes } from 'react-icons/fa';
import Logo from '../ui/Logo';

const QuizSidebar = ({ currentQuestion = 1, totalQuestions = 11, attemptedQuestions = [], onQuestionClick }) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const questions = Array.from({ length: totalQuestions }, (_, i) => i + 1);

  const getQuestionClass = (q) => {
    if (q === currentQuestion) return 'current';
    if (attemptedQuestions.includes(q)) return 'attempted';
    return 'unattempted';
  };

  const handleQuestionClick = (index) => {
    if (onQuestionClick) {
      onQuestionClick(index);
    }
    setIsMobileOpen(false);
  };

  const progressPercentage = (attemptedQuestions.length / totalQuestions) * 100;

  const handleLinkClick = () => {
    setIsMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky top-0 left-0 h-screen z-50
          w-64 app-sidebar flex flex-col border-r border-white/5
          transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo Section - Matching header height */}
        <div className="h-16 lg:h-20 px-4 sm:px-6 lg:px-8 border-b border-[var(--border-strong)] bg-[var(--header-bg)] backdrop-blur-xl shadow-[var(--shadow-strong)] flex items-center justify-between flex-shrink-0">
          <Logo />
          <button
            onClick={() => setIsMobileOpen(false)}
            className="lg:hidden text-muted hover:text-[var(--text-primary)] transition"
          >
            <FaTimes className="w-5 h-5" />
          </button>
        </div>

        {/* Question Navigator */}
        <nav className="flex-1 p-4 sm:p-6 lg:p-8 space-y-4 overflow-y-auto">
          {/* Header with Progress */}
          <div className="mb-4">
            <div className="flex items-baseline justify-between mb-2">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                Questions
              </h3>
              <span className="text-xs font-medium text-muted">
                {attemptedQuestions.length}/{totalQuestions}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden border border-[var(--border-subtle)]">
              <div
                className="h-full bg-blue-600 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>

          {/* Question Grid */}
          <div className="grid grid-cols-4 gap-2">
            {questions.map((q, index) => {
              const status = getQuestionClass(q);

              return (
                <button
                  key={q}
                  onClick={() => handleQuestionClick(index)}
                  className={`
                    w-full aspect-square rounded-lg font-semibold text-xs
                    flex items-center justify-center
                    transition-all duration-200
                    ${status === 'current'
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                      : status === 'attempted'
                      ? 'bg-green-500/20 text-green-600 dark:text-green-300 border border-green-500/40 hover:bg-green-500/30'
                      : 'bg-white/5 text-gray-600 dark:text-gray-400 border border-[var(--border-subtle)] hover:bg-white/10 dark:hover:bg-white/10'
                    }
                  `}
                >
                  {q}
                </button>
              );
            })}
          </div>

          {/* Legend */}
          <div className="space-y-2 mt-6 pt-4 border-t border-[var(--border-subtle)]">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Status</h4>

            <div className="space-y-2 text-xs">
              {/* Current */}
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-md bg-blue-600 flex-shrink-0 shadow-sm" />
                <span className="text-muted">Current</span>
              </div>

              {/* Attempted */}
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-md bg-green-500/20 border border-green-500/40 flex-shrink-0" />
                <span className="text-muted">Attempted</span>
              </div>

              {/* Unattempted */}
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-md bg-white/5 border border-[var(--border-subtle)] flex-shrink-0" />
                <span className="text-muted">Unattempted</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Back to Module Link */}
        <div className="px-4 sm:px-6 lg:px-8 py-4 border-t border-[var(--border-subtle)] bg-white/[0.01] flex-shrink-0">
          <Link
            to="/module"
            onClick={handleLinkClick}
            className="flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-muted hover:text-[var(--text-primary)] hover:bg-white/3 transition"
          >
            <FaHome className="w-5 h-5" />
            Back to Module
          </Link>
        </div>
      </aside>

      {/* Mobile Menu Toggle Button - Floating */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed bottom-6 right-6 z-30 w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center shadow-2xl hover:scale-110 active:scale-95 transition-all duration-200"
        aria-label="Open quiz navigator"
      >
        <svg
          className="w-6 h-6 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    </>
  );
};

export default QuizSidebar;
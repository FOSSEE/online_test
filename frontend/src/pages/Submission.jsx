import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FaCheck, FaTimes, FaExclamationTriangle } from 'react-icons/fa';
import Logo from '../components/ui/Logo';
import { getQuizSubmissionStatus, quitQuiz, getModeratorStatus } from '../api/api';
import { useAuthStore } from '../store/authStore';

const Submission = () => {
  const { answerpaperId } = useParams();
  const { user } = useAuthStore(); 
  const isTeacher = user?.is_moderator; 
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quitting, setQuitting] = useState(false);
  const [isModeratorActive, setIsModeratorActive] = useState(null);

  useEffect(() => {
    if (answerpaperId) {
      loadSubmissionStatus();
    }
  }, [answerpaperId]);

  useEffect(() => {
    const fetchModeratorStatus = async () => {
      if (user?.is_moderator) {
        try {
          const status = await getModeratorStatus();
          setIsModeratorActive(status.is_moderator_active);
        } catch (error) {
          console.error('Failed to fetch moderator status:', error);
          // Default to false if we can't fetch status
          setIsModeratorActive(false);
        }
      } else {
        setIsModeratorActive(false);
      }
    };

    fetchModeratorStatus();
  }, [user]);

  const loadSubmissionStatus = async () => {
    try {
      setLoading(true);
      const data = await getQuizSubmissionStatus(answerpaperId);
      setSubmission(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load submission status:', err);
      setError('Failed to load submission status');
    } finally {
      setLoading(false);
    }
  };

  const handleQuit = async () => {
    try {
      setQuitting(true);
      await quitQuiz(answerpaperId);
      // Reload status
      await loadSubmissionStatus();
    } catch (err) {
      console.error('Failed to quit quiz:', err);
      alert('Failed to quit quiz');
    } finally {
      setQuitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col relative grid-texture bg-gradient-to-b from-[var(--bg-1)] to-[var(--bg-2)]">
        <header className="px-8 py-4 border-b border-white/6 bg-gradient-to-b from-white/[0.01] to-transparent">
          <div className="flex items-center justify-between">
            <Logo />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading submission status...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error || !submission) {
    return (
      <div className="min-h-screen flex flex-col relative grid-texture bg-gradient-to-b from-[var(--bg-1)] to-[var(--bg-2)]">
        <header className="px-8 py-4 border-b border-white/6 bg-gradient-to-b from-white/[0.01] to-transparent">
          <div className="flex items-center justify-between">
            <Logo />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 mb-4">
              {error || 'Submission not found'}
            </div>
            <Link to={(isTeacher && isModeratorActive) ? "/teacher/courses" : "/courses"} className="text-indigo-400 hover:text-indigo-300">
              Back to Courses
            </Link>
          </div>
        </main>
      </div>
    );
  }

  const attemptedCount = submission.attempted_count || 0;
  const notAttemptedCount = submission.not_attempted_count || 0;

  return (
    <div className="min-h-screen flex flex-col relative grid-texture bg-gradient-to-b from-[var(--bg-1)] to-[var(--bg-2)]">
      {/* Header */}
      <header className="px-8 py-4 border-b border-white/6 bg-gradient-to-b from-white/[0.01] to-transparent">
        <div className="flex items-center justify-between">
          <Logo />
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-4xl w-full">
          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2">Submission Status</h1>
            <p className="text-gray-400 text-sm">Review your exam submission details</p>
          </div>

          {/* Status Table */}
          <div className="card-strong overflow-hidden mb-8">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left px-6 py-4 text-indigo-400 font-semibold uppercase tracking-wider text-sm">
                      Question
                    </th>
                    <th className="text-left px-6 py-4 text-indigo-400 font-semibold uppercase tracking-wider text-sm">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {submission.questions && submission.questions.map((question, index) => (
                    <tr
                      key={question.id}
                      className={`border-b border-white/5 hover:bg-white/[0.03] transition-colors ${index === submission.questions.length - 1 ? 'border-b-0' : ''
                        }`}
                    >
                      <td className="px-6 py-4 soft">{question.title}</td>
                      <td className="px-6 py-4">
                        {question.attempted ? (
                          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold tracking-wide bg-green-500/15 text-green-300 border border-green-500/30">
                            <FaCheck className="w-4 h-4" />
                            ATTEMPTED
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold tracking-wide bg-red-500/15 text-red-300 border border-red-500/30">
                            <FaTimes className="w-4 h-4" />
                            NOT ATTEMPTED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="card p-4 text-center">
              <div className="text-3xl font-bold text-green-400 mb-1">{attemptedCount}</div>
              <div className="text-sm muted">Questions Attempted</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-3xl font-bold text-red-400 mb-1">{notAttemptedCount}</div>
              <div className="text-sm muted">Questions Not Attempted</div>
            </div>
          </div>

          {/* Confirmation / Completion Box */}
          {['completed', 'quit'].includes(submission.status) ? (
            <div className="card p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center bg-green-500/20 border border-green-500/30">
                <FaCheck className="w-8 h-8 text-green-400" />
              </div>

              <p className="text-xl font-semibold text-white mb-2">Quiz Submitted Successfully</p>
              <p className="text-base muted mb-6">Your answers have been recorded for evaluation.</p>

              {submission.percent !== undefined && (
                <p className="text-2xl font-bold mb-6">Score: {submission.percent}%</p>
              )}

              <Link
                to={(isTeacher && isModeratorActive) ? "/teacher/courses" : "/courses"}
                className="bg-indigo-600 text-white px-10 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition text-lg inline-flex items-center gap-2"
              >  
                Back to Courses 
              </Link>
            </div>
          ) : (
            <div className="card p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center bg-yellow-500/20 border border-yellow-500/30">
                <FaExclamationTriangle className="w-8 h-8 text-yellow-400" />
              </div>

              <p className="text-lg soft mb-2">Your current answers are saved.</p>
              <p className="text-xl font-semibold text-white mb-2">Are you sure you wish to quit exam?</p>
              <p className="text-base muted mb-8">Be sure, as you won't be able to restart this exam.</p>

              <div className="flex justify-center gap-4 flex-wrap">
                <button
                  onClick={handleQuit}
                  disabled={quitting}
                  className="bg-green-600 text-white px-10 py-3 rounded-xl font-semibold hover:bg-green-700 transition text-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <FaCheck className="w-5 h-5" />
                  {quitting ? 'Quitting...' : 'Yes, Quit'}
                </button>
                <button
                  onClick={() => window.history.back()}
                  className="bg-red-600 text-white px-10 py-3 rounded-xl font-semibold hover:bg-red-700 transition text-lg flex items-center gap-2"
                >
                  <FaTimes className="w-5 h-5" />
                  No, Continue
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Submission;
import React from "react";
import { FaChevronLeft, FaUser } from "react-icons/fa";

const QuizStatisticsPanel = ({
  statsData,
  onBack,
  attempts,
  currentAttempt,
  onAttemptChange,
  loading,
}) => {
  if (!statsData) return null;
  const { quiz, total_attempts_count, statistics, message } = statsData;

  return (
    <div className="card-strong p-5 sm:p-6 min-h-[600px] border-2 border-[var(--border-strong)] rounded-2xl shadow-lg">
      {/* Header */}
      <div className="mb-6 flex items-start gap-4 pb-5 border-b-2 border-[var(--border-subtle)]">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
        >
          <FaChevronLeft className="w-4 h-4" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-xl sm:text-2xl font-bold line-clamp-2">Attempt {currentAttempt}</h2>
            <span className="text-[10px] px-2.5 py-1 rounded-lg border-2 bg-emerald-500/10 text-emerald-400 border-emerald-500/30 uppercase font-bold tracking-wider whitespace-nowrap">
              Statistics
            </span>
          </div>
          <div className="flex flex-wrap gap-4 text-xs muted">
            <div className="flex items-center gap-1.5">
              <FaUser className="w-2.5 h-2.5" />
              <span className="font-medium">Total Participants: {total_attempts_count}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Attempt Tabs */}
      {attempts && attempts.length > 0 && (
        <div className="flex bg-[var(--input-bg)] p-1.5 rounded-xl overflow-x-auto scrollbar-hide mb-6 border-2 border-[var(--border-strong)]">
          {[...attempts]
            .sort((a, b) => a.attempt_number - b.attempt_number)
            .map((attempt) => (
              <button
                key={attempt.id}
                onClick={() => onAttemptChange(attempt)}
                className={`flex-1 sm:flex-initial px-4 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 whitespace-nowrap ${currentAttempt === attempt.attempt_number
                  ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5'
                  }`}
                disabled={loading}
              >
                Attempt {attempt.attempt_number}
              </button>
            ))}
        </div>
      )}

      {/* Statistics Table or Message */}
      <div className="overflow-x-auto rounded-xl border-2 border-[var(--border-strong)]">
        {loading ? (
          <div className="text-center py-12 text-blue-400 font-bold text-base">Loading statistics...</div>
        ) : message ? (
          <div className="text-center py-12 text-yellow-400 font-bold text-base">{message}</div>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-blue-500/10 border-b-2 border-[var(--border-strong)]">
                <th className="px-4 py-3 text-left font-bold text-blue-400">#</th>
                <th className="px-4 py-3 text-left font-bold text-blue-400">Question</th>
                <th className="px-4 py-3 text-center font-bold text-blue-400">Type</th>
                <th className="px-4 py-3 text-center font-bold text-blue-400">Points</th>
                <th className="px-4 py-3 text-center font-bold text-blue-400">Total Attempts</th>
                <th className="px-4 py-3 text-center font-bold text-blue-400">Correct Attempts</th>
                <th className="px-4 py-3 text-center font-bold text-blue-400">% Correct</th>
              </tr>
            </thead>
            <tbody className="bg-[var(--card-bg)]">
              {statistics && statistics.length > 0 ? (
                statistics.map((q, idx) => (
                  <tr key={q.question.id} className="border-b border-[var(--border-subtle)] hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-center font-semibold">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium">{q.question.summary}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-2 py-1 rounded-lg bg-blue-500/10 text-blue-400 text-xs font-semibold">
                        {q.question.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-blue-400">{q.question.points}</td>
                    <td className="px-4 py-3 text-center font-semibold">{q.total_attempts}</td>
                    <td className="px-4 py-3 text-center font-semibold">{q.correct_attempts}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2.5 py-1 rounded-lg font-bold text-sm ${q.correct_percentage > 70 ? "bg-emerald-500/20 text-emerald-400" :
                        q.correct_percentage > 40 ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-red-500/20 text-red-400"
                        }`}>
                        {q.correct_percentage}%
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-muted font-medium">No statistics available for this attempt.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default QuizStatisticsPanel;
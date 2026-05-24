import React from 'react';
import { FaBookOpen, FaTimes } from 'react-icons/fa';
import { MdGrading } from "react-icons/md";

export default function GradingSystemDetail({ gradingSystem, onBack }) {
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-2">
      <div className="card-strong w-full max-w-2xl p-4 sm:p-6 relative max-h-[90vh] overflow-y-auto">
        {/* Close (Cross) Button */}
        <button
          type="button"
          className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border border-[var(--border-color)] bg-[var(--input-bg)] hover:bg-white/10 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all z-10"
          onClick={onBack}
          aria-label="Close"
        >
          <FaTimes />
        </button>
        
        {/* Header */}
        <div className="flex flex-row items-center gap-4 mb-4 sm:mt-0">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
            <MdGrading className="w-7 h-7 sm:w-8 sm:h-8 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">{gradingSystem.name}</h2>
            <p className="text-xs sm:text-sm muted line-clamp-2">{gradingSystem.description}</p>
          </div>
        </div>
        
        {/* Grade Ranges Table */}
        <div className="mt-4">
          <h3 className="font-semibold mb-2 text-base sm:text-lg">Grade Ranges</h3>
          <div className="overflow-x-auto rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)]">
            <table className="min-w-full text-xs sm:text-sm">
              <thead>
                <tr className="bg-white/5">
                  <th className="px-3 py-2 text-left font-semibold">Lower</th>
                  <th className="px-3 py-2 text-left font-semibold">Upper</th>
                  <th className="px-3 py-2 text-left font-semibold">Grade</th>
                  <th className="px-3 py-2 text-left font-semibold">Description</th>
                </tr>
              </thead>
              <tbody>
                {gradingSystem.grade_ranges && gradingSystem.grade_ranges.length > 0 ? (
                  gradingSystem.grade_ranges.map((gr, idx) => (
                    <tr key={idx} className="border-t border-[var(--border-color)] hover:bg-white/5 transition">
                      <td className="px-3 py-2">{gr.lower_limit}</td>
                      <td className="px-3 py-2">{gr.upper_limit}</td>
                      <td className="px-3 py-2 font-bold">{gr.grade}</td>
                      <td className="px-3 py-2">{gr.description || '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="px-3 py-4 text-center text-muted">
                      No grade ranges defined
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
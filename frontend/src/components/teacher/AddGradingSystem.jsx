import React, { useState, useEffect } from 'react';
import { FaBookOpen, FaTimes, FaPlus, FaMinus } from 'react-icons/fa';
import useGradingSystemStore from '../../store/teacherGradeStore';
import { MdGrading } from "react-icons/md";

export default function AddGradingSystem({ onCancel, gradingSystem = null, isEdit = false }) {
  const [form, setForm] = useState({ name: '', description: '' });
  const [ranges, setRanges] = useState([
    { lower_limit: '', upper_limit: '', grade: '', description: '' },
  ]);
  const { addGradingSystem, updateGradingSystem, loading, error } = useGradingSystemStore();

  
  useEffect(() => {
    if (isEdit && gradingSystem) {
      setForm({
        name: gradingSystem.name || '',
        description: gradingSystem.description || ''
      });
      
      
      if (gradingSystem.grade_ranges && gradingSystem.grade_ranges.length > 0) {
        setRanges(gradingSystem.grade_ranges.map(range => ({
          lower_limit: range.lower_limit ?? '',
          upper_limit: range.upper_limit ?? '',
          grade: range.grade || '',
          description: range.description || ''
        })));
      } else {
        setRanges([{ lower_limit: '', upper_limit: '', grade: '', description: '' }]);
      }
    }
  }, [isEdit, gradingSystem]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleRangeChange = (idx, e) => {
    const newRanges = [...ranges];
    newRanges[idx][e.target.name] = e.target.value;
    setRanges(newRanges);
  };

  const addRange = () =>
    setRanges([...ranges, { lower_limit: '', upper_limit: '', grade: '', description: '' }]);
  
  const removeRange = (idx) => {
    if (ranges.length > 1) {
      setRanges(ranges.filter((_, i) => i !== idx));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { 
      ...form, 
      grade_ranges: ranges.map(range => ({
        lower_limit: parseFloat(range.lower_limit),
        upper_limit: parseFloat(range.upper_limit),
        grade: range.grade,
        description: range.description
      }))
    };
    
    try {
      if (isEdit && gradingSystem) {
        await updateGradingSystem(gradingSystem.id, data);
      } else {
        await addGradingSystem(data);
      }
      onCancel();
    } catch (err) {
      console.error('Error saving grading system:', err);
    }
  };

  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-2">
      <div className="card-strong w-full max-w-2xl p-4 sm:p-6 relative max-h-[90vh] overflow-y-auto">
      
        <button
          type="button"
          className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border border-[var(--border-color)] bg-[var(--input-bg)] hover:bg-white/10 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all z-10"
          onClick={onCancel}
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
            <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
              {isEdit ? 'Edit Grading System' : 'Add Grading System'}
            </h2>
            <p className="text-xs sm:text-sm muted line-clamp-2">
              {isEdit ? 'Update the grading system details.' : 'Create a new grading system.'}
            </p>
          </div>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="flex flex-col gap-2">
            <input
              className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm"
              name="name"
              placeholder="Name"
              value={form.name}
              onChange={handleChange}
              required
            />
            <textarea
              className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm"
              name="description"
              placeholder="Description"
              value={form.description}
              onChange={handleChange}
              rows={5}
            />
          </div>
          
          {/* Grade Ranges */}
          <div>
            <h3 className="font-semibold mb-2 text-base sm:text-lg">Grade Ranges</h3>
            <div className="space-y-2">
              {ranges.map((range, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row gap-2 items-center bg-white/5 p-3 rounded-lg border border-[var(--border-color)] w-full"
                >
                  <input
                    className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm w-full sm:w-36"
                    name="lower_limit"
                    type="number"
                    step="0.01"
                    placeholder="Lower"
                    value={range.lower_limit}
                    onChange={e => handleRangeChange(idx, e)}
                    required
                  />
                  <input
                    className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm w-full sm:w-36"
                    name="upper_limit"
                    type="number"
                    step="0.01"
                    placeholder="Upper"
                    value={range.upper_limit}
                    onChange={e => handleRangeChange(idx, e)}
                    required
                  />
                  <input
                    className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm w-full sm:w-28"
                    name="grade"
                    placeholder="Grade"
                    value={range.grade}
                    onChange={e => handleRangeChange(idx, e)}
                    required
                  />
                  <input
                    className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm w-full sm:flex-1"
                    name="description"
                    placeholder="Description"
                    value={range.description}
                    onChange={e => handleRangeChange(idx, e)}
                  />
                  <button
                    type="button"
                    onClick={() => removeRange(idx)}
                    className="p-2 rounded-full border border-red-400 text-red-400 hover:bg-red-400/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Remove grade range"
                    disabled={ranges.length === 1}
                  >
                    <FaMinus />
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="text-red-500 text-sm bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              {error}
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex gap-2 justify-between items-center">
            <button
              type="button"
              onClick={addRange}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-violet-400 text-violet-400 hover:bg-violet-400/10 font-medium transition"
            >
              <FaPlus className="w-3 h-3" />
              Add Range
            </button>

            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition disabled:opacity-60 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? 'Saving...' : (isEdit ? 'Update' : 'Save')}
              </button>
              <button
                type="button"
                className="px-4 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/10 font-medium transition"
                onClick={onCancel}
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
import React, { useState, useEffect } from 'react';
import { FaBook, FaTimes } from 'react-icons/fa';
import useGradingSystemStore from '../../store/teacherGradeStore';
import { createCourse, updateCourse, getTeacherCourse } from '../../api/api';

export default function AddCourseModal({ onCancel, courseId = null, isEdit = false, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    enrollment: '',
    code: '',
    instructions: '',
    start_enroll_time: '',
    end_enroll_time: '',
    grading_system_id: '',
    view_grade: false,
    active: true,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  
  const { gradingSystems, loadGradingSystems, loading: gradingLoading } = useGradingSystemStore();

  useEffect(() => {
    loadGradingSystems();
  }, [loadGradingSystems]);

  useEffect(() => {
    if (isEdit && courseId) {
      loadCourse();
    }
    // eslint-disable-next-line
  }, [isEdit, courseId]);

  const loadCourse = async () => {
    try {
      setLoading(true);
      const course = await getTeacherCourse(courseId);
      setFormData({
        name: course.name || '',
        enrollment: course.enrollment || 'default',
        code: course.code || '',
        instructions: course.instructions || '',
        start_enroll_time: course.start_enroll_time ? new Date(course.start_enroll_time).toISOString().slice(0, 16) : '',
        end_enroll_time: course.end_enroll_time ? new Date(course.end_enroll_time).toISOString().slice(0, 16) : '',
        grading_system_id: course.grading_system_id || '',
        view_grade: course.view_grade || false,
        active: course.active !== undefined ? course.active : true,
      });
    } catch (err) {
      console.error('Failed to load course:', err);
      setError('Failed to load course data');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);

      const submitData = {
        ...formData,
        start_enroll_time: formData.start_enroll_time ? new Date(formData.start_enroll_time).toISOString() : null,
        end_enroll_time: formData.end_enroll_time ? new Date(formData.end_enroll_time).toISOString() : null,
      };

      if (isEdit && courseId) {
        await updateCourse(courseId, submitData);
      } else {
        await createCourse(submitData);
      }
      
      if (onSuccess) {
        onSuccess();
      }
      onCancel();
    } catch (err) {
      console.error('Failed to save course:', err);
      setError(err.response?.data?.error || 'Failed to save course');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2">
        <div className="card-strong w-full max-w-5xl p-6 relative rounded-2xl border-2 border-[var(--border-strong)]">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading course...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto custom-scrollbar">
      <div className="card-strong w-full max-w-5xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">
        
        {/* Close Button */}
        <button
          type="button"
          className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
          onClick={onCancel}
          aria-label="Close"
        >
          <FaTimes />
        </button>
        
        {/* Header */}
        <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border-2 border-blue-500/30">
            <FaBook className="w-6 h-6 sm:w-7 sm:h-7 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
              {isEdit ? 'Edit Course' : 'Add New Course'}
            </h2>
            <p className="text-xs sm:text-sm muted line-clamp-2">
              {isEdit ? 'Update course details and settings' : 'Create a new course with details and settings'}
            </p>
          </div>
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border-2 border-red-500/30 rounded-xl p-3 sm:p-4 text-red-300 mb-4 sm:mb-5 text-sm">
            {error}
          </div>
        )}
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
          <div className="grid lg:grid-cols-2 gap-5 sm:gap-6">
            {/* Left Column - Course Details */}
            <div className="space-y-4">
              <div>
                <h3 className="text-base sm:text-lg font-bold mb-1">Course Details</h3>
                <p className="text-xs sm:text-sm muted mb-4">Basic information about your course</p>
              </div>
              
              {/* Course Title */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-2">
                  Course Title *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="Enter course title"
                  className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                />
              </div>
              
              {/* Instructions */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-2">
                  Instructions
                </label>
                <textarea
                  name="instructions"
                  rows="11"
                  value={formData.instructions}
                  onChange={handleChange}
                  placeholder="Enter course instructions"
                  className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 resize-none text-sm transition-colors"
                />
              </div>
              
              {/* Code and Enrollment */}
              <div className="grid grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs sm:text-sm font-semibold mb-2">
                    Code
                  </label>
                  <input
                    type="text"
                    name="code"
                    value={formData.code}
                    onChange={handleChange}
                    placeholder="xxxx"
                    className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs sm:text-sm font-semibold mb-2">
                    Enrollment
                  </label>
                  <select
                    name="enrollment"
                    value={formData.enrollment}
                    onChange={handleChange}
                    className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                  >
                    <option value="">---------</option>
                    <option value="default">Enroll Request</option>
                    <option value="open">Open Enrollment</option>
                  </select>
                </div>
              </div>
            </div>
            
            {/* Right Column - Course Settings */}
            <div className="space-y-4">
              <div>
                <h3 className="text-base sm:text-lg font-bold mb-1">Course Settings</h3>
                <p className="text-xs sm:text-sm muted mb-4">Configure how your course works</p>
              </div>
              
              {/* Start Enrollment Date & Time */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-2">
                  Start Enrollment Date & Time
                </label>
                <input
                  type="datetime-local"
                  name="start_enroll_time"
                  value={formData.start_enroll_time}
                  onChange={handleChange}
                  className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                />
              </div>
              
              {/* End Enrollment Date & Time */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-2">
                  End Enrollment Date & Time
                </label>
                <input
                  type="datetime-local"
                  name="end_enroll_time"
                  value={formData.end_enroll_time}
                  onChange={handleChange}
                  className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                />
              </div>
              
              {/* Grading System */}
              <div>
                <label className="block text-xs sm:text-sm font-semibold mb-2">
                  Grading System
                </label>
                <select
                  name="grading_system_id"
                  value={formData.grading_system_id}
                  onChange={handleChange}
                  className="w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors"
                  disabled={gradingLoading}
                >
                  <option value="">---------</option>
                  {gradingSystems.map(gs => (
                    <option key={gs.id} value={gs.id}>
                      {gs.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs muted mt-1.5">Leave empty if not using a grading system</p>
                {gradingLoading && <p className="text-xs text-blue-400 mt-1.5">Loading grading systems...</p>}
              </div>
              
              {/* View Grade Toggle */}
              <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm sm:text-base font-semibold mb-1">View Grade</div>
                    <div className="text-xs muted">Allow students to view their grades</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                    <input
                      type="checkbox"
                      name="view_grade"
                      checked={formData.view_grade}
                      onChange={handleChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
              
              {/* Active Toggle */}
              <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm sm:text-base font-semibold mb-1">Active</div>
                    <div className="text-xs muted">Course ready for enrollment</div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                    <input
                      type="checkbox"
                      name="active"
                      checked={formData.active}
                      onChange={handleChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-2 sm:gap-3 justify-end pt-4 border-t-2 border-[var(--border-subtle)]">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-blue-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
              disabled={saving}
            >
              {saving ? 'Saving...' : (isEdit ? 'Update Course' : 'Create Course')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

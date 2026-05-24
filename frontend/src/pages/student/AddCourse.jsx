import React, { useState, useEffect, useMemo } from 'react';
import {
  FaSearch, FaTimes, FaBook, FaSpinner, FaCheckCircle,
  FaInfoCircle, FaUser, FaCalendarAlt, FaClock, FaExclamationTriangle,
  FaBan, FaHourglassHalf, FaLayerGroup
} from 'react-icons/fa';
import { AiOutlineClockCircle, AiOutlineBarChart } from 'react-icons/ai';
import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import CourseActionButtons from '../../components/student/CourseActionButtons';
import useCourseStore from '../../store/student/courseStore';
import toast from 'react-hot-toast';


const AddNewCourseStudent = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCourse, setExpandedCourse] = useState(null);

  const {
    newCourses,
    loading,
    error,
    enrollmentLoading,
    enrollmentError,
    enrollmentSuccess,
    searchCourses,
    clearSearch,
    requestEnrollment,
    selfEnroll,
    clearEnrollmentMessages
  } = useCourseStore();


  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      searchCourses(searchTerm.trim());
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    clearSearch();
  };

  const handleEnroll = async (course) => {
    clearEnrollmentMessages();

    let result;

    // Determine the enrollment type based on status
    if (course.enrollment_status === 'can_enroll_open') {
      // Self-enrollment
      result = await selfEnroll(course.id);
    } else if (course.enrollment_status === 'can_enroll_request') {
      // Request enrollment
      result = await requestEnrollment(course.id);
    } else {
      toast.error('Enrollment is not available for this course');
      return;
    }

    // Handle result
    if (result.success) {
      toast.success(result.data.message);
      // Optionally refresh the search results
      if (searchTerm.trim()) {
        setTimeout(() => {
          searchCourses(searchTerm.trim());
        }, 1000);
      }
    } else {
      toast.error(result.error);
    }
  };

  const toggleCourseDetails = (courseId) => {
    setExpandedCourse(expandedCourse === courseId ? null : courseId);
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Function to render enrollment button/badge based on status
  const renderEnrollmentAction = (course) => {
    const status = course.enrollment_status;

    switch (status) {
      case 'enrolled':
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-green-600/20 text-green-400 border border-green-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaCheckCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Enrolled</span>
          </div>
        );

      case 'request_pending':
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-yellow-600/20 text-yellow-400 border border-yellow-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaHourglassHalf className="w-4 h-4" />
            <span className="hidden sm:inline">Request Pending</span>
          </div>
        );

      case 'request_rejected':
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-red-600/20 text-red-400 border border-red-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaBan className="w-4 h-4" />
            <span className="hidden sm:inline">Request Rejected</span>
          </div>
        );

      case 'can_enroll_open':
        return (
          <button
            onClick={() => handleEnroll(course)}
            disabled={enrollmentLoading}
            className="px-3 sm:px-6 py-2 sm:py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg sm:rounded-xl shadow-lg shadow-blue-600/25 hover:shadow-xl hover:shadow-blue-600/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-95 flex-shrink-0"
          >
            {enrollmentLoading ? (
              <>
                <FaSpinner className="animate-spin w-4 h-4" />
                <span className="hidden sm:inline">Enrolling...</span>
              </>
            ) : (
              <>
                <FaCheckCircle className="w-4 h-4" />
                <span className="hidden sm:inline">Enroll Now</span>
              </>
            )}
          </button>
        );

      case 'can_enroll_request':
        return (
          <button
            onClick={() => handleEnroll(course)}
            disabled={enrollmentLoading}
            className="px-3 sm:px-6 py-2 sm:py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-lg sm:rounded-xl shadow-lg shadow-purple-600/25 hover:shadow-xl hover:shadow-purple-600/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 active:scale-95 flex-shrink-0"
          >
            {enrollmentLoading ? (
              <>
                <FaSpinner className="animate-spin w-4 h-4" />
                <span className="hidden sm:inline">Requesting...</span>
              </>
            ) : (
              <>
                <FaHourglassHalf className="w-4 h-4" />
                <span className="hidden sm:inline">Request Enrollment</span>
              </>
            )}
          </button>
        );

      case 'no_enrollment_allowed':
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-gray-600/20 text-gray-400 border border-gray-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaBan className="w-4 h-4" />
            <span className="hidden sm:inline">Enrollment Closed</span>
          </div>
        );

      case 'inactive_course':
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-red-600/20 text-red-400 border border-red-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaExclamationTriangle className="w-4 h-4" />
            <span className="hidden sm:inline">Inactive Course</span>
          </div>
        );

      default:
        return (
          <div className="px-3 sm:px-6 py-2 sm:py-2.5 bg-gray-600/20 text-gray-400 border border-gray-500/30 text-sm font-semibold rounded-lg sm:rounded-xl flex items-center justify-center gap-2 flex-shrink-0">
            <FaInfoCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Unknown Status</span>
          </div>
        );
    }
  };

  return (
    <div className="flex min-h-screen relative grid-texture">
      <Sidebar />
      <main className="flex-1 w-full lg:w-auto">
        <Header isAuth />
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Page Header */}
          <div className="mb-6 lg:mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Courses</h1>
            <p className="text-sm muted">Browse, enroll, and manage your learning courses</p>
          </div>

          {/* Action Buttons */}
          <CourseActionButtons activeButton="create" />

          {/* Main Content Card */}
          <div className="card-strong p-4 sm:p-5 lg:p-6 min-h-[500px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
            {/* Search Section */}
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                  <FaSearch className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-bold mb-0.5">Search for Courses</h2>
                  <p className="text-xs sm:text-sm muted">Browse and explore new courses</p>
                </div>
              </div>

              <form className="flex flex-row gap-2 sm:gap-3 mt-5" onSubmit={handleSearch}>
                <div className="relative flex-1">
                  <input
                    type="text"
                    className="input input-bordered w-full pl-10 pr-10 py-3 text-sm border-2 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all rounded-xl"
                    placeholder="Enter course code (e.g., CS101, 0002)"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                  <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-3.5 h-3.5" />
                  {searchTerm && (
                    <button
                      type="button"
                      onClick={() => setSearchTerm('')}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                    >
                      <FaTimes className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                <div className="flex gap-2 sm:gap-3">
                  <button
                    type="submit"
                    disabled={!searchTerm.trim() || loading}
                    className="flex-1 sm:flex-none px-4 sm:px-7 py-3 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white text-sm font-bold rounded-xl shadow-xl shadow-purple-600/30 hover:shadow-2xl hover:shadow-purple-600/40 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 flex items-center justify-center gap-2.5 border-2 border-purple-500/50"
                  >
                    {loading ? (
                      <>
                        <FaSpinner className="animate-spin w-4 h-4" />
                        <span className="hidden sm:inline">Searching...</span>
                      </>
                    ) : (
                      <>
                        <FaSearch className="w-4 h-4" />
                        <span className="hidden sm:inline">Search</span>
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={handleClearSearch}
                    disabled={loading || (newCourses.length === 0 && !searchTerm)}
                    className="flex-1 sm:flex-none px-4 sm:px-7 py-3 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600 text-white text-sm font-bold rounded-xl shadow-xl shadow-red-600/30 hover:shadow-2xl hover:shadow-red-600/40 transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed active:scale-95 flex items-center justify-center gap-2.5 border-2 border-red-500/50"
                  >
                    <FaTimes className="w-4 h-4" />
                    <span className="hidden sm:inline">Clear</span>
                  </button>
                </div>
              </form>

              {/* Search Tips */}
              <div className="mt-5 p-4 bg-blue-500/10 border-2 border-blue-500/30 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                    <FaInfoCircle className="text-blue-400 w-4 h-4" />
                  </div>
                  <div className="text-xs sm:text-sm text-[var(--text-primary)]">
                    <span className="font-bold text-blue-500 dark:text-blue-400">Search Tips:</span> Enter the exact course code to find available courses.
                    Contact your instructor if you need the course code.
                  </div>
                </div>
              </div>

              {/* Enrollment Success/Error Messages */}
              {enrollmentSuccess && (
                <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg animate-fade-in">
                  <div className="flex items-center gap-2">
                    <FaCheckCircle className="text-green-600 dark:text-green-400 flex-shrink-0" />
                    <p className="text-sm text-green-700 dark:text-green-300">{enrollmentSuccess}</p>
                  </div>
                </div>
              )}

              {enrollmentError && (
                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg animate-fade-in">
                  <div className="flex items-center gap-2">
                    <FaExclamationTriangle className="text-red-600 dark:text-red-400 flex-shrink-0" />
                    <p className="text-sm text-red-700 dark:text-red-300">{enrollmentError}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="relative">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-t-4 border-blue-500"></div>
                  <FaBook className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-blue-400 text-xl" />
                </div>
                <p className="mt-4 text-sm muted">Searching for courses...</p>
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center animate-fade-in">
                <div className="flex items-center justify-center gap-2 text-red-600 dark:text-red-300 mb-2">
                  <FaTimes className="w-5 h-5" />
                  <span className="font-semibold text-lg">Error</span>
                </div>
                <p className="text-red-700 dark:text-red-300">{error}</p>
              </div>
            )}

            {/* Empty State - No search yet */}
            {!loading && !error && newCourses.length === 0 && !searchTerm && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-5 p-8 bg-gradient-to-br from-purple-500/15 to-blue-500/15 rounded-3xl border-2 border-purple-500/30">
                  <FaSearch className="w-16 h-16 text-purple-400" />
                </div>
                <h3 className="text-2xl font-bold mb-3 text-[var(--text-primary)]">Start Your Search</h3>
                <p className="text-sm muted max-w-md leading-relaxed">
                  Enter a course code above to discover new courses and expand your learning opportunities.
                </p>
              </div>
            )}

            {/* Empty State - No results */}
            {!loading && !error && newCourses.length === 0 && searchTerm && (
              <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
                <div className="mb-4 p-6 bg-red-500/10 rounded-full">
                  <FaBook className="w-12 h-12 text-red-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">No Courses Found</h3>
                <p className="text-sm muted max-w-md mb-4">
                  We couldn't find any courses matching "<span className="font-semibold text-[var(--text-primary)]">{searchTerm}</span>".
                  Please check the course code and try again.
                </p>
                <button
                  onClick={handleClearSearch}
                  className="btn btn-info px-6 py-2"
                >
                  Clear Search
                </button>
              </div>
            )}

            {/* Course Results */}
            {!loading && !error && newCourses.length > 0 && (
              <div className="space-y-5 animate-fade-in">
                <div className="mb-5 pb-4 border-b-2 border-[var(--border-subtle)] flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-green-500/10 border-2 border-green-500/30 flex items-center justify-center">
                      <FaCheckCircle className="w-5 h-5 text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold mb-0.5">Search Results</h3>
                      <p className="text-sm muted">Found {newCourses.length} course{newCourses.length > 1 ? 's' : ''}</p>
                    </div>
                  </div>
                </div>

                {newCourses.map((item) => {
                  const course = item.data;
                  const isExpanded = expandedCourse === course.id;

                  return (
                    <div
                      key={course.id}
                      className="card-strong p-5 sm:p-6 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group bg-[var(--surface)] hover:shadow-md rounded-xl"
                    >
                      {/* Course Header and Enrollment Action */}
                      <div className="flex flex-row items-center justify-between gap-3 sm:gap-4 mb-5">
                        <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/15 flex items-center justify-center flex-shrink-0 border-2 border-blue-500/30 group-hover:border-blue-500/50 group-hover:scale-110 transition-all duration-300">
                            <FaBook className="w-6 h-6 sm:w-7 sm:h-7 text-blue-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              <h3 className="font-bold text-base sm:text-lg line-clamp-1 group-hover:text-blue-400 transition-colors duration-300">
                                {course.name}
                              </h3>
                            </div>
                            {course.code && (
                              <p className="text-xs sm:text-sm muted mb-2 sm:mb-3 line-clamp-2">
                                Code: {course.code}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Dynamic Enrollment Action */}
                        {renderEnrollmentAction(course)}
                      </div>

                      {/* Course Metadata */}
                      <div className="mb-4">
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                          {course.instructor && (
                            <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                              <FaUser className="w-4 h-4 text-purple-500 dark:text-purple-400 flex-shrink-0" />
                              <span className="truncate">
                                <span className="font-semibold">Instructor:</span> {course.instructor}
                              </span>
                            </div>
                          )}

                          <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                            <FaCalendarAlt className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                            <span className="truncate">
                              <span className="font-semibold">Start:</span> {formatDateTime(course.start_date)}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                            <FaCalendarAlt className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
                            <span className="truncate">
                              <span className="font-semibold">End:</span> {formatDateTime(course.end_date)}
                            </span>
                          </div>

                          {course.modules && (
                            <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                              <FaLayerGroup className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                              <span>
                                <span className="font-semibold">Modules:</span> {course.modules.length}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Course Details Toggle */}
                      <button
                        onClick={() => toggleCourseDetails(course.id)}
                        className="w-full py-2.5 px-4 bg-[var(--input-bg)] hover:bg-purple-500/10 border-2 border-[var(--border-color)] hover:border-purple-500/30 rounded-xl transition-all duration-300 text-sm font-semibold flex items-center justify-between mb-4 text-[var(--text-primary)] hover:text-purple-400"
                      >
                        <span>{isExpanded ? 'Hide Details' : 'View Details'}</span>
                        <svg
                          className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          strokeWidth="2"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {/* Expandable Course Details */}
                      {isExpanded && (
                        <div className="animate-fade-in space-y-5 pt-5 border-t-2 border-[var(--border-subtle)]">
                          {/* Instructions */}
                          {course.instructions && (
                            <div>
                              <h4 className="text-sm sm:text-base font-bold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
                                <div className="w-6 h-6 rounded-lg bg-yellow-500/15 border border-yellow-500/30 flex items-center justify-center">
                                  <FaInfoCircle className="text-yellow-400 w-3.5 h-3.5" />
                                </div>
                                Course Instructions
                              </h4>
                              <div className="p-4 bg-[var(--input-bg)] border border-[var(--border-color)] rounded-xl text-sm text-[var(--text-secondary)] leading-relaxed">
                                {course.instructions}
                              </div>
                            </div>
                          )}

                          {/* Course Modules */}
                          {course.modules && course.modules.length > 0 && (
                            <div>
                              <h4 className="text-sm sm:text-base font-bold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
                                <div className="w-6 h-6 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                                  <FaBook className="text-blue-400 w-3.5 h-3.5" />
                                </div>
                                Course Content ({course.modules.length} Modules)
                              </h4>
                              <div className="space-y-2.5">
                                {course.modules.map((mod, index) => (
                                  <div
                                    key={mod.id}
                                    className="p-3 sm:p-4 bg-[var(--input-bg)] hover:bg-blue-500/5 border border-[var(--border-color)] hover:border-blue-500/30 rounded-xl transition-all duration-300 flex items-center gap-3 group"
                                  >
                                    <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center flex-shrink-0 text-xs font-bold text-blue-400 group-hover:scale-110 transition-transform duration-300">
                                      {index + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors duration-300">{mod.name}</p>
                                      {mod.description && (
                                        <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-2">{mod.description}</p>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          {/* Progress Info */}
                          {course.completion_percent !== undefined && course.completion_percent > 0 && (
                            <div>
                              <h4 className="text-sm sm:text-base font-bold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
                                <div className="w-6 h-6 rounded-lg bg-green-500/15 border border-green-500/30 flex items-center justify-center">
                                  <AiOutlineBarChart className="text-green-400 w-3.5 h-3.5" />
                                </div>
                                Course Progress
                              </h4>
                              <div className="flex items-center gap-3">
                                <div className="flex-1 bg-[var(--input-bg)] border border-[var(--border-color)] rounded-full h-3 overflow-hidden">
                                  <div
                                    className="bg-gradient-to-r from-blue-500 to-green-500 h-full transition-all duration-500 rounded-full"
                                    style={{ width: `${course.completion_percent || 0}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm font-semibold text-green-400 whitespace-nowrap">
                                  {course.completion_percent || 0}%
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AddNewCourseStudent;
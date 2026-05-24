import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaBook, FaUserFriends, FaEllipsisV, FaLayerGroup, FaCalendar, FaSearch } from 'react-icons/fa';
import { VscLibrary } from "react-icons/vsc";
import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import CourseActionButtons from '../../components/student/CourseActionButtons';
import useCourseStore from '../../store/student/courseStore';


const CourseStudent = () => {
  const { courses, loading, error, fetchCourses } = useCourseStore();
  
  const [activeTab, setActiveTab] = useState('All Courses');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);


  const getCourseStatus = (course) => {
    // If the course active flag from backend is true, display 'Active', otherwise 'Inactive'
    return course.active ? 'Active' : 'Inactive';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'Inactive':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const handleSearch = (e) => setSearchQuery(e.target.value);

  const filteredCourses = courses.filter((item) => {
    const course = item.data;
    const status = getCourseStatus(course);
    
    // Text search (by name or code)
    const matchesSearch = course.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          course.code?.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Tab filter
    const matchesTab = activeTab === 'All Courses' || activeTab === status;
    
    return matchesSearch && matchesTab;
  });

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
          <CourseActionButtons activeButton="enrolled" />

          {/* Course Library Section */}
          <div className="card-strong p-4 sm:p-5 lg:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
            <div className="mb-5 sm:mb-7 pb-4 border-b-2 border-[var(--border-subtle)] flex items-center gap-3">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                <VscLibrary className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-bold mb-0.5">Course Library</h2>
                <p className="text-xs sm:text-sm muted">Browse and manage all your courses</p>
              </div>
            </div>

            
            <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 sm:gap-4 mb-6">
              <div className="flex bg-[var(--input-bg)] p-1.5 rounded-xl overflow-x-auto scrollbar-hide border-2 border-[var(--border-strong)]">
                  {['All Courses', 'Active'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 sm:flex-initial px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 whitespace-nowrap ${activeTab === tab
                            ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                            : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5'
                            }`}
                    >
                  
                    {tab}
                  </button>
                ))}
              </div>
              
              {/* Search Bar */}
              <div className="flex gap-2 sm:gap-3 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-3.5 h-3.5 transition-colors" />
                  <input
                    type="text"
                    placeholder="Search courses..."
                    value={searchQuery}
                    onChange={handleSearch}
                    className="w-full pl-9 pr-3 sm:pr-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              </div>
            )}

            {/* Error State */}
            {error && !loading && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 text-center">
                {error}
              </div>
            )}

            {/* Course List */}
            {!loading && !error && (
              <div className="space-y-3 sm:space-y-4">
                {/* 1. Change from courses.length to filteredCourses.length */}
                {filteredCourses.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="inline-block p-5 bg-blue-500/10 rounded-full mb-4">
                      <FaBook className="w-12 h-12 text-blue-400 opacity-50" />
                    </div>
                    <p className="text-lg font-semibold text-[var(--text-secondary)] mb-2">No courses found</p>
                    <p className="text-sm muted">
                      {courses.length === 0 
                        ? "Start by enrolling in your first course" 
                        : "No courses match your search or filter criteria"}
                    </p>
                  </div>
                ) : (
                  // 2. Change from courses.map to filteredCourses.map
                  filteredCourses.map((item) => {
                    const course = item.data;
                    const modulesCount = course.modules ? course.modules.length : 0;
                    const status = getCourseStatus(course);

                    return (
                      <div
                        key={course.id}
                        className="card-strong p-4 sm:p-5 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group rounded-xl hover:shadow-md bg-[var(--surface)]"
                      >
                        <div className="flex flex-row flex-wrap items-center gap-3 sm:gap-4">
                          {/* Icon */}
                          <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/15 flex items-center justify-center flex-shrink-0 border-2 border-blue-500/30 group-hover:border-blue-500/50 group-hover:scale-110 transition-all duration-300">
                            <FaBook className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                          </div>
                          {/* Content */}
                          <div className="flex-1 min-w-0 w-full">
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              <h3 className="font-bold text-base sm:text-lg line-clamp-1 group-hover:text-blue-400 transition-colors duration-300">
                                {course.name}
                              </h3>
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${status === 'Active'
                                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                                  : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                                  }`}
                              >
                                {getCourseStatus(course)}
                              </span>

                            </div>
                            {course.code && (
                              <p className="text-xs sm:text-sm muted mb-2 sm:mb-3 line-clamp-2">Code: {course.code}</p>
                            )}
                            <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-4 text-xs muted">
                              <div className="flex items-center gap-1.5">
                                <FaLayerGroup className="w-w-2 h-2 sm:w-3 sm:h-3 flex-shrink-0" />
                                <span>{modulesCount} modules</span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <FaUserFriends className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0" />
                                <span>{course.students_count || 0} students</span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{item.completion_percentage ?? 0}% complete</span>
                              </div>
                              {course.end_date && (

                                <div className="flex items-center gap-1.5 text-red-300">
                                  <FaCalendar className="w-2 h-2 sm:w-2.5 sm:h-2.5 flex-shrink-0" />
                                  <span>{new Date(course.end_date).toLocaleDateString()}</span>
                                </div>

                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto sm:self-start">
                            <Link
                              to={`/courses/${course.id}/manage`}
                              className="flex-1 sm:flex-none px-4 sm:px-5 py-2.5 border-2 border-blue-500/30 bg-blue-500/10 rounded-lg text-xs sm:text-sm font-semibold text-blue-400 hover:border-blue-500/50 hover:bg-blue-500/20 hover:shadow-lg hover:shadow-blue-500/20 active:scale-95 transition-all duration-300 text-center whitespace-nowrap"
                            >
                              Manage
                            </Link>

                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default CourseStudent;
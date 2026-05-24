import React, { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import { useTeacherDashboardStore } from '../../store/teacherDashboardStore';
import { toggleModeratorRole } from '../../api/api';
import {
  FaBook,
  FaPuzzlePiece,
  FaLayerGroup,
} from 'react-icons/fa';

const DashboardTeachers = () => {
  const navigate = useNavigate();
  const {
    dashboardData,
    loading,
    error,
    errorDetails,
    loadDashboard,
    message,
    clearMessage,
  } = useTeacherDashboardStore();

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      loadDashboard();
    }
  }, [loadDashboard]);


  useEffect(() => {
    if (message) {
      alert(message);
      clearMessage();
    }
  }, [message, clearMessage]);

  // Stats config for UI
  const stats = [
    {
      label: 'Total Courses',
      value: dashboardData?.total_courses ?? 0,
      icon: (
        <FaBook className="w-6 h-6" />
      ),
      color: 'rgb(234, 179, 8)',
    },
    {
      label: 'Active Courses',
      value: dashboardData?.active_courses ?? 0,
      icon: (
        <FaBook className="w-6 h-6" />
      ),
      color: 'rgb(34, 197, 94)',
    },
    {
      label: 'Students',
      value: dashboardData?.total_students ?? 0,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      color: 'rgb(59, 130, 246)',
    },
    {
      label: 'Avg. Completion',
      value: `${dashboardData?.avg_completion ?? 0}%`,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'rgb(249, 115, 22)',
    },
  ];

  // Loading and error states
  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <TeacherSidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading dashboard...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const handleSwitchToTeacher = async () => {
    try {
      const response = await toggleModeratorRole();
      if (response.success && response.is_moderator_active) {
        // Reload the dashboard after switching
        window.location.reload();
      }
    } catch (err) {
      console.error('Failed to switch to teacher mode:', err);
    }
  };

  if (error || !dashboardData) {
    // Check if user is in student mode and can toggle
    const canToggle = errorDetails?.can_toggle === true;
    const isModeratorDesignation = errorDetails?.is_moderator_designation === true;

    return (
      <div className="flex min-h-screen relative grid-texture">
        <TeacherSidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="text-center max-w-md">
              <div className={`${canToggle ? 'bg-amber-500/10 border-amber-500/30' : 'bg-red-500/10 border-red-500/30'} border rounded-lg p-6 mb-4`}>
                <div className={`${canToggle ? 'text-amber-300' : 'text-red-300'} mb-4`}>
                  <svg className="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="font-semibold text-lg mb-2">{error || 'Failed to load dashboard'}</p>
                  {canToggle && (
                    <p className="text-sm opacity-90">
                      You are currently in student view. Switch to teacher view to access the teacher dashboard.
                    </p>
                  )}
                </div>
                {canToggle ? (
                  <button
                    onClick={handleSwitchToTeacher}
                    className="bg-amber-600 hover:bg-amber-700 text-white px-6 py-3 rounded-lg font-semibold transition w-full mb-3"
                  >
                    Switch To Teacher View
                  </button>
                ) : (
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition w-full mb-3"
                  >
                    Go To Student Dashboard
                  </button>
                )}
                <button
                  onClick={loadDashboard}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition w-full"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Use dashboardData for events, students, courses, etc.
  const recentEvents = dashboardData.upcoming_quizzes || [];
  const topStudents = dashboardData.top_students || [];
  const courses = dashboardData.recent_courses || [];

  return (
    <div className="flex min-h-screen relative grid-texture">
      <TeacherSidebar />
      <main className="flex-1 w-full lg:w-auto">
        <Header isAuth />
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Header Section */}
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4 mb-6 lg:mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold mb-2">Dashboard</h1>
              <p className="muted text-sm">
                Welcome back, {dashboardData.teacher_name || 'Teacher'}! Here&apos;s what&apos;s happening with your courses and quizzes
              </p>
            </div>

          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 lg:mb-8">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="card p-4 sm:p-5 lg:p-6 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden"

              >
                {/* Subtle background glow */}
                <div
                  className="absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl opacity-20 group-hover:opacity-40 transition-opacity duration-300"
                  style={{ background: stat.color }}
                />

                <div className="relative flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                  <div className="flex-1 order-2 sm:order-1">
                    <p className="muted text-xs sm:text-sm mb-1.5 font-medium">{stat.label}</p>
                    <p className="text-2xl sm:text-3xl font-bold" style={{ color: stat.color }}>{stat.value}</p>
                  </div>
                  <div
                    className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center flex-shrink-0 order-1 sm:order-2 group-hover:scale-110 transition-transform duration-300"
                    style={{
                      background: `${stat.color}1A`,
                      border: `2px solid ${stat.color}33`,
                      color: stat.color,
                    }}
                  >
                    {stat.icon}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Content Grid */}
          <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 mb-6 lg:mb-8">
            {/* Recent Events */}
            <div className="lg:col-span-2 card p-5 sm:p-6 rounded-2xl border-2 border-[var(--border-subtle)] shadow-lg shadow-emerald-500/5">
              <div className="mb-4 sm:mb-6 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-bold mb-0.5">Recent Events</h2>
                  <p className="text-xs sm:text-sm muted">Manage your upcoming active quiz & exercise events</p>
                </div>
              </div>
              <div className="space-y-3 sm:space-y-4">
                {recentEvents.length > 0 ? recentEvents.map((event, index) => (
                  <div
                    key={index}
                    className={`card-strong p-4 sm:p-5 rounded-xl hover:shadow-md hover:bg-white/[0.03] transition-all duration-300 group ${event.is_exercise ? 'hover:border-purple-500' : 'hover:border-green-500'
                      }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                      <div className="flex gap-3 sm:gap-4 flex-1">
                        <div
                          className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300 border-2 ${event.is_exercise
                            ? 'bg-purple-500/15 border-purple-500/30'
                            : 'bg-green-500/15 border-green-500/30'
                            }`}
                        >
                          {event.is_exercise ? (
                            <FaPuzzlePiece className="w-5 h-5 sm:w-6 sm:h-6 text-purple-500 dark:text-purple-400" />
                          ) : (
                            <svg className="w-5 h-5 sm:w-6 sm:h-6 text-green-500 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-base sm:text-lg mb-1 flex items-center gap-2">
                            <span className="truncate">{event.name}</span>
                            <span className={`px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-lg border-2 text-[10px] sm:text-xs font-bold whitespace-nowrap flex-shrink-0 ${event.is_exercise
                              ? 'bg-purple-500/10 text-purple-500 border-purple-500/20'
                              : 'bg-green-500/10 text-green-500 border-green-500/20'
                              } `}>
                              {event.is_exercise ? 'Exercise' : 'Quiz'}
                            </span>
                          </h3>
                          <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm muted">
                            <div className="flex items-center gap-1.5">

                              <FaBook className="w-2.5 h-2.5 sm:w-3 sm:h-3 " />
                              {event.course_name}
                            </div>
                            <div className="flex items-center gap-1.5">
                              <FaLayerGroup className="w-2.5 h-2.5 sm:w-3 sm:h-3 " />
                              {event.module_name}
                            </div>
                          </div>
                        </div>
                      </div>
                      {event.course_id ? (
                        <Link
                          to={`/teacher/courses/${event.course_id}/manage`}
                          className="w-full sm:w-auto border border-[var(--border-color)] px-4 sm:px-5 py-2 rounded-lg text-xs sm:text-sm font-semibold hover:bg-[var(--input-bg)] transition whitespace-nowrap text-center"
                        >
                          Manage
                        </Link>
                      ) : (
                        <span className="w-full sm:w-auto border border-[var(--border-color)] px-4 sm:px-5 py-2 rounded-lg text-xs sm:text-sm font-semibold text-muted opacity-50 cursor-not-allowed whitespace-nowrap text-center">
                          Manage
                        </span>
                      )}
                    </div>
                  </div>
                )) : (
                  <div className="card-strong p-8 text-center rounded-xl">
                    <div className="inline-block p-4 bg-emerald-500/10 rounded-full mb-3">
                      <svg className="w-8 h-8 text-emerald-400 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <p className="text-muted font-medium">No upcoming recent events</p>
                  </div>
                )}
              </div>
            </div>

            {/* Top Students */}
            <div className="card p-5 sm:p-6 rounded-2xl border-b-2 border-[var(--border-subtle)] shadow-lg shadow-purple-500/5">
              <div className="mb-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border-2 border-purple-500/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-bold mb-0.5">Top Students</h2>
                  <p className="text-xs sm:text-sm muted">Students with highest quiz scores</p>
                </div>
              </div>
              <div className="space-y-4">
                {topStudents.length > 0 ? topStudents.map((student, index) => (
                  <div key={index} className="flex items-center gap-2 sm:gap-3">
                    <div className="text-base sm:text-lg font-bold muted w-5 sm:w-6">{index + 1}</div>
                    <img
                      src={`https://ui-avatars.com/api/?name=${student.name}&background=random&color=fff&size=128`}
                      className="w-8 h-8 sm:w-10 sm:h-10 rounded-full flex-shrink-0"
                      alt={student.name}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm sm:text-base truncate">{student.name}</div>
                      <div className="text-xs muted truncate">{student.subject}</div>
                    </div>
                    <div className="flex items-center gap-1 text-orange-400 font-bold text-xs sm:text-sm">
                      <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {student.score}
                    </div>
                  </div>
                )) : (
                  <div className="text-center text-muted py-4">
                    No student data available
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Courses Section */}
          <section
            className="
              rounded-2xl
              border-2 border-[var(--border-strong)]
              card
              hover:border-blue-500/70 dark:hover:border-blue-500/50 hover:shadow-lg
              p-5 sm:p-6 lg:p-8
            "
          >
            <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 mb-6 sm:mb-8 pb-4 border-b-2 border-[var(--border-subtle)]">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-9 h-9 sm:w-10 sm:h-10 lg:w-12 lg:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                  <FaBook className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-[var(--text-primary)] truncate">
                    Courses
                  </h2>
                  <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-0.5 truncate">
                    Your recently created courses
                  </p>
                </div>
              </div>
              <span className="text-xs sm:text-sm font-semibold text-[var(--text-secondary)] px-3 py-1.5 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)] whitespace-nowrap">
                {courses.length} total
              </span>
            </header>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-5 lg:gap-6">
              {courses.length > 0 ? courses.map((course, index) => (
                <Link
                  key={course.id}
                  to={`/teacher/courses/${course.id}/manage`}
                  className="
                    group relative flex flex-col rounded-xl
                    border-2 border-[var(--border-color)]
                    card-strong
                    p-4 sm:p-5
                    transition-all duration-300
                    hover:-translate-y-1
                    hover:shadow-lg
                    hover:border-blue-500/30
                  "
                >
                  <h3 className="text-sm sm:text-base font-bold leading-snug line-clamp-2 mb-1.5 text-[var(--text-primary)] group-hover:text-blue-400 transition-colors duration-300">
                    {course.name}
                  </h3>

                  <div className="flex justify-between text-[10px] sm:text-[11px] text-[var(--text-muted)] mb-4 sm:mb-5 gap-2">
                    <span className="truncate flex items-center gap-1">
                      <svg className="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                      </svg>
                      {course.students_count} students
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs mb-3 gap-2 sm:mb-4">
                    <span className="text-[var(--text-muted)] flex items-center gap-1.5 truncate">
                      <FaLayerGroup className="w-3 h-3 text-cyan-400" />
                      <span className="truncate">{course.modules_count} modules</span>
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${course.active
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                        : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                        }`}
                    >
                      {course.active ? 'Active' : 'Inactive'}
                    </span>

                  </div>
                  <div className="mb-4 sm:mb-5">
                    <div className="flex justify-between text-[10px] sm:text-[11px] mb-2">
                      <span className="text-[var(--text-muted)] font-medium">
                        Completion Rate
                      </span>
                      <span className="text-[var(--text-primary)] font-bold">
                        {course.completion_rate ?? 0}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-[var(--input-bg)] border border-[var(--border-color)] overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700 bg-blue-500"
                        style={{ width: `${course.completion_rate ?? 0}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex justify-between text-[10px] sm:text-[11px] text-[var(--text-muted)] mb-4 sm:mb-5 gap-2">
                    <span className="truncate">{new Date(course.start_date).toLocaleDateString()}</span>
                    <span className="truncate">{new Date(course.end_date).toLocaleDateString()}</span>
                  </div>

                </Link>
              )) : (
                <div className="
                  col-span-full rounded-xl
                  border-2 border-dashed border-[var(--border-color)]
                  card-strong
                  py-16 text-center
                ">
                  <div className="inline-block p-5 bg-blue-500/10 rounded-full mb-4">
                    <svg className="w-12 h-12 text-blue-400 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13M3 6.253C4.168 5.477 5.754 5 7.5 5S10.832 5.477 12 6.253M12 6.253C13.168 5.477 14.754 5 16.5 5S19.832 5.477 21 6.253M3 19.253C4.168 18.477 5.754 18 7.5 18S10.832 18.477 12 19.253M12 19.253C13.168 18.477 14.754 18 16.5 18S19.832 18.477 21 19.253" />
                    </svg>
                  </div>
                  <p className="text-base text-[var(--text-secondary)] mb-4 font-medium">
                    No courses yet
                  </p>
                  <p className="text-sm text-[var(--text-muted)]">
                    Create your first course to get started!
                  </p>
                </div>
              )}
              {/* Create New Course Card */}
              <Link
                to="/teacher/courses"
                className="
                  group relative flex flex-col rounded-xl
                  border-2 border-dashed border-[var(--border-color)]
                  card-strong
                  p-4 sm:p-5
                  transition-all duration-300
                  hover:-translate-y-1
                  hover:shadow-lg
                  hover:border-blue-500/40
                  hover:bg-blue-500/5
                  items-center justify-center text-center
                  min-h-[180px] sm:min-h-[200px]
                  cursor-pointer
                "
              >
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center mb-3 sm:mb-4 group-hover:border-blue-500/50 group-hover:scale-110 transition-all duration-300">
                  <svg className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <h3 className="font-bold text-sm sm:text-base mb-1 sm:mb-2 group-hover:text-blue-400 transition-colors duration-300">Create New Course</h3>
                <p className="text-xs text-[var(--text-muted)]">Add details, set time limits and more</p>
              </Link>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default DashboardTeachers;
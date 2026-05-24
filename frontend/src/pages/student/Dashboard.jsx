import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FaCheckCircle, FaBolt, FaChartLine, FaClock, FaArrowRight,
  FaBook,
  FaLayerGroup,
  FaPuzzlePiece,
  FaHistory,
  FaStar
} from 'react-icons/fa';

import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import { useAuthStore } from '../../store/authStore';
import { fetchStudentDashboardCourses } from '../../api/api';

const Dashboard = () => {
  const { user } = useAuthStore();
  const [stats, setStats] = useState(null);
  const [courses, setCourses] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [activities, setActivities] = useState([]);
  const [upcomingQuizzes, setUpcomingQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchCode, setSearchCode] = useState('');
  const [searchResult, setSearchResult] = useState(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const data = await fetchStudentDashboardCourses();
        console.log('Dashboard data:', data.dashboard);
        setStats(data.stats || {});
        setCourses(data.courses || []);
        setDashboard(data.dashboard || {});
        setActivities(data.dashboard?.recent_activities || []);
        setUpcomingQuizzes(data.dashboard?.upcoming_quizzes || []);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const stat_s = [
    {
      label: 'Total Courses',
      value: dashboard?.total_enrolled ?? 0,
      icon: (
        <FaBook className="w-6 h-6" />
      ),
      color: 'rgb(234, 179, 8)',
    },
    {
      label: 'Active Courses',
      value: dashboard?.active_enrolled ?? 0,
      icon: (
        <FaBook className="w-6 h-6" />
      ),
      color: 'rgb(34, 197, 94)',
    },
    {
      label: 'Avg. Completion',
      value: `${dashboard?.avg_completion ?? 0}%`,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'rgb(249, 115, 22)',
    },
    {
      label: 'Learning Hours',
      value: stats?.learning_hours || '0h 0m',
      icon: (
        <FaClock className="w-6 h-6" />
      ),
      color: 'rgb(168, 85, 247)',
    },
  ];



  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading dashboard...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center min-h-[400px]">
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-red-300 text-center max-w-md">
              {error}
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Helper for course progress bar color
  const getProgressColor = (percent) => {
    if (percent >= 80) return 'bg-green-500';
    if (percent >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex min-h-screen relative grid-texture">
      <Sidebar />
      <main className="flex-1 w-full lg:w-auto">
        <Header isAuth />
        <div className="p-4 sm:p-6 lg:p-8">

          {/* Header Section */}
          <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4 mb-6 lg:mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold mb-2">Dashboard</h1>
              <p className="muted text-sm">
                Welcome back, {user?.name || user?.username}! Here&apos;s your learning progress and activities.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-6 lg:mb-8">
            {stat_s.map((stat, index) => (
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

          <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 mb-6 lg:mb-8">
            {/* Upcoming Quizzes */}
            <div className="lg:col-span-2 card p-5 sm:p-6 rounded-2xl border-2 border-[var(--border-subtle)] shadow-lg shadow-emerald-500/5">
              <div className="mb-4 sm:mb-6 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-bold mb-0.5">Upcoming</h2>
                  <p className="text-xs sm:text-sm muted">Quizzes & Exercises scheduled for your courses</p>
                </div>
              </div>
              <div className="space-y-3 sm:space-y-4">
                {upcomingQuizzes.length > 0 ? upcomingQuizzes.map((quiz, index) => (
                  <div
                    key={index}
                    className={`card-strong p-4 sm:p-5 rounded-xl hover:shadow-md hover:bg-white/[0.03] transition-all duration-300 group ${quiz.is_exercise ? 'hover:border-purple-500' : 'hover:border-green-500'
                      }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                      <div className="flex gap-3 sm:gap-4 flex-1">
                        <div
                          className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300 border-2 ${quiz.is_exercise
                              ? 'bg-purple-500/15 border-purple-500/30'
                              : 'bg-green-500/15 border-green-500/30'
                            }`}
                        >
                          {quiz.is_exercise ? (
                            <FaPuzzlePiece className="w-5 h-5 sm:w-6 sm:h-6 text-purple-500 dark:text-purple-400" />
                          ) : (
                            <svg className="w-5 h-5 sm:w-6 sm:h-6 text-green-500 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-base sm:text-lg mb-1 flex items-center gap-2">
                            <span className="truncate">{quiz.name}</span>
                            <span className={`px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-lg border-2 text-[10px] sm:text-xs font-bold whitespace-nowrap flex-shrink-0 ${quiz.is_exercise
                                ? 'bg-purple-500/10 text-purple-500 border-purple-500/20'
                                : 'bg-green-500/10 text-green-500 border-green-500/20'
                              } `}>
                              {quiz.is_exercise ? 'Exercise' : 'Quiz'}
                            </span>
                          </h3>
                          <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm muted">
                            <div className="flex items-center gap-1.5">
                              <FaBook className="w-2.5 h-2.5 sm:w-3 sm:h-3 " />
                              {quiz.course_name}
                            </div>
                            <div className="flex items-center gap-1.5">
                              <FaLayerGroup className="w-2.5 h-2.5 sm:w-3 sm:h-3 " />
                              {quiz.module_name}
                            </div>
                          </div>
                        </div>
                      </div>
                      {quiz.course_id ? (
                        <Link
                          to={`/courses/${quiz.course_id}/manage`}
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
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p className="text-muted font-medium">No upcoming quizzes & exercises</p>
                  </div>
                )}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="card p-5 sm:p-6 rounded-2xl border-b-2 border-[var(--border-subtle)] shadow-lg shadow-purple-500/5">
              <div className="mb-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border-2 border-purple-500/30 flex items-center justify-center">
                  <FaHistory className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold mb-0.5">Recent Activity</h2>
                  <p className="text-xs muted">Your latest actions</p>
                </div>
              </div>
              <div className="space-y-3">
                {activities && activities.length > 0 ? (
                  activities.map((activity) => (
                    <div
                      key={activity.id}
                      className="card-strong p-3.5 sm:p-4 rounded-xl flex items-center gap-3 sm:gap-4 group hover:bg-white/[0.03] hover:border-purple-500/30 transition-all duration-300 border border-transparent"
                    >
                      <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-lg border flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300 ${activity.color === 'yellow' ? 'bg-amber-500/15 border-amber-500/30 text-amber-500 dark:text-amber-400' :
                          activity.color === 'green' ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-500 dark:text-emerald-400' :
                            activity.color === 'blue' ? 'bg-blue-500/15 border-blue-500/30 text-blue-500 dark:text-blue-400' :
                              'bg-purple-500/15 border-purple-500/30 text-purple-500 dark:text-purple-400'
                        }`}>
                        {activity.icon === 'check' ? <FaCheckCircle className="w-4 h-4 sm:w-5 sm:h-5" /> :
                          activity.icon === 'clock' ? <FaClock className="w-4 h-4 sm:w-5 sm:h-5" /> :
                            activity.icon === 'star' ? <FaStar className="w-4 h-4 sm:w-5 sm:h-5" /> :
                              <FaBolt className="w-4 h-4 sm:w-5 sm:h-5" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-[var(--text-primary)] truncate">
                          {activity.title}
                        </p>
                        <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs muted mt-0.5">
                          <span className="truncate">{activity.description}</span>
                          <span className="w-1 h-1 rounded-full bg-[var(--text-muted)] flex-shrink-0"></span>
                          <span className="flex-shrink-0 whitespace-nowrap">{activity.time}</span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 card-strong rounded-xl border border-dashed border-[var(--border-color)]">
                    <p className="text-sm muted">No recent activities</p>
                  </div>
                )}
              </div>
            </div>

          </div>

          <section
            className="
              rounded-2xl
              border-2 border-[var(--border-strong)]
              card
              
              hover:border-blue-500/70 dark:hover:border-blue-500/50 hover:shadow-lg
              p-5 sm:p-6 lg:p-8
            "
          >
            {/* Header */}
            <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 mb-6 sm:mb-8 pb-4 border-b-2 border-[var(--border-subtle)]">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-9 h-9 sm:w-10 sm:h-10 lg:w-12 lg:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                  <FaBook className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-[var(--text-primary)] truncate">
                    Enrolled Courses
                  </h2>
                  <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-0.5 truncate">
                    Continue where you left off
                  </p>
                </div>
              </div>
              <span className="text-xs sm:text-sm font-semibold text-[var(--text-secondary)] px-3 py-1.5 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)] whitespace-nowrap">
                {(searchResult || courses).length} total
              </span>
            </header>

            {/* Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-5 lg:gap-6">
              {(searchResult || courses).length > 0 ? (
                (searchResult || courses).map((course) => (
                  <article
                    key={course.id}
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
                    {/* Course Title */}
                    <h3 className="text-sm sm:text-base font-bold leading-snug line-clamp-2 mb-1.5 text-[var(--text-primary)] group-hover:text-blue-400 transition-colors duration-300">
                      {course.name}
                    </h3>
                    {/* Instructor */}
                    <p className="text-xs text-[var(--text-muted)] mb-3 sm:mb-4 flex items-center gap-1.5">
                      <svg className="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                      </svg>
                      <span className="truncate">{course.instructor}</span>
                    </p>
                    {/* Meta */}
                    <div className="flex items-center justify-between text-xs mb-3 gap-2">
                      <span className="text-[var(--text-muted)] flex items-center gap-1.5 truncate">
                        <FaLayerGroup className="w-3 h-3 text-cyan-400" />
                        <span className="truncate">{course.course_content?.length ?? 0} modules</span>
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
                    {/* Progress */}
                    <div className="mb-4 sm:mb-5">
                      <div className="flex justify-between text-[10px] sm:text-[11px] mb-2">
                        <span className="text-[var(--text-muted)] font-medium">
                          Progress
                        </span>
                        <span className="text-[var(--text-primary)] font-bold">
                          {course.completion_percentage || 0}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-[var(--input-bg)] border border-[var(--border-color)] overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${getProgressColor(
                            course.completion_percentage
                          )}`}
                          style={{ width: `${course.completion_percentage || 0}%` }}
                        />
                      </div>
                    </div>
                    {/* Dates */}
                    <div className="flex justify-between text-[10px] sm:text-[11px] text-[var(--text-muted)] mb-4 sm:mb-5 gap-2">
                      <span className="truncate">{new Date(course.start_date).toLocaleDateString()}</span>
                      <span className="truncate">{new Date(course.end_date).toLocaleDateString()}</span>
                    </div>
                    {/* CTA */}
                    <Link
                      to={`/courses/${course.id}/manage`}
                      className="
                        mt-auto inline-flex items-center justify-center gap-2
                        rounded-lg
                        border-2 border-blue-500/30
                        bg-blue-500/10
                        py-2 sm:py-2.5 px-3 sm:px-4 text-xs sm:text-sm font-semibold
                        text-blue-400
                        transition-all duration-300
                        hover:border-blue-500/50
                        hover:bg-blue-500/20
                        hover:shadow-lg hover:shadow-blue-500/20
                        active:scale-95
                      "
                    >
                      <span className="hidden sm:inline">Resume Course</span>
                      <span className="sm:hidden">Resume</span>
                      <FaArrowRight className="w-3 h-3 sm:w-3.5 sm:h-3.5 group-hover:translate-x-1 transition-transform duration-300" />
                    </Link>
                  </article>
                ))
              ) : (
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
                    You haven't enrolled in any courses yet
                  </p>
                  <Link
                    to="/courses"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg shadow-blue-600/25 hover:shadow-xl hover:shadow-blue-600/30 transition-all duration-300 active:scale-95"
                  >
                    Explore Courses
                    <FaArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              )}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
};

export default Dashboard;
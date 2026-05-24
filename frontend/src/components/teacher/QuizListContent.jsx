import React from 'react';
import { Link } from 'react-router-dom';
import {
    FaCalendar,
    FaClock,
    FaPuzzlePiece,
    FaUsers,
    FaCheckCircle,
    FaBook,
    FaTrophy,
    FaDumbbell,
    FaChartLine,
    FaChevronDown,
    FaChevronUp,
    FaEye,
    FaEllipsisV,
    FaQuestionCircle
} from 'react-icons/fa';

const QuizListContent = ({
    courses,
    loading,
    error,
    filteredCourses,
    activeFilter,
    searchQuery,
    expandedCourseId,
    openMenuId,
    totalQuizzes,
    totalExercises,
    totalActive,
    loadQuizzes,
    toggleCourseDetails,
    toggleMenu,
    getQuizTypeIcon,
    getQuizTypeColor,
    onGradeClick,
    onMonitorClick

}) => {
    return (
        <>
            {/* Stats Cards - Responsive Grid */}
            <div className="grid grid-cols-2 gap-4 sm:gap-5 mb-6">
                <div className="card p-4 sm:p-5 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden bg-[var(--card-bg)]">
                    <div className="relative flex items-center gap-3">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-orange-500/15 flex items-center justify-center border-2 border-orange-500/40 group-hover:scale-110 transition-transform duration-300 flex-shrink-0">
                            <FaTrophy className="w-5 h-5 sm:w-6 sm:h-6 text-orange-600 dark:text-orange-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                            <p className="text-xs text-[var(--text-muted)] mb-1 font-medium">Total Quizzes & Exercises</p>
                            <p className="text-2xl sm:text-3xl font-bold truncate text-orange-600 dark:text-orange-400">{totalQuizzes}</p>
                        </div>
                    </div>
                </div>

                <div className="card p-4 sm:p-5 rounded-2xl border-2 border-[var(--border-subtle)] hover:shadow-lg transition-all duration-300 group relative overflow-hidden bg-[var(--card-bg)]">
                    <div className="relative flex items-center gap-3">
                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-yellow-500/15 flex items-center justify-center border-2 border-yellow-500/40 group-hover:scale-110 transition-transform duration-300 flex-shrink-0">
                            <FaCheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-yellow-600 dark:text-yellow-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                            <p className="text-xs text-[var(--text-muted)] mb-1 font-medium">Active</p>
                            <p className="text-2xl sm:text-3xl font-bold truncate text-yellow-600 dark:text-yellow-400">{totalActive}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Notice Banner - Responsive */}
            {courses.length > 0 && !loading && (
                <div className="mb-5 p-4 bg-blue-500/10 dark:bg-blue-500/10 border-2 border-blue-500/40 dark:border-blue-500/30 rounded-xl">
                    <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-xl bg-blue-500/20 border-2 border-blue-500/40 dark:border-blue-500/30 flex items-center justify-center flex-shrink-0">
                            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>

                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm text-blue-700 dark:text-blue-400 font-semibold mb-1">
                                📚 Showing {courses.length} course{courses.length !== 1 ? 's' : ''} with quizzes or exercises
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400/80">
                                Courses without any quizzes or exercises are not displayed here.{' '}
                                <Link to="/teacher/courses" className="underline hover:text-blue-800 dark:hover:text-blue-300 font-semibold transition-colors">
                                    View all courses →
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Content Card */}
            <div className="card-strong p-4 sm:p-5 lg:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                <div className="mb-6 pb-5 border-b-2 border-[var(--border-subtle)] flex items-center gap-3">
                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                        <FaQuestionCircle className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-lg sm:text-xl font-bold mb-1">All Quizzes & Exercises</h2>
                        <p className="text-xs sm:text-sm muted">Browse and manage all assessments across courses</p>
                    </div>
                </div>

                {error ? (
                    <div className="card p-6 sm:p-8 border-2 border-red-500/50 dark:border-red-500/30 bg-red-500/15 dark:bg-red-500/10 rounded-xl text-center">
                        <div className="inline-block p-4 bg-red-500/20 rounded-full mb-4 border-2 border-red-500/40">
                            <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <p className="text-sm sm:text-base text-red-700 dark:text-red-400 mb-4 font-semibold">{error}</p>
                        <button
                            onClick={loadQuizzes}
                            className="bg-red-500/25 dark:bg-red-500/20 hover:bg-red-500/35 dark:hover:bg-red-500/30 text-red-700 dark:text-red-400 px-6 py-2.5 rounded-xl border-2 border-red-500/50 dark:border-red-500/30 hover:border-red-500/60 dark:hover:border-red-500/50 transition-all duration-300 text-sm font-semibold active:scale-95"
                        >
                            Retry
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {filteredCourses.length === 0 ? (
                            <div className="text-center py-12 sm:py-16">
                                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-blue-500/15 border-2 border-blue-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                    {activeFilter === 'quiz' ? (
                                        <FaTrophy className="w-8 h-8 sm:w-10 sm:h-10 text-blue-600 dark:text-blue-400 opacity-60" />
                                    ) : activeFilter === 'exercise' ? (
                                        <FaDumbbell className="w-8 h-8 sm:w-10 sm:h-10 text-purple-600 dark:text-purple-400 opacity-60" />
                                    ) : (
                                        <FaBook className="w-8 h-8 sm:w-10 sm:h-10 text-blue-600 dark:text-blue-400 opacity-60" />
                                    )}
                                </div>
                                <h3 className="text-lg sm:text-xl font-bold mb-2">
                                    {searchQuery ? 'No matches found' :
                                        activeFilter === 'quiz' ? 'No quizzes found' :
                                            activeFilter === 'exercise' ? 'No exercises found' :
                                                'No quizzes or exercises found'}
                                </h3>
                                <p className="text-sm text-muted mb-6 px-4">
                                    {searchQuery ? 'Try adjusting your search terms' :
                                        'Create your first quiz or exercise in a course'}
                                </p>
                                <Link
                                    to="/teacher/courses"
                                    className="inline-block bg-gradient-to-r from-blue-600 to-blue-500 text-white px-6 py-2.5 rounded-xl hover:shadow-xl hover:shadow-blue-600/30 transition-all duration-300 active:scale-95 text-sm font-semibold"
                                >
                                    Go to Courses
                                </Link>
                            </div>
                        ) : (
                            filteredCourses.map((course) => {
                                const isExpanded = expandedCourseId === course.course_id;
                                const quizCount = course.quizzes.filter(q => !q.is_exercise).length;
                                const exerciseCount = course.quizzes.filter(q => q.is_exercise).length;

                                return (
                                    <div key={course.course_id} className="mb-4">
                                        <div className={`card p-4 sm:p-5 rounded-xl border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group hover:shadow-md bg-[var(--surface)] ${isExpanded ? 'border-blue-500/70 dark:border-blue-500/50' : ''}`}>
                                            <div className="flex flex-col sm:flex-row items-start gap-4">
                                                {/* Icon */}
                                                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/15 flex items-center justify-center flex-shrink-0 border-2 border-blue-500/40 dark:border-blue-500/30 group-hover:border-blue-500/60 dark:group-hover:border-blue-500/50 group-hover:scale-110 transition-all duration-300">
                                                    <FaBook className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                                                </div>

                                                {/* Content */}
                                                <div className="flex-1 min-w-0 w-full">
                                                    <div className="flex items-start gap-2 mb-2">
                                                        <div className="flex-1 min-w-0">
                                                            <h3 className="text-base sm:text-lg font-bold line-clamp-2 text-[var(--text-primary)] group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
                                                                {course.course_name}
                                                            </h3>
                                                        </div>
                                                    </div>

                                                    {/* Stats */}
                                                    <div className="flex flex-wrap gap-3 sm:gap-4 text-xs text-[var(--text-muted)] mt-2">
                                                        <div className="flex items-center gap-1.5">
                                                            <FaTrophy className="w-3.5 h-3.5 flex-shrink-0 text-blue-400" />
                                                            <span className="font-medium">{course.quizzes.length} quizzes and exercises</span>
                                                        </div>

                                                    </div>
                                                </div>

                                                {/* Actions */}
                                                <div className="flex items-center gap-2 w-full sm:w-auto sm:self-start flex-shrink-0">
                                                    <button
                                                        onClick={() => toggleCourseDetails(course.course_id)}
                                                        className="flex-1 sm:flex-none px-4 py-2.5 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] rounded-xl text-xs sm:text-sm font-semibold hover:border-blue-500/40 hover:bg-blue-500/5 active:scale-95 transition-all duration-300 text-center whitespace-nowrap flex items-center justify-center gap-2"
                                                    >
                                                        {isExpanded ? (
                                                            <>
                                                                <span>Hide Details</span>
                                                                <FaChevronUp className="w-3 h-3" />
                                                            </>
                                                        ) : (
                                                            <>
                                                                <span>Details</span>
                                                                <FaChevronDown className="w-3 h-3" />
                                                            </>
                                                        )}
                                                    </button>

                                                    {/* Three Dot Menu */}
                                                    <div className="relative menu-container">
                                                        <button
                                                            onClick={(e) => toggleMenu(course.course_id, e)}
                                                            className="p-2.5 border-2 border-[var(--border-strong)] bg-[var(--input-bg)] rounded-xl hover:border-blue-500/40 hover:bg-blue-500/5 active:scale-95 transition-all duration-300 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                                            aria-label="Course Actions"
                                                        >
                                                            <FaEllipsisV className="w-4 h-4" />
                                                        </button>

                                                        {openMenuId === course.course_id && (
                                                            <div className="absolute right-0 mt-2 z-50 w-48 bg-[var(--card-strong-bg)] border-2 border-[var(--border-strong)] rounded-xl shadow-2xl py-1.5 animate-fadeIn">
                                                                <Link
                                                                    to={`/teacher/courses/${course.course_id}/manage`}
                                                                    className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium hover:bg-blue-500/10 text-blue-400 hover:text-blue-300 transition-colors"
                                                                    onClick={() => toggleMenu(null)}
                                                                >
                                                                    <FaChartLine className="w-4 h-4" />
                                                                    <span>Manage Course</span>
                                                                </Link>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Quiz Details Dropdown */}
                                        {isExpanded && (
                                            <div className="mt-3 border-2 border-blue-500/70 dark:border-blue-500/50 rounded-xl overflow-hidden shadow-lg animate-slideDown hover:shadow-md bg-[var(--surface)]">
                                                <div className="p-5">
                                                    <h4 className="text-sm font-bold mb-4 flex items-center gap-2">
                                                        <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                                        Quizzes & Exercises ({course.quizzes.length})
                                                    </h4>

                                                    <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                                        {course.quizzes.length === 0 ? (
                                                            <div className="text-center py-10">
                                                                <div className="w-14 h-14 bg-blue-500/10 border-2 border-blue-500/20 rounded-xl flex items-center justify-center mx-auto mb-3">
                                                                    <FaBook className="w-7 h-7 text-blue-400 opacity-50" />
                                                                </div>
                                                                <p className="text-sm text-muted font-semibold mb-2">No quizzes or exercises yet</p>
                                                                <Link
                                                                    to={`/teacher/courses/${course.course_id}/manage`}
                                                                    className="text-xs text-blue-400 hover:text-blue-300 underline transition-colors"
                                                                >
                                                                    Add quizzes in course management →
                                                                </Link>
                                                            </div>
                                                        ) : (
                                                            <ul className="space-y-3">
                                                                {course.quizzes.map((quiz) => {
                                                                    const TypeIcon = getQuizTypeIcon(quiz.is_exercise);
                                                                    const typeColor = getQuizTypeColor(quiz.is_exercise);

                                                                    return (
                                                                        <li
                                                                            key={quiz.id}
                                                                            className="card-strong p-4 rounded-xl border-2 border-[var(--border-medium)] hover:shadow-md hover:bg-white/[0.02] transition-all duration-300 group"

                                                                        >
                                                                            <div className="flex items-start gap-3">
                                                                                <div className={`p-2 rounded-xl flex-shrink-0 border-2 ${quiz.is_exercise
                                                                                    ? 'bg-purple-500/10 border-purple-500/30'
                                                                                    : 'bg-emerald-500/10 border-emerald-500/30'
                                                                                    } group-hover:scale-110 transition-transform duration-300`}>
                                                                                    {quiz.is_exercise ? (
                                                                                        <FaPuzzlePiece className="text-purple-400 w-6 h-6" />
                                                                                    ) : (
                                                                                        <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                                        </svg>
                                                                                    )}

                                                                                </div>



                                                                                <div className="flex-1 min-w-0">
                                                                                    <div className="flex items-start justify-between gap-2 mb-2">
                                                                                        <div className="flex-1 min-w-0">
                                                                                            <div className="text-[10px] font-bold text-blue-400 mb-1 uppercase tracking-wide">
                                                                                                {quiz.module_name}
                                                                                            </div>
                                                                                            <h5 className="text-sm font-bold group-hover:text-blue-400 transition-colors line-clamp-2">
                                                                                                {quiz.name}
                                                                                            </h5>
                                                                                        </div>
                                                                                        <span
                                                                                            className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${quiz.active
                                                                                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                                                                                                : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                                                                                                }`}
                                                                                        >
                                                                                            {quiz.active ? 'Active' : 'Inactive'}
                                                                                        </span>

                                                                                    </div>


                                                                                    <div className="flex flex-wrap items-center gap-3 text-xs text-muted mb-3">
                                                                                        <span className="flex items-center gap-1.5">
                                                                                            <FaUsers className="w-3.5 h-3.5" />
                                                                                            <span className="font-medium">{quiz.attempts || 0} users</span>
                                                                                        </span>
                                                                                        <span className="flex items-center gap-1.5">
                                                                                            <FaCalendar className="w-3.5 h-3.5" />
                                                                                            <span className="font-medium">{new Date(quiz.start_date).toLocaleDateString()}</span>
                                                                                        </span>
                                                                                    </div>

                                                                                    <div className="flex items-center justify-between flex-wrap gap-2">
                                                                                        <Link
                                                                                            to={`/teacher/courses/${course.course_id}/manage`}
                                                                                            className="inline-flex items-center gap-2 text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
                                                                                        >
                                                                                            <FaEye className="w-3.5 h-3.5" />
                                                                                            View in Course
                                                                                        </Link>
                                                                                        <div className="flex gap-2">
                                                                                            <Link
                                                                                                to="#"
                                                                                                onClick={(e) => { e.preventDefault(); onMonitorClick(quiz, course); }}
                                                                                                className="inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 hover:shadow-lg hover:shadow-purple-500/30 active:scale-95 transition-all duration-300"
                                                                                            >
                                                                                                <FaChartLine className="w-3.5 h-3.5" />
                                                                                                Monitor
                                                                                            </Link>
                                                                                            <Link
                                                                                                to="#"
                                                                                                onClick={e => { e.preventDefault(); onGradeClick(quiz, course); }}
                                                                                                className="inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white hover:from-emerald-700 hover:to-green-700 hover:shadow-lg hover:shadow-emerald-500/30 active:scale-95 transition-all duration-300"
                                                                                            >
                                                                                                <FaCheckCircle className="w-3 h-3 sm:w-4 sm:h-4" />
                                                                                                Grade
                                                                                            </Link>
                                                                                        </div>
                                                                                    </div>
                                                                                </div>
                                                                            </div>
                                                                        </li>
                                                                    );
                                                                })}
                                                            </ul>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>
                )}
            </div>

            <style>{`
                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                .animate-slideDown {
                    animation: slideDown 0.3s ease-out;
                }

                .animate-fadeIn {
                    animation: fadeIn 0.2s ease-out;
                }

                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }

                .custom-scrollbar::-webkit-scrollbar-track {
                    background: var(--input-bg);
                    border-radius: 10px;
                }

                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: var(--border-strong);
                    border-radius: 10px;
                }

                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: var(--border-subtle);
                }

                .scrollbar-hide {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }

                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
            `}</style>
        </>
    );
};

export default QuizListContent;
import React, { useState, useEffect } from 'react';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import QuizListContent from '../../components/teacher/QuizListContent';
import QuizGradingPanel from '../../components/teacher/QuizGradingPanel';
import QuizMonitorPanel from '../../components/teacher/QuizMonitorPanel';

import { useQuizGradingStore } from '../../store/quizGradeStore';
import { FaTrophy, FaDumbbell, FaSearch, FaFilter } from 'react-icons/fa';

const TeacherQuizzes = () => {
    // Zustand store
    const {
        quizzesByCourse,
        loadingQuizzes,
        quizzesError,
        loadTeacherQuizzes,
        getFilteredQuizzes,
        getQuizStats,
        clearError
    } = useQuizGradingStore();

    // Local UI state
    const [searchQuery, setSearchQuery] = useState('');
    const [activeFilter, setActiveFilter] = useState('all'); // all, quiz, exercise
    const [expandedCourseId, setExpandedCourseId] = useState(null);
    const [openMenuId, setOpenMenuId] = useState(null);
    const [gradingQuiz, setGradingQuiz] = useState(null);
    const [gradingCourse, setGradingCourse] = useState(null);

    const [monitoringQuiz, setMonitoringQuiz] = useState(null);
    const [monitoringCourse, setMonitoringCourse] = useState(null);

    // Load quizzes on mount
    useEffect(() => {
        loadTeacherQuizzes();
    }, []);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (openMenuId && !event.target.closest('.menu-container')) {
                setOpenMenuId(null);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [openMenuId]);

    const toggleCourseDetails = (courseId) => {
        setExpandedCourseId(expandedCourseId === courseId ? null : courseId);
    };

    const toggleMenu = (courseId, e) => {
        if (e) e.stopPropagation();
        setOpenMenuId(openMenuId === courseId ? null : courseId);
    };

    const handleSearch = (e) => setSearchQuery(e.target.value);

    const handleRetry = () => {
        clearError('quizzes');
        loadTeacherQuizzes();
    };

    const handleGradeClick = (quiz, course) => {
        setGradingQuiz(quiz);
        setGradingCourse(course);
    };

    const handleMonitorClick = (quiz, course) => {
        setMonitoringQuiz(quiz);
        setMonitoringCourse(course);
    };


    // Get filtered courses based on search and filter
    const filteredCourses = getFilteredQuizzes(searchQuery, activeFilter);

    // Get statistics
    const { totalQuizzes, totalExercises, totalActive } = getQuizStats();

    // Helper functions for quiz rendering
    const getQuizTypeIcon = (isExercise) => {
        return isExercise ? FaDumbbell : FaTrophy;
    };

    const getQuizTypeColor = (isExercise) => {
        return isExercise ? 'purple' : 'blue';
    };

    if (loadingQuizzes) {
        return (
            <div className="flex min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="p-4 sm:p-8 flex items-center justify-center min-h-[400px]">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-10 w-10 sm:h-12 sm:w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p className="text-sm sm:text-base text-gray-400">Loading quizzes...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1 w-full lg:w-auto">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Quizzes</h1>
                        <p className="text-sm muted">Manage and monitor all your quizzes and exercises</p>
                    </div>
                    {gradingQuiz && gradingCourse ? (
                        <QuizGradingPanel
                            quiz={gradingQuiz}
                            course={gradingCourse}
                            onBack={() => { setGradingQuiz(null); setGradingCourse(null); }}
                        />
                    ) : monitoringQuiz && monitoringCourse ? (
                        <QuizMonitorPanel
                            quiz={monitoringQuiz}
                            course={monitoringCourse}
                            onBack={() => { setMonitoringQuiz(null); setMonitoringCourse(null); }}
                        />
                    ) : (
                        <QuizListContent
                            courses={quizzesByCourse}
                            loading={loadingQuizzes}
                            error={quizzesError}
                            filteredCourses={filteredCourses}
                            activeFilter={activeFilter}
                            searchQuery={searchQuery}
                            expandedCourseId={expandedCourseId}
                            openMenuId={openMenuId}
                            totalQuizzes={totalQuizzes}
                            totalExercises={totalExercises}
                            totalActive={totalActive}
                            loadQuizzes={handleRetry}
                            toggleCourseDetails={toggleCourseDetails}
                            toggleMenu={toggleMenu}
                            getQuizTypeIcon={getQuizTypeIcon}
                            getQuizTypeColor={getQuizTypeColor}
                            onGradeClick={handleGradeClick}
                            onMonitorClick={handleMonitorClick}
                        />
                    )}    
                </div>
            </main>

            <style jsx>{`
                .scrollbar-hide {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }

                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
            `}</style>
        </div>
    );
};

export default TeacherQuizzes;
import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
    FaChevronLeft,
    FaShareAlt,
    FaEllipsisV,
    FaPlus,
} from 'react-icons/fa';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import CourseAnalytics from '../../components/teacher/CourseAnalytics';

import CourseDiscussionsTab from '../../components/teacher/CourseDiscussion';
import useManageCourseStore from '../../store/manageCourseStore';
import CourseEnrollment from '../../components/teacher/CourseEnrollement';
import CourseModules from '../../components/teacher/CourseModules';
import CourseDesign from '../../components/teacher/CourseDesign';
import CourseMail from '../../components/teacher/CourseMail';
import CourseTeachers from '../../components/teacher/CourseTeachers';
import CourseMembers from '../../components/teacher/CourseMembers';
import CourseMDManager from '../../components/teacher/CourseMDManager';

const ManageCourse = () => {
    const { courseId } = useParams();
    const {
        course, modules, loading, error, enrollments, loadingEnrollments, analytics, loadingAnalytics,
        activeTab, setActiveTab, activeForumTab, showQuizQuestionManager, setShowQuizQuestionManager, selectedQuizId, setSelectedQuizId,
        moduleOrder, unitOrders, savingOrder, showModuleForm, editingModule, showLessonForm, showQuizForm,
        selectedModule, editingLesson, editingQuiz, moduleFormData, lessonFormData, quizFormData,
        setShowModuleForm, setEditingModule, setModuleFormData, handleModuleFormChange, handleCreateModule, handleUpdateModule, handleDeleteModule,
        openEditModule, openCreateModule, setShowLessonForm, setSelectedModule, setEditingLesson, setLessonFormData, handleLessonFormChange,
        openCreateLesson, openEditLesson, handleCreateLesson, handleDeleteLesson,
        setShowQuizForm, setEditingQuiz, setQuizFormData, handleQuizFormChange, openCreateQuiz, openEditQuiz, handleCreateQuiz, handleDeleteQuiz,
        loadCourseData, loadEnrollments, loadAnalytics, initializeOrdering, moveModule, saveModuleOrder, moveUnit, saveUnitOrder,
        handleApproveEnrollment, handleRejectEnrollment, handleRemoveEnrollment, handleQuizQuestionsUpdate
    } = useManageCourseStore();

    const [showAddPostModal, setShowAddPostModal] = useState(false);
    const openCreatePost = () => setShowAddPostModal(true);
    const closeCreatePost = () => setShowAddPostModal(false);

    useEffect(() => {
        if (courseId) {
            loadCourseData(courseId);
        }
    }, [courseId]);

    useEffect(() => {
        if (courseId && activeTab === 'Enrollment') {
            loadEnrollments(courseId);
        }
        if (courseId && activeTab === 'Analytics') {
            loadAnalytics(courseId);
        }
    }, [courseId, activeTab]);

    useEffect(() => {
        if (modules.length > 0 && activeTab === 'Design Course') {
            initializeOrdering();
        }
    }, [modules, activeTab]);

    if (loading) {
        return (
            <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="p-4 sm:p-8 flex items-center justify-center min-h-[300px]">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-10 w-10 sm:h-12 sm:w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p className="text-gray-400 text-base sm:text-lg">Loading course...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    if (error || !course) {
        return (
            <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="p-4 sm:p-8 flex items-center justify-center min-h-[300px]">
                        <div className="text-center">
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 mb-4">
                                {error || 'Course not found'}
                            </div>
                            <Link to="/teacher/courses" className="text-blue-500 hover:text-blue-400">
                                Back to Courses
                            </Link>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    const tabs = [
        'Enrollment',
        'Modules',
        'Design Course',
        'Analytics',
        'Discussions',
        'Mail',
        'Add',
        'Members',
        'Files',
    ];

    return (
        <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
            <TeacherSidebar />

            <main className="flex-1">
                <Header isAuth />

                <div className="p-4 sm:p-8">
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Courses</h1>
                        <p className="text-sm muted">Create, manage and analyze your courses</p>
                    </div>

                    <div className="card-strong p-3 sm:p-6 min-h-[400px] sm:min-h-[600px] w-full max-w-full overflow-x-auto border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                        <div className="flex sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 gap-4 border-b-2 border-[var(--border-subtle)]">
                            <div className="flex items-start gap-4 mb-6">
                                <Link
                                    to="/teacher/courses"
                                    className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
                                >
                                    <FaChevronLeft className="w-4 h-4" />
                                </Link>
                                <div>
                                    <h2 className="text-lg sm:text-xl font-bold mb-1">
                                        {course?.name || 'Course'}
                                    </h2>
                                    <p className="text-xs sm:text-sm muted">
                                        {course?.instructions || 'Course management'}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 sm:gap-3">

                                {activeTab === 'Modules' && (
                                    <button
                                        onClick={openCreateModule}
                                        className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs sm:text-sm font-bold hover:from-blue-700 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/20 border border-blue-500/40 flex items-center gap-2"
                                    >
                                        <FaPlus className="w-3 h-3" />
                                        <span className="hidden sm:inline">Add Module</span>
                                    </button>
                                )}

                                {activeTab === 'Discussions' && activeForumTab === 'Course Forum' && (
                                    <button
                                        onClick={openCreatePost}
                                        className="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs sm:text-sm font-bold hover:from-blue-700 hover:to-blue-600 transition-all shadow-lg shadow-blue-500/20 border border-blue-500/40 flex items-center gap-2"
                                    >
                                        <FaPlus className="w-3 h-3" />
                                        <span className="hidden sm:inline">New Post</span>
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="w-full overflow-x-auto scrollbar-thin">
                            <div className="flex flex-nowrap sm:flex-wrap bg-[var(--input-bg)] border border-[var(--border-subtle)] sm:border-2 p-0.5 sm:p-1 rounded-xl min-w-[280px] sm:min-w-0 w-full sm:w-fit mb-6 sm:mb-8 gap-1 sm:gap-2 shadow-inner">
                                {tabs.map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`flex-1 sm:flex-none px-2 py-1.5 sm:px-4 sm:py-2 rounded-lg text-[11px] sm:text-sm font-bold transition-all duration-300 whitespace-nowrap ${activeTab === tab
                                            ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-600/30 sm:scale-105 border border-blue-400/50 sm:border-2'
                                            : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] border border-transparent sm:border-2'
                                            }`}
                                    >
                                        {tab}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="min-h-[200px] sm:min-h-[400px]">
                            {activeTab === 'Enrollment' && <CourseEnrollment courseId={course.id} />}
                            {activeTab === 'Modules' && <CourseModules />}
                            {activeTab === 'Design Course' && <CourseDesign />}
                            {activeTab === 'Analytics' && (
                                <div>

                                    <CourseAnalytics analytics={analytics} loading={loadingAnalytics} />
                                </div>
                            )}
                            {activeTab === 'Discussions' && course && (
                                <CourseDiscussionsTab
                                    courseId={course.id}
                                    showAddPostModal={showAddPostModal}
                                    setShowAddPostModal={setShowAddPostModal}
                                    closeCreatePost={closeCreatePost}
                                />
                            )}
                            {activeTab === 'Mail' && <CourseMail courseId={course.id} />}
                            {activeTab === 'Add' && <CourseTeachers />}
                            {activeTab === 'Members' && <CourseMembers />}
                            {activeTab === 'Files' && <CourseMDManager />}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ManageCourse;
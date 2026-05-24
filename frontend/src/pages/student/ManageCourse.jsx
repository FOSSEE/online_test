import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
    FaChevronLeft,
    FaShareAlt,
    FaEllipsisV,
    FaPlus,
} from 'react-icons/fa';
import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import useManageCourseStore from '../../store/student/manageCourseStore';
import CourseModules from '../../components/student/CourseModules';
import CourseDiscussion from '../../components/student/CourseDiscussion';

const ManageCourseStudent = () => {
    const { courseId } = useParams();
    const {
        course,
        courseLoading,
        courseError,
        loadCourseData,
        activeTab,
        activeForumTab,
        setActiveTab,
    } = useManageCourseStore();

    const [showAddPostModal, setShowAddPostModal] = useState(false);
    const openCreatePost = () => setShowAddPostModal(true);
    const closeCreatePost = () => setShowAddPostModal(false);

    useEffect(() => {
        if (courseId) {
            loadCourseData(courseId);
        }
    }, [courseId]);

    const tabs = [
        'Modules',
        'Discussions',
    ];


    if (courseLoading) {
        return (
            <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
                <Sidebar />
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

    if (courseError || (!course && !courseLoading)) {
        return (
             <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
                <Sidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="p-4 sm:p-8 flex items-center justify-center min-h-[300px]">
                        <div className="text-center">
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-300 mb-4">
                                {courseError || 'Course not found'}
                            </div>
                            <Link to="/courses" className="text-blue-400 hover:text-blue-300">
                                Back to Courses
                            </Link>
                        </div>
                    </div>
                </main>
            </div>
        );
    }


   
    return (
        <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
            <Sidebar />

            <main className="flex-1">
                <Header isAuth />

                <div className="p-4 sm:p-8">
                    {/* Page Header */}
                    <div className="mb-6 lg:mb-8">
                       <h1 className="text-2xl sm:text-3xl font-bold mb-2">Courses</h1>
                       <p className="text-sm muted">Browse, enroll, and manage your learning courses</p>
                    </div>

                    {/* Course Container */}
                    <div className="card-strong p-3 sm:p-6 min-h-[400px] sm:min-h-[600px] w-full max-w-full overflow-x-auto border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                        {/* Course Header */}
                        <div className="flex sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 gap-4">
                            <div className="flex items-center gap-3 sm:gap-4">
                                
                                <Link
                                    to="/courses"
                                    className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:bg-[var(--border-subtle)] transition-all duration-300 flex-shrink-0 active:scale-95"
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
                                

                                {activeTab === 'Discussions' && activeForumTab === 'Course Forum' && (
                                    <button
                                        onClick={openCreatePost}
                                        className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 shadow-xl shadow-blue-600/30 hover:shadow-2xl hover:shadow-blue-600/40 border-2 border-blue-500/50 active:scale-95 flex items-center gap-2"
                                    >
                                        <FaPlus className="w-3 h-3" />
                                        <span className="hidden sm:inline">New Post</span>
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="w-full overflow-x-auto scrollbar-thin">
                            <div className="flex flex-nowrap sm:flex-wrap bg-[var(--input-bg)] border border-[var(--border-subtle)] sm:border-2 p-0.5 sm:p-1 rounded-xl min-w-[280px] sm:min-w-0 w-full sm:w-fit mb-6 sm:mb-8 gap-1 sm:gap-2 shadow-inner">
                                {tabs.map((tab) => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`flex-1 sm:flex-none px-2 py-1.5 sm:px-4 sm:py-2 rounded-lg text-[11px] sm:text-sm font-bold transition-all duration-300 whitespace-nowrap ${activeTab === tab
                                            ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white sm:scale-105 border border-blue-400/50 sm:border-2'
                                            : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] border border-transparent sm:border-2'
                                            }`}
                                    >
                                        {tab}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Tab Content */}
                        <div className="min-h-[200px] sm:min-h-[400px]">
                            {activeTab === 'Modules' && <CourseModules />}
                            {activeTab === 'Discussions' && course && (
                                <CourseDiscussion
                                   courseId={course.id} // Pass courseId
                                   showAddPostModal={showAddPostModal} // Pass modal state
                                   setShowAddPostModal={setShowAddPostModal} // Pass setter
                                   closeCreatePost={closeCreatePost} // Pass close handler
                                />
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default ManageCourseStudent;
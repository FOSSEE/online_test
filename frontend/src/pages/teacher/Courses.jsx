import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FaPlus, FaSearch, FaFilter, FaBook, FaClock, FaUserFriends, FaEllipsisV, FaEdit, FaTimes, FaLayerGroup, FaCalendar } from 'react-icons/fa';
import { VscLibrary } from "react-icons/vsc";
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import CourseActionButtons from '../../components/teacher/CourseActionButtons';
import AddCourseModal from '../../components/teacher/AddCourseModal';
import { fetchTeacherCourses, getTeacherCourse, updateCourse, createDemoCourse } from '../../api/api';
import useGradingSystemStore from '../../store/teacherGradeStore';


const Courses = () => {
    const [activeTab, setActiveTab] = useState('All Courses');
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [message, setMessage] = useState(null);

    // Modal States
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingCourseId, setEditingCourseId] = useState(null);

    // Dropdown States
    const [openDropdownId, setOpenDropdownId] = useState(null);
    const dropdownRef = useRef(null);

    const { gradingSystems, loadGradingSystems, loading: gradingLoading } = useGradingSystemStore();

    useEffect(() => {
        loadCourses();
        loadGradingSystems();
        // eslint-disable-next-line
    }, [activeTab, searchQuery]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setOpenDropdownId(null);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadCourses = async () => {
        try {
            setLoading(true);
            const status = activeTab === 'All Quizzes' ? 'all' : activeTab.toLowerCase();
            const data = await fetchTeacherCourses(status, searchQuery);
            setCourses(data);
            setError(null);
        } catch (err) {
            setError('Failed to load courses');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => setSearchQuery(e.target.value);

    const getStatusColor = (status) => {
        switch (status) {
            case 'Active':
                return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'Inactive':
                return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
            case 'Draft':
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            default:
                return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
        }
    };

    const toggleDropdown = (courseId) => {
        setOpenDropdownId(openDropdownId === courseId ? null : courseId);
    };

    const handleEditClick = (courseId) => {
        setOpenDropdownId(null);
        setEditingCourseId(courseId);
        setShowEditModal(true);
    };

    const handleAddCourse = () => {
        setShowAddModal(true);
    };

    const handleCourseSuccess = () => {
        loadCourses();
    };

    const handleCreateDemoCourse = async () => {
        try {
            const result = await createDemoCourse();
            setMessage(result.message || 'Demo course created successfully!');
            loadCourses();
            setTimeout(() => setMessage(null), 3000);
        } catch (err) {
            setMessage('Failed to create demo course');
            setTimeout(() => setMessage(null), 3000);
        }
    };

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1 w-full lg:w-auto">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Page Header */}
                    <div className="mb-6 lg:mb-8 flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
                        <div>
                            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Courses</h1>
                            <p className="text-sm muted">Create, manage and analyze your courses</p>
                        </div>

                    </div>

                    {/* Success/Error Message */}
                    {message && (
                        <div className="mb-4 bg-blue-500/10 border-2 border-blue-500/30 rounded-xl p-3 sm:p-4 text-blue-300 text-sm animate-fade-in">
                            {message}
                        </div>
                    )}

                    {/* Action Buttons */}
                    <CourseActionButtons activeButton="library" />

                    {/* Course Library Section */}
                    <div className="card-strong p-4 sm:p-5 lg:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                        <div className="mb-5 sm:mb-7 pb-4 border-b-2 border-[var(--border-subtle)] flex items-center gap-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                                <VscLibrary className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                            </div>
                            <div>
                                <h2 className="text-lg sm:text-xl font-bold mb-1">Course Library</h2>
                                <p className="text-xs sm:text-sm muted">Browse and manage all your courses</p>
                            </div>
                        </div>



                        {/* Filters and Search */}
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
                            <div className="flex gap-2 sm:gap-3 w-full md:w-auto">
                                <div className="relative flex-1 md:w-64">
                                    <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] w-3.5 h-3.5 transition-colors" />
                                    <input
                                        type="text"
                                        placeholder="Search courses..."
                                        value={searchQuery}
                                        onChange={handleSearch}
                                        className="w-full pl-9 pr-3 sm:pr-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                                    />
                                </div>
                                <button
                                    className="px-3 sm:px-5 py-2.5 border-2 border-transparent bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl text-xs sm:text-sm font-semibold hover:shadow-xl hover:shadow-blue-600/30 active:scale-95 transition-all duration-300 flex items-center justify-center gap-2 whitespace-nowrap"
                                    onClick={handleAddCourse}
                                >
                                    <FaPlus className="w-4 h-4" />
                                    <span className="hidden lg:inline">Add Course</span>
                                    <span className="lg:hidden">Add</span>
                                </button>
                                <button
                                    className="px-3 sm:px-5 py-2.5 border-2 border-[var(--border-strong)] bg-[var(--card-bg)] rounded-xl text-xs sm:text-sm font-semibold hover:border-blue-500/40 hover:bg-blue-500/5 hover:shadow-md transition-all duration-300 flex items-center justify-center gap-2 "
                                    onClick={handleCreateDemoCourse}
                                >
                                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                    </svg>
                                    <span className="hidden lg:inline">Demo Course</span>
                                    <span className="lg:hidden">Demo</span>
                                </button>
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
                                {courses.length === 0 ? (
                                    <div className="text-center py-16">
                                        <div className="inline-block p-5 bg-blue-500/10 rounded-full mb-4">
                                            <FaBook className="w-12 h-12 text-blue-400 opacity-50" />
                                        </div>
                                        <p className="text-lg font-semibold text-[var(--text-secondary)] mb-2">No courses found</p>
                                        <p className="text-sm muted">Create your first course to get started</p>
                                    </div>
                                ) : (
                                    courses.map((course) => (
                                        <div
                                            key={course.id}
                                            className="card-strong p-4 sm:p-5 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group bg-[var(--surface)] hover:shadow-md rounded-xl"
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
                                                            className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${course.status === 'Active'
                                                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                                                                : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                                                                }`}
                                                        >
                                                            {course.status}
                                                        </span>

                                                    </div>
                                                    {course.code && (
                                                        <p className="text-xs sm:text-sm muted mb-2 sm:mb-3 line-clamp-2">Code: {course.code}</p>
                                                    )}
                                                    <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-4 text-xs muted">
                                                        <div className="flex items-center gap-1.5">
                                                            <FaLayerGroup className="w-2 h-2 sm:w-3 sm:h-3 flex-shrink-0" />
                                                            <span>{course.modules_count} modules</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5">
                                                            <FaUserFriends className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0" />
                                                            <span>{course.students_count} students</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5">
                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                            </svg>
                                                            <span>{course.completions} completions</span>
                                                        </div>
                                                        {course.created_on && (

                                                            <div className="flex items-center gap-1.5 text-blue-300">
                                                                <FaCalendar className="w-2 h-2 sm:w-2.5 sm:h-2.5 flex-shrink-0" />
                                                                <span>{new Date(course.created_on).toLocaleDateString()}</span>
                                                            </div>

                                                        )}
                                                    </div>
                                                </div>
                                                {/* Actions */}
                                                <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto sm:self-start">
                                                    <Link
                                                        to={`/teacher/courses/${course.id}/manage`}
                                                        className="flex-1 sm:flex-none px-4 sm:px-5 py-2.5 border-2 border-blue-500/30 bg-blue-500/10 rounded-lg text-xs sm:text-sm font-semibold text-blue-400 hover:border-blue-500/50 hover:bg-blue-500/20 hover:shadow-lg hover:shadow-blue-500/20 active:scale-95 transition-all duration-300 text-center whitespace-nowrap"
                                                    >
                                                        Manage
                                                    </Link>
                                                    <div className="relative" ref={openDropdownId === course.id ? dropdownRef : null}>
                                                        <button
                                                            onClick={() => toggleDropdown(course.id)}
                                                            className="p-2.5 border-2 border-[var(--border-strong)] rounded-lg hover:bg-[var(--input-bg)] hover:border-blue-500/30 active:scale-95 transition-all duration-300 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                                        >
                                                            <FaEllipsisV className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                                                        </button>

                                                        {/* Dropdown Menu */}
                                                        {openDropdownId === course.id && (

                                                            <div className="absolute right-0 mt-2 z-50 w-36 bg-[var(--card-strong-bg)] border-2 border-[var(--border-strong)] rounded-xl shadow-2xl py-1.5 flex flex-col text-sm animate-fade-in">
                                                                <button
                                                                    className="flex items-center gap-2.5 px-4 py-2.5 hover:bg-blue-500/10 text-emrald-400 hover:text-emrald-300 transition-colors duration-200"
                                                                    onClick={() => handleEditClick(course.id)}
                                                                >
                                                                    <FaEdit className="w-4 h-4" /> Edit
                                                                </button>

                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Edit Course Modal */}
            {showEditModal && (
                <AddCourseModal
                    onCancel={() => {
                        setShowEditModal(false);
                        setEditingCourseId(null);
                    }}
                    courseId={editingCourseId}
                    isEdit={true}
                    onSuccess={handleCourseSuccess}
                />
            )}

            {/* Add Course Modal */}
            {showAddModal && (
                <AddCourseModal
                    onCancel={() => setShowAddModal(false)}
                    onSuccess={handleCourseSuccess}
                />
            )}
        </div>
    );
};

export default Courses;
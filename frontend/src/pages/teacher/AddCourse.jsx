import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import CourseActionButtons from '../../components/teacher/CourseActionButtons';
import { createCourse, updateCourse, getTeacherCourse } from '../../api/api';
import useGradingSystemStore from '../../store/teacherGradeStore';
import { FaTrash } from 'react-icons/fa';

const AddCourse = () => {
    const { gradingSystems, loadGradingSystems, loading: gradingLoading } = useGradingSystemStore();
    
    const navigate = useNavigate();
    const { courseId } = useParams();
    const [searchParams] = useSearchParams();
    const editCourseId = courseId || searchParams.get('courseId');
    const isEditMode = !!editCourseId;

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

    // For now, drafts are just UI placeholders
    const drafts = [
        {
            id: 1,
            title: 'Introduction to Environmental Science',
            instructions: 'Test your knowledge about environmental science basics, including renewable energy, ecosystems, and sustainability.',
            code: '0001',
            savedAt: '2 hours ago',
        },
        {
            id: 2,
            title: 'Advanced Machine Learning',
            instructions: 'Deep dive into neural networks, deep learning, and AI applications',
            code: '0002',
            savedAt: '1 day ago',
        },
        {
            id: 3,
            title: 'Web Development Bootcamp',
            instructions: 'Complete guide to modern web development with React and Node.js',
            code: '0003',
            savedAt: '3 days ago',
        },
    ];

    useEffect(() => {
        if (isEditMode) {
            loadCourse();
        }
        // eslint-disable-next-line
    }, [editCourseId]);

    useEffect(() => {
        loadGradingSystems();
        // ...existing code...
    }, []);



    const loadCourse = async () => {
        try {
            setLoading(true);
            const course = await getTeacherCourse(editCourseId);
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

            if (isEditMode) {
                await updateCourse(editCourseId, submitData);
            } else {
                const result = await createCourse(submitData);
                navigate(`/teacher/courses/${result.id}/manage`);
                return;
            }
            navigate('/teacher/courses');
        } catch (err) {
            console.error('Failed to save course:', err);
            setError(err.response?.data?.error || 'Failed to save course');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="p-8 flex items-center justify-center min-h-[400px]">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p className="text-gray-400">Loading course...</p>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Header Section */}
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Courses</h1>
                        <p className="text-sm muted">Create, manage and analyze your courses</p>
                    </div>
                    {/* Action Buttons */}
                    <CourseActionButtons activeButton="create" />
                    <div className="flex flex-col xl:flex-row gap-4 sm:gap-6 lg:gap-8">
                        {/* Main Card */}
                        <div className="flex-1 card-strong rounded-xl sm:rounded-2xl overflow-hidden">
                            {/* Card Header */}
                            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[var(--border-color)] gap-3 sm:gap-4">
                                <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                                    <button
                                        type="button"
                                        onClick={() => navigate('/teacher/courses')}
                                        className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-[var(--input-bg)] border border-[var(--border-color)] flex items-center justify-center hover:bg-[var(--border-subtle)] transition flex-shrink-0"
                                    >
                                        <svg
                                            className="w-4 h-4 sm:w-5 sm:h-5"
                                            fill="none"
                                            stroke="currentColor"
                                            viewBox="0 0 24 24"
                                            strokeWidth="2"
                                        >
                                            <path
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                d="M15 19l-7-7 7-7"
                                            />
                                        </svg>
                                    </button>
                                    <div className="min-w-0 flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h2 className="text-lg sm:text-xl font-bold">
                                                {isEditMode ? 'Edit Course' : 'Create New Course'}
                                            </h2>
                                        </div>
                                        <p className="text-xs sm:text-sm muted line-clamp-1">
                                            {isEditMode
                                                ? 'Update course details and settings'
                                                : 'Add details, set timings and configure course settings'}
                                        </p>
                                    </div>
                                </div>
                                
                            </div>
                            {/* Form Content */}
                            <form onSubmit={handleSubmit}>
                                <div className="p-4 sm:p-6 lg:p-8">
                                    <div className="grid lg:grid-cols-2 gap-6 sm:gap-8">
                                        {/* Left Column - Course Details */}
                                        <div>
                                            <div className="mb-5 sm:mb-6">
                                                <h3 className="text-base sm:text-lg font-bold mb-1">Course Details</h3>
                                                <p className="text-xs sm:text-sm muted">Basic information about your Course</p>
                                            </div>
                                            {/* Course Title */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Course Title 
                                                </label>
                                                <input
                                                    type="text"
                                                    name="name"
                                                    value={formData.name}
                                                    onChange={handleChange}
                                                    required
                                                    placeholder="Enter course title"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                />
                                            </div>
                                            {/* Instructions */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Instructions
                                                </label>
                                                <textarea
                                                    name="instructions"
                                                    rows="12"
                                                    value={formData.instructions}
                                                    onChange={handleChange}
                                                    placeholder="Enter course instructions"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg resize-none text-sm"
                                                />
                                            </div>
                                            {/* Code and Enrollment */}
                                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Code
                                                    </label>
                                                    <input
                                                        type="text"
                                                        name="code"
                                                        value={formData.code}
                                                        onChange={handleChange}
                                                        placeholder="xxxx"
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Enrollment
                                                    </label>
                                                    <select
                                                        name="enrollment"
                                                        value={formData.enrollment}
                                                        onChange={handleChange}
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    >
                                                        <option value="">---------</option>
                                                        <option value="default">Enroll Request</option>
                                                        <option value="open">Open Enrollment</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        {/* Right Column - Course Settings */}
                                        <div>
                                            <div className="mb-5 sm:mb-6">
                                                <h3 className="text-base sm:text-lg font-bold mb-1">Course Settings</h3>
                                                <p className="text-xs sm:text-sm muted">Configure how your course works</p>
                                            </div>
                                            {/* Start date & Time */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Start Enrollment Date & Time
                                                </label>
                                                <input
                                                    type="datetime-local"
                                                    name="start_enroll_time"
                                                    value={formData.start_enroll_time}
                                                    onChange={handleChange}
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                />
                                            </div>
                                            {/* End date & Time */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    End Enrollment Date & Time
                                                </label>
                                                <input
                                                    type="datetime-local"
                                                    name="end_enroll_time"
                                                    value={formData.end_enroll_time}
                                                    onChange={handleChange}
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                />
                                            </div>
                                            {/* Grading System */}
                                            <div className="mb-5 sm:mb-6">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Grading System
                                                </label>
                                                <select
                                                    name="grading_system_id"
                                                    value={formData.grading_system_id}
                                                    onChange={handleChange}
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                >
                                                    <option value="">---------</option>
                                                    {gradingSystems.map(gs => (
                                                        <option key={gs.id} value={gs.id}>
                                                            {gs.name}
                                                        </option>
                                                    ))}
                                                </select>
                                                <p className="text-xs muted mt-1">Leave empty if not using a grading system</p>
                                                {gradingLoading && <p className="text-xs text-blue-500 mt-1">Loading grading systems...</p>}
                                            </div>
                                            {/* View Grade Toggle */}
                                            <div className="p-3 sm:p-4 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)] mb-5">
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
                                            <div className="p-3 sm:p-4 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)]">
                                                <div className="flex items-center justify-between gap-3">
                                                    <div>
                                                        <div className="text-sm sm:text-base font-semibold mb-1">Active</div>
                                                        <div className="text-xs muted">Course ready for Enrollment</div>
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
                                    {/* Bottom Action Buttons */}
                                    <div className="flex justify-between gap-3 mt-6 sm:mt-8 pt-5 sm:pt-6 border-t border-white/10">
                                        <button
                                            type="button"
                                            onClick={() => navigate('/teacher/courses')}
                                            className="border border-white/10 px-4 sm:px-6 py-2 sm:py-2.5 rounded-lg font-medium hover:bg-white/5 active:scale-95 transition flex items-center justify-center gap-2 text-sm flex-1 sm:flex-initial"
                                        >
                                            <svg
                                                className="w-4 h-4 sm:w-5 sm:h-5"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                                strokeWidth="2"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    d="M15 19l-7-7 7-7"
                                                />
                                            </svg>
                                            <span className="hidden sm:inline">Cancel</span>
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={saving}
                                            className="bg-blue-600 text-white px-5 sm:px-8 py-2 sm:py-2.5 rounded-lg font-semibold hover:bg-blue-700 active:scale-95 transition text-sm flex-1 sm:flex-initial disabled:opacity-50"
                                        >
                                            {saving ? 'Saving...' : (isEditMode ? 'Update Course' : 'Create')}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                        {/* Drafts UI (no functionality) */}
                        <div className="xl:w-80 2xl:w-96">
                            <div className="card-strong p-4 sm:p-6 rounded-xl sm:rounded-2xl sticky top-6">
                                <div className="mb-4">
                                    <h3 className="text-base sm:text-lg font-bold mb-1">Course Drafts</h3>
                                    <p className="text-xs sm:text-sm muted">Your saved course drafts</p>
                                </div>
                                {drafts.length > 0 ? (
                                    <div className="space-y-3">
                                        {drafts.map((draft) => (
                                            <div
                                                key={draft.id}
                                                className="p-3 sm:p-4 rounded-lg bg-[var(--input-bg)] border border-[var(--border-color)] hover:border-[var(--border-subtle)] transition group"
                                            >
                                                <div className="flex items-start justify-between gap-2 mb-2">
                                                    <div className="flex-1 min-w-0">
                                                        <h4 className="font-semibold text-sm line-clamp-1">
                                                            {draft.title}
                                                        </h4>
                                                        <span className="text-xs text-[var(--text-muted)]">Code: {draft.code}</span>
                                                    </div>
                                                    <button
                                                        className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 transition p-1 cursor-not-allowed"
                                                        title="Delete draft"
                                                        disabled
                                                    >
                                                        <FaTrash className="w-3 h-3" />
                                                    </button>
                                                </div>
                                                <p className="text-xs muted line-clamp-2 mb-3">
                                                    {draft.instructions}
                                                </p>
                                                <div className="flex items-center justify-between gap-2">
                                                    <span className="text-xs muted">{draft.savedAt}</span>
                                                    <button
                                                        className="text-xs text-blue-500 hover:text-blue-400 font-medium transition cursor-not-allowed"
                                                        disabled
                                                    >
                                                        Load
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8">
                                        <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-[var(--input-bg)] flex items-center justify-center mx-auto mb-3">
                                            <svg
                                                className="w-6 h-6 sm:w-7 sm:h-7 text-[var(--text-muted)]"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth="2"
                                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                                />
                                            </svg>
                                        </div>
                                        <p className="text-xs sm:text-sm muted">No saved drafts yet</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default AddCourse;
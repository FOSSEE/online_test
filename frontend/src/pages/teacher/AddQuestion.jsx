import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import QuestionActionButtons from '../../components/teacher/QuestionActionButtons';
import useQuestionsStore from '../../store/questionsStore';
import { FaTrash, FaUpload, FaFileAlt, FaCheckCircle, FaPlus } from 'react-icons/fa';

const defaultFormData = {
    summary: '',
    description: '',
    type: '',
    language: 'python',
    points: 1.0,
    active: true,
    topic: '',
    snippet: '',
    solution: '',
    partial_grading: false,
    grade_assignment_upload: false,
    min_time: 0,
};

const getDefaultTestCase = (questionType) => {
    switch (questionType) {
        case 'mcq':
            return {
                type: 'mcqtestcase',
                options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                correct: 0
            };
        case 'mcc':
            return {
                type: 'mcqtestcase',
                options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                correct: []
            };
        case 'code':
            return {
                type: 'stdiobasedtestcase',
                expected_input: '',
                expected_output: '',
                weight: 1.0,
                hidden: false
            };
        case 'assignment_upload':
            return {
                type: 'uploadtestcase',
                description: '',
                required: true
            };
        case 'integer':
            return {
                type: 'integertestcase',
                correct: 0
            };
        case 'float':
            return {
                type: 'floattestcase',
                correct: 0.0,
                error_margin: 0.0
            };
        case 'string':
            return {
                type: 'stringtestcase',
                correct: '',
                string_check: 'lower'
            };
        case 'arrange':
            return {
                type: 'arrangetestcase',
                options: ['Option 1', 'Option 2', 'Option 3']
            };
        default:
            return { type: 'stdiobasedtestcase', expected_output: '', weight: 1.0 };
    }
};

const AddQuestion = () => {
    const navigate = useNavigate();
    const { createQuestion, uploadQuestionFile } = useQuestionsStore();

    const [formData, setFormData] = useState(defaultFormData);
    const [testCases, setTestCases] = useState([]);
    const [pendingFiles, setPendingFiles] = useState([]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    // Non-functional draft data (UI placeholder)
    const drafts = [
        {
            id: 1,
            summary: 'Python List Comprehension',
            type: 'code',
            language: 'python',
            points: 5.0,
            savedAt: '2 hours ago',
        },
        {
            id: 2,
            summary: 'Database Normalization MCQ',
            type: 'mcq',
            language: 'select',
            points: 2.0,
            savedAt: '1 day ago',
        },
        {
            id: 3,
            summary: 'JavaScript Async/Await',
            type: 'code',
            language: 'javascript',
            points: 10.0,
            savedAt: '3 days ago',
        },
    ];

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) : value)
        }));
    };

    const addTestCase = () => {
        const newTestCase = getDefaultTestCase(formData.type);
        setTestCases([...testCases, newTestCase]);
    };

    const updateTestCase = (index, field, value) => {
        const updated = [...testCases];
        updated[index] = { ...updated[index], [field]: value };
        setTestCases(updated);
    };

    const removeTestCase = (index) => {
        setTestCases(testCases.filter((_, i) => i !== index));
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        const newFiles = files.map(file => ({
            file,
            name: file.name,
            size: file.size,
            id: Date.now() + Math.random()
        }));
        setPendingFiles([...pendingFiles, ...newFiles]);
        e.target.value = '';
    };

    const removePendingFile = (fileId) => {
        setPendingFiles(pendingFiles.filter(f => f.id !== fileId));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        try {
            const result = await createQuestion({
                ...formData,
                test_cases: testCases,
            });

            if (pendingFiles.length > 0 && result.id) {
                for (const fileObj of pendingFiles) {
                    try {
                        await uploadQuestionFile(result.id, fileObj.file);
                    } catch (err) {
                        console.error(`Failed to upload file ${fileObj.name}:`, err);
                    }
                }
            }
            
            navigate('/teacher/questions');
        } catch (err) {
            console.error('Failed to create question:', err);
            setError(err.response?.data?.error || 'Failed to create question');
        } finally {
            setSaving(false);
        }
    };

    const questionTypes = [
        { value: '', label: 'Select Type' },
        { value: 'code', label: 'Code' },
        { value: 'mcq', label: 'Multiple Choice (Single)' },
        { value: 'mcc', label: 'Multiple Choice (Multiple)' },
        { value: 'integer', label: 'Integer' },
        { value: 'float', label: 'Float' },
        { value: 'string', label: 'String' },
        { value: 'arrange', label: 'Arrange' },
        { value: 'assignment_upload', label: 'Assignment Upload' },
    ];

    const languages = [
        { value: 'python', label: 'Python' },
        { value: 'java', label: 'Java' },
        { value: 'cpp', label: 'C++' },
        { value: 'javascript', label: 'JavaScript' },
        { value: 'bash', label: 'Bash' },
        { value: 'r', label: 'R' },
        { value: 'scilab', label: 'Scilab' },
    ];

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Header Section */}
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Questions</h1>
                        <p className="text-sm muted">Create, manage and organize your question bank</p>
                    </div>

                    {/* Action Buttons */}
                    <QuestionActionButtons activeButton="create" />

                    <div className="flex flex-col xl:flex-row gap-4 sm:gap-6 lg:gap-8">
                        {/* Main Card */}
                        <div className="flex-1 card-strong rounded-xl sm:rounded-2xl overflow-hidden">
                            {/* Card Header */}
                            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-[var(--border-color)] gap-3 sm:gap-4">
                                <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                                    <button
                                        type="button"
                                        onClick={() => navigate('/teacher/questions')}
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
                                            <h2 className="text-lg sm:text-xl font-bold">Create New Question</h2>
                                        </div>
                                        <p className="text-xs sm:text-sm muted line-clamp-1">
                                            Add question details, test cases and configure settings
                                        </p>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    className="bg-orange-600 text-white px-3 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold hover:bg-orange-700 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap flex-shrink-0 opacity-60 cursor-not-allowed"
                                    disabled
                                >
                                    <span className="hidden sm:inline">Save Draft</span>
                                    <span className="sm:hidden">Draft</span>
                                </button>
                            </div>

                            {/* Form Content */}
                            <form onSubmit={handleSubmit}>
                                <div className="p-4 sm:p-6 lg:p-8">
                                    {error && (
                                        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                            {error}
                                        </div>
                                    )}

                                    <div className="grid lg:grid-cols-2 gap-6 sm:gap-8">
                                        {/* Left Column - Question Details */}
                                        <div>
                                            <div className="mb-5 sm:mb-6">
                                                <h3 className="text-base sm:text-lg font-bold mb-1">Question Details</h3>
                                                <p className="text-xs sm:text-sm muted">Basic information about your question</p>
                                            </div>

                                            {/* Summary */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Summary <span className="text-red-400">*</span>
                                                </label>
                                                <input
                                                    type="text"
                                                    name="summary"
                                                    value={formData.summary}
                                                    onChange={handleChange}
                                                    required
                                                    placeholder="Enter question summary"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                />
                                            </div>

                                            {/* Description */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Description
                                                </label>
                                                <textarea
                                                    name="description"
                                                    rows="6"
                                                    value={formData.description}
                                                    onChange={handleChange}
                                                    placeholder="Enter question description"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg resize-none text-sm"
                                                />
                                            </div>

                                            {/* Type and Language */}
                                            <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-5">
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Type <span className="text-red-400">*</span>
                                                    </label>
                                                    <select
                                                        name="type"
                                                        value={formData.type}
                                                        onChange={handleChange}
                                                        required
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    >
                                                        {questionTypes.map(type => (
                                                            <option key={type.value} value={type.value}>
                                                                {type.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Language
                                                    </label>
                                                    <select
                                                        name="language"
                                                        value={formData.language}
                                                        onChange={handleChange}
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    >
                                                        {languages.map(lang => (
                                                            <option key={lang.value} value={lang.value}>
                                                                {lang.label}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>

                                            {/* Points and Min Time */}
                                            <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4 sm:mb-5">
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Points
                                                    </label>
                                                    <input
                                                        type="number"
                                                        name="points"
                                                        step="0.1"
                                                        value={formData.points}
                                                        onChange={handleChange}
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                        Min Time (mins)
                                                    </label>
                                                    <input
                                                        type="number"
                                                        name="min_time"
                                                        value={formData.min_time}
                                                        onChange={handleChange}
                                                        className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                    />
                                                </div>
                                            </div>

                                            {/* Topic */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Topic
                                                </label>
                                                <input
                                                    type="text"
                                                    name="topic"
                                                    value={formData.topic}
                                                    onChange={handleChange}
                                                    placeholder="Enter topic"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-sm"
                                                />
                                            </div>
                                        </div>

                                        {/* Right Column - Additional Settings */}
                                        <div>
                                            <div className="mb-5 sm:mb-6">
                                                <h3 className="text-base sm:text-lg font-bold mb-1">Additional Settings</h3>
                                                <p className="text-xs sm:text-sm muted">Configure question behavior</p>
                                            </div>

                                            {/* Snippet */}
                                            <div className="mb-4 sm:mb-5">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Code Snippet
                                                </label>
                                                <textarea
                                                    name="snippet"
                                                    rows="6"
                                                    value={formData.snippet}
                                                    onChange={handleChange}
                                                    placeholder="Enter code snippet"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg resize-none text-sm font-mono"
                                                />
                                            </div>

                                            {/* Solution */}
                                            <div className="mb-5 sm:mb-6">
                                                <label className="block text-xs sm:text-sm font-semibold soft mb-2">
                                                    Solution
                                                </label>
                                                <textarea
                                                    name="solution"
                                                    rows="6"
                                                    value={formData.solution}
                                                    onChange={handleChange}
                                                    placeholder="Enter solution"
                                                    className="w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg resize-none text-sm font-mono"
                                                />
                                            </div>

                                            {/* Checkboxes - Enhanced UI */}
                                            <div className="space-y-4">
                                                {/* Active */}
                                                <label className="flex items-center gap-2 cursor-pointer select-none group">
                                                    <div className="relative">
                                                        <input
                                                            type="checkbox"
                                                            name="active"
                                                            checked={formData.active}
                                                            onChange={handleChange}
                                                            className="peer sr-only"
                                                        />
                                                        <div className="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-blue-600 transition-all duration-300"></div>
                                                        <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 peer-checked:translate-x-5"></div>
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-200 group-hover:text-white transition">Active</span>
                                                </label>

                                                {/* Partial Grading */}
                                                <label className="flex items-center gap-2 cursor-pointer select-none group">
                                                    <div className="relative">
                                                        <input
                                                            type="checkbox"
                                                            name="partial_grading"
                                                            checked={formData.partial_grading}
                                                            onChange={handleChange}
                                                            className="peer sr-only"
                                                        />
                                                        <div className="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-green-600 transition-all duration-300"></div>
                                                        <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 peer-checked:translate-x-5"></div>
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-200 group-hover:text-white transition">Partial Grading</span>
                                                </label>

                                                {/* Grade Assignment Upload */}
                                                <label className="flex items-center gap-2 cursor-pointer select-none group">
                                                    <div className="relative">
                                                        <input
                                                            type="checkbox"
                                                            name="grade_assignment_upload"
                                                            checked={formData.grade_assignment_upload}
                                                            onChange={handleChange}
                                                            className="peer sr-only"
                                                        />
                                                        <div className="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-purple-600 transition-all duration-300"></div>
                                                        <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-all duration-300 peer-checked:translate-x-5"></div>
                                                    </div>
                                                    <span className="text-sm font-medium text-gray-200 group-hover:text-white transition">Grade Assignment Upload</span>
                                                </label>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Pending Files Display */}
                                    {pendingFiles.length > 0 && (
                                        <div className="mt-6 relative overflow-hidden bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-xl p-5 border border-blue-500/20">
                                            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl"></div>
                                            <div className="relative">
                                                <div className="flex items-center gap-2 mb-4">
                                                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                                        <FaFileAlt className="text-blue-400 w-5 h-5" />
                                                    </div>
                                                    <div>
                                                        <h2 className="text-lg font-bold">Files to Upload</h2>
                                                        <p className="text-xs text-gray-400">{pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''} ready</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-3">
                                                    {pendingFiles.map((fileObj) => (
                                                        <div key={fileObj.id} className="group bg-black/20 hover:bg-black/30 rounded-lg p-3 border border-white/5 hover:border-blue-500/30 transition-all duration-200">
                                                            <div className="flex items-center gap-3">
                                                                <FaFileAlt className="text-blue-400 w-4 h-4 flex-shrink-0" />
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-medium text-gray-300 truncate">{fileObj.name}</p>
                                                                    <p className="text-xs text-gray-500">{formatFileSize(fileObj.size)}</p>
                                                                </div>
                                                                <button
                                                                    type="button"
                                                                    onClick={() => removePendingFile(fileObj.id)}
                                                                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all duration-200"
                                                                >
                                                                    <FaTrash className="w-3 h-3" />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Upload File Section */}
                                    <div className="mt-6 relative overflow-hidden bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-xl p-5 border border-purple-500/20">
                                        <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl"></div>
                                        <div className="relative">
                                            <div className="flex items-center gap-3 mb-3">
                                                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                                    <FaUpload className="text-purple-400 w-5 h-5" />
                                                </div>
                                                <div>
                                                    <label className="text-sm font-semibold text-gray-200 block">Upload Files</label>
                                                    <p className="text-xs text-gray-400">Attach files to this question</p>
                                                </div>
                                            </div>
                                            <div className="relative group">
                                                <input
                                                    type="file"
                                                    id="file-upload"
                                                    onChange={handleFileSelect}
                                                    multiple
                                                    className="hidden"
                                                />
                                                <label 
                                                    htmlFor="file-upload"
                                                    className="flex items-center justify-center gap-3 w-full px-6 py-4 border-2 border-dashed border-purple-500/30 rounded-lg cursor-pointer hover:border-purple-500/50 hover:bg-purple-500/5 transition-all duration-200 group-hover:scale-[1.02]"
                                                >
                                                    <FaUpload className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform duration-200" />
                                                    <div className="text-center">
                                                        <span className="text-sm font-medium text-gray-300 group-hover:text-white transition">
                                                            Click to browse or drag and drop
                                                        </span>
                                                        <p className="text-xs text-gray-400 mt-1">All file types supported • Multiple files allowed</p>
                                                    </div>
                                                </label>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Test Cases Section - Enhanced UI */}
                                    {formData.type && (
                                        <div className="mt-6 relative overflow-hidden bg-gradient-to-br from-green-500/5 to-cyan-500/5 rounded-xl p-5 border border-green-500/20">
                                            <div className="absolute top-0 left-0 w-40 h-40 bg-green-500/10 rounded-full blur-3xl"></div>
                                            <div className="relative">
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                                                            <FaCheckCircle className="text-green-400 w-5 h-5" />
                                                        </div>
                                                        <div>
                                                            <h2 className="text-lg font-bold">Test Cases</h2>
                                                            <p className="text-xs text-gray-400">{testCases.length} test case{testCases.length !== 1 ? 's' : ''}</p>
                                                        </div>
                                                    </div>
                                                    <button
                                                        type="button"
                                                        onClick={addTestCase}
                                                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 hover:scale-105"
                                                    >
                                                        <FaPlus className="w-3 h-3" />
                                                        Add Test Case
                                                    </button>
                                                </div>

                                                {testCases.length === 0 ? (
                                                    <div className="text-center py-8">
                                                        <div className="w-14 h-14 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-3">
                                                            <FaCheckCircle className="w-7 h-7 text-green-400" />
                                                        </div>
                                                        <p className="text-sm text-gray-400">No test cases added yet</p>
                                                        <p className="text-xs text-gray-500 mt-1">Click "Add Test Case" to get started</p>
                                                    </div>
                                                ) : (
                                                    <div className="space-y-4">
                                                        {testCases.map((tc, index) => (
                                                            <div key={index} className="group bg-black/20 hover:bg-black/30 rounded-lg p-4 border border-white/5 hover:border-green-500/30 transition-all duration-200">
                                                                <div className="flex items-center justify-between mb-3">
                                                                    <div className="flex items-center gap-3">
                                                                        <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                                                                            <span className="text-sm font-bold text-green-400">{index + 1}</span>
                                                                        </div>
                                                                        <span className="text-sm font-medium text-gray-300">Test Case {index + 1}</span>
                                                                    </div>
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => removeTestCase(index)}
                                                                        className="opacity-0 group-hover:opacity-100 p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all duration-200"
                                                                    >
                                                                        <FaTrash className="w-4 h-4" />
                                                                    </button>
                                                                </div>

                                                                {/* MCQ/MCC Test Case */}
                                                                {(formData.type === 'mcq' || formData.type === 'mcc') && (
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Options</label>
                                                                            {tc.options && tc.options.map((opt, optIdx) => (
                                                                                <div key={optIdx} className="mb-2">
                                                                                    <input
                                                                                        type="text"
                                                                                        value={opt}
                                                                                        onChange={(e) => {
                                                                                            const newOptions = [...tc.options];
                                                                                            newOptions[optIdx] = e.target.value;
                                                                                            updateTestCase(index, 'options', newOptions);
                                                                                        }}
                                                                                        className="w-full px-3 py-2 rounded-lg text-sm"
                                                                                        placeholder={`Option ${optIdx + 1}`}
                                                                                    />
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">
                                                                                Correct {formData.type === 'mcq' ? 'Option' : 'Options'}
                                                                            </label>
                                                                            {formData.type === 'mcq' ? (
                                                                                <select
                                                                                    value={tc.correct || 0}
                                                                                    onChange={(e) => updateTestCase(index, 'correct', parseInt(e.target.value))}
                                                                                    className="w-full px-3 py-2 rounded-lg text-sm"
                                                                                >
                                                                                    {tc.options && tc.options.map((_, optIdx) => (
                                                                                        <option key={optIdx} value={optIdx}>Option {optIdx + 1}</option>
                                                                                    ))}
                                                                                </select>
                                                                            ) : (
                                                                                <div className="space-y-2">
                                                                                    {tc.options && tc.options.map((opt, optIdx) => (
                                                                                        <label key={optIdx} className="flex items-center gap-2 text-sm cursor-pointer">
                                                                                            <div className="relative">
                                                                                                <input
                                                                                                    type="checkbox"
                                                                                                    checked={(tc.correct || []).includes(optIdx)}
                                                                                                    onChange={(e) => {
                                                                                                        const current = tc.correct || [];
                                                                                                        const newCorrect = e.target.checked
                                                                                                            ? [...current, optIdx]
                                                                                                            : current.filter(i => i !== optIdx);
                                                                                                        updateTestCase(index, 'correct', newCorrect);
                                                                                                    }}
                                                                                                    className="peer sr-only"
                                                                                                />
                                                                                                <div className="w-4 h-4 border-2 border-gray-500 rounded peer-checked:bg-green-500 peer-checked:border-green-500 transition-all duration-200"></div>
                                                                                                <svg className="absolute top-0 left-0 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                                                                                                </svg>
                                                                                            </div>
                                                                                            <span className="text-gray-300">Option {optIdx + 1}</span>
                                                                                        </label>
                                                                                    ))}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                )}

                                                                {/* Code/StdIO Test Case */}
                                                                {formData.type === 'code' && (
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Input</label>
                                                                            <textarea
                                                                                value={tc.expected_input || ''}
                                                                                onChange={(e) => updateTestCase(index, 'expected_input', e.target.value)}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm font-mono"
                                                                                rows="3"
                                                                                placeholder="Expected input"
                                                                            />
                                                                        </div>
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Expected Output</label>
                                                                            <textarea
                                                                                value={tc.expected_output || ''}
                                                                                onChange={(e) => updateTestCase(index, 'expected_output', e.target.value)}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm font-mono"
                                                                                rows="3"
                                                                                placeholder="Expected output"
                                                                            />
                                                                        </div>
                                                                        <div className="grid grid-cols-2 gap-3">
                                                                            <div>
                                                                                <label className="block text-xs font-semibold text-gray-400 mb-2">Weight</label>
                                                                                <input
                                                                                    type="number"
                                                                                    step="0.1"
                                                                                    value={tc.weight || 1.0}
                                                                                    onChange={(e) => updateTestCase(index, 'weight', parseFloat(e.target.value))}
                                                                                    className="w-full px-3 py-2 rounded-lg text-sm"
                                                                                />
                                                                            </div>
                                                                            <div className="flex items-end">
                                                                                <label className="flex items-center gap-2 cursor-pointer select-none">
                                                                                    <div className="relative">
                                                                                        <input
                                                                                            type="checkbox"
                                                                                            checked={tc.hidden || false}
                                                                                            onChange={(e) => updateTestCase(index, 'hidden', e.target.checked)}
                                                                                            className="peer sr-only"
                                                                                        />
                                                                                        <div className="w-4 h-4 border-2 border-gray-500 rounded peer-checked:bg-orange-500 peer-checked:border-orange-500 transition-all duration-200"></div>
                                                                                        <svg className="absolute top-0 left-0 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                                                                                        </svg>
                                                                                    </div>
                                                                                    <span className="text-xs text-gray-300">Hidden</span>
                                                                                </label>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )}

                                                                {/* Upload Test Case */}
                                                                {formData.type === 'assignment_upload' && (
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Description</label>
                                                                            <textarea
                                                                                value={tc.description || ''}
                                                                                onChange={(e) => updateTestCase(index, 'description', e.target.value)}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm"
                                                                                rows="3"
                                                                                placeholder="Describe what needs to be uploaded"
                                                                            />
                                                                        </div>
                                                                        <label className="flex items-center gap-2 cursor-pointer select-none">
                                                                            <div className="relative">
                                                                                <input
                                                                                    type="checkbox"
                                                                                    checked={tc.required !== undefined ? tc.required : true}
                                                                                    onChange={(e) => updateTestCase(index, 'required', e.target.checked)}
                                                                                    className="peer sr-only"
                                                                                />
                                                                                <div className="w-4 h-4 border-2 border-gray-500 rounded peer-checked:bg-green-500 peer-checked:border-green-500 transition-all duration-200"></div>
                                                                                <svg className="absolute top-0 left-0 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                                                                                </svg>
                                                                            </div>
                                                                            <span className="text-xs text-gray-300">Required</span>
                                                                        </label>
                                                                    </div>
                                                                )}

                                                                {/* Integer Test Case */}
                                                                {formData.type === 'integer' && (
                                                                    <div>
                                                                        <label className="block text-xs font-semibold text-gray-400 mb-2">Correct Answer</label>
                                                                        <input
                                                                            type="number"
                                                                            value={tc.correct || 0}
                                                                            onChange={(e) => updateTestCase(index, 'correct', parseInt(e.target.value))}
                                                                            className="w-full px-3 py-2 rounded-lg text-sm"
                                                                        />
                                                                    </div>
                                                                )}

                                                                {/* Float Test Case */}
                                                                {formData.type === 'float' && (
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Correct Answer</label>
                                                                            <input
                                                                                type="number"
                                                                                step="0.01"
                                                                                value={tc.correct || 0.0}
                                                                                onChange={(e) => updateTestCase(index, 'correct', parseFloat(e.target.value))}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm"
                                                                            />
                                                                        </div>
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Error Margin</label>
                                                                            <input
                                                                                type="number"
                                                                                step="0.01"
                                                                                value={tc.error_margin || 0.0}
                                                                                onChange={(e) => updateTestCase(index, 'error_margin', parseFloat(e.target.value))}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm"
                                                                            />
                                                                        </div>
                                                                    </div>
                                                                )}

                                                                {/* String Test Case */}
                                                                {formData.type === 'string' && (
                                                                    <div className="space-y-3">
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">Correct Answer</label>
                                                                            <input
                                                                                type="text"
                                                                                value={tc.correct || ''}
                                                                                onChange={(e) => updateTestCase(index, 'correct', e.target.value)}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm"
                                                                            />
                                                                        </div>
                                                                        <div>
                                                                            <label className="block text-xs font-semibold text-gray-400 mb-2">String Check</label>
                                                                            <select
                                                                                value={tc.string_check || 'lower'}
                                                                                onChange={(e) => updateTestCase(index, 'string_check', e.target.value)}
                                                                                className="w-full px-3 py-2 rounded-lg text-sm"
                                                                            >
                                                                                <option value="lower">Lowercase</option>
                                                                                <option value="exact">Exact Match</option>
                                                                            </select>
                                                                        </div>
                                                                    </div>
                                                                )}

                                                                {/* Arrange Test Case */}
                                                                {formData.type === 'arrange' && (
                                                                    <div>
                                                                        <label className="block text-xs font-semibold text-gray-400 mb-2">Options (in correct order)</label>
                                                                        {tc.options && tc.options.map((opt, optIdx) => (
                                                                            <div key={optIdx} className="mb-2">
                                                                                <input
                                                                                    type="text"
                                                                                    value={opt}
                                                                                    onChange={(e) => {
                                                                                        const newOptions = [...tc.options];
                                                                                        newOptions[optIdx] = e.target.value;
                                                                                        updateTestCase(index, 'options', newOptions);
                                                                                    }}
                                                                                    className="w-full px-3 py-2 rounded-lg text-sm"
                                                                                    placeholder={`Option ${optIdx + 1}`}
                                                                                />
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Bottom Action Buttons */}
                                    <div className="flex justify-between gap-3 mt-6 sm:mt-8 pt-5 sm:pt-6 border-t border-white/10">
                                        <button
                                            type="button"
                                            onClick={() => navigate('/teacher/questions')}
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
                                            {saving ? 'Creating...' : 'Create Question'}
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>

                        {/* Drafts UI (non-functional) */}
                        <div className="xl:w-80 2xl:w-96">
                            <div className="card-strong p-4 sm:p-6 rounded-xl sm:rounded-2xl sticky top-6">
                                <div className="mb-4">
                                    <h3 className="text-base sm:text-lg font-bold mb-1">Question Drafts</h3>
                                    <p className="text-xs sm:text-sm muted">Your saved question drafts</p>
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
                                                            {draft.summary}
                                                        </h4>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
                                                                {draft.type}
                                                            </span>
                                                            <span className="text-xs text-[var(--text-muted)]">{draft.language}</span>
                                                        </div>
                                                    </div>
                                                    <button
                                                        className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 transition p-1 cursor-not-allowed"
                                                        title="Delete draft"
                                                        disabled
                                                    >
                                                        <FaTrash className="w-3 h-3" />
                                                    </button>
                                                </div>
                                                <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-white/5">
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

export default AddQuestion;
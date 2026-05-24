import React, { useState, useEffect } from 'react';
import { FaTimes, FaPlus, FaTrash, FaUpload, FaFileAlt, FaCheckCircle, FaExternalLinkAlt } from 'react-icons/fa';
import { FaRegQuestionCircle } from 'react-icons/fa';
import useQuestionsStore from '../../store/questionsStore';

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
            return { type: 'mcqtestcase', options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'], correct: 0 };
        case 'mcc':
            return { type: 'mcqtestcase', options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'], correct: [] };
        case 'code':
            return { type: 'stdiobasedtestcase', expected_input: '', expected_output: '', weight: 1.0, hidden: false };
        case 'assignment_upload':
            return { type: 'uploadtestcase', description: '', required: true };
        case 'integer':
            return { type: 'integertestcase', correct: 0 };
        case 'float':
            return { type: 'floattestcase', correct: 0.0, error_margin: 0.0 };
        case 'string':
            return { type: 'stringtestcase', correct: '', string_check: 'lower' };
        case 'arrange':
            return { type: 'arrangetestcase', options: ['Option 1', 'Option 2', 'Option 3'] };
        default:
            return { type: 'stdiobasedtestcase', expected_output: '', weight: 1.0 };
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
    { value: 'c', label: 'C' },
    { value: 'cpp', label: 'C++' },
    { value: 'bash', label: 'Bash' },
    { value: 'r', label: 'R' },
    { value: 'scilab', label: 'Scilab' },
];

export default function AddQuestionModal({ onCancel, questionId = null, isEdit = false, onSuccess }) {
    const { createQuestion, getQuestion, updateQuestion, uploadQuestionFile, deleteQuestionFile } = useQuestionsStore();

    const [formData, setFormData] = useState(defaultFormData);
    const [testCases, setTestCases] = useState([]);
    const [pendingFiles, setPendingFiles] = useState([]);
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isEdit && questionId) {
            loadQuestion();
        }
        // eslint-disable-next-line
    }, [isEdit, questionId]);

    const loadQuestion = async () => {
        try {
            setLoading(true);
            setError(null);
            const q = await getQuestion(questionId);
            if (q) {
                setFormData({
                    summary: q.summary || '',
                    description: q.description || '',
                    type: q.type || '',
                    language: q.language || 'python',
                    points: q.points || 1.0,
                    active: q.active !== undefined ? q.active : true,
                    topic: q.topic || '',
                    snippet: q.snippet || '',
                    solution: q.solution || '',
                    partial_grading: q.partial_grading || false,
                    grade_assignment_upload: q.grade_assignment_upload || false,
                    min_time: q.min_time || 0,
                    files: q.files || [],
                });
                setTestCases(q.test_cases || []);
            } else {
                setError('Failed to load question');
            }
        } catch {
            setError('Failed to load question');
        } finally {
            setLoading(false);
        }
    };

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

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        try {
            if (isEdit && questionId) {
                await updateQuestion(questionId, {
                    ...formData,
                    test_cases: testCases,
                    files: formData.files,
                });
                // Upload any new pending files for edit mode
                if (pendingFiles.length > 0) {
                    for (const fileObj of pendingFiles) {
                        try {
                            await uploadQuestionFile(questionId, fileObj.file);
                        } catch (err) {
                            console.error(`Failed to upload file ${fileObj.name}:`, err);
                        }
                    }
                }
            } else {
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
            }
            if (onSuccess) onSuccess();
            onCancel();
        } catch (err) {
            console.error('Failed to save question:', err);
            setError(err.response?.data?.error || `Failed to ${isEdit ? 'update' : 'create'} question`);
        } finally {
            setSaving(false);
        }
    };

    // Input class matching AddCourseModal
    const inputClass = "w-full px-3 sm:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl focus:outline-none focus:border-blue-500/50 text-sm transition-colors";

    if (loading) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2">
                <div className="card-strong w-full max-w-5xl p-6 relative rounded-2xl border-2 border-[var(--border-strong)]">
                    <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                            <p className="text-[var(--text-muted)]">Loading question...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-2 py-4 overflow-y-auto custom-scrollbar">
            <div className="card-strong w-full max-w-5xl p-4 sm:p-6 relative my-4 rounded-2xl border-2 border-[var(--border-strong)] max-h-[90vh] overflow-y-auto">

                {/* Close Button */}
                <button
                    type="button"
                    className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border-2 border-[var(--border-strong)] bg-[var(--input-bg)] hover:bg-red-500/10 hover:border-red-500/30 text-[var(--text-muted)] hover:text-red-400 transition-all z-10"
                    onClick={onCancel}
                    aria-label="Close"
                >
                    <FaTimes />
                </button>

                {/* Header */}
                <div className="flex flex-row items-center gap-4 mb-4 sm:mb-6 pb-4 border-b-2 border-[var(--border-subtle)] pr-12">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border-2 border-blue-500/30">
                        <FaRegQuestionCircle className="w-6 h-6 sm:w-7 sm:h-7 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h2 className="text-xl sm:text-2xl font-bold mb-1 line-clamp-1">
                            {isEdit ? 'Edit Question' : 'Add New Question'}
                        </h2>
                        <p className="text-xs sm:text-sm muted line-clamp-2">
                            {isEdit ? 'Update question details, test cases and settings' : 'Create a new question with details, test cases and settings'}
                        </p>
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-500/10 border-2 border-red-500/30 rounded-xl p-3 sm:p-4 text-red-400 mb-4 sm:mb-5 text-sm">
                        {error}
                    </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
                    <div className="grid lg:grid-cols-2 gap-5 sm:gap-6">
                        {/* Left Column - Question Details */}
                        <div className="space-y-4">
                            <div>
                                <h3 className="text-base sm:text-lg font-bold mb-1">Question Details</h3>
                                <p className="text-xs sm:text-sm muted mb-4">Basic information about your question</p>
                            </div>

                            {/* Summary */}
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2">
                                    Summary <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    name="summary"
                                    value={formData.summary}
                                    onChange={handleChange}
                                    required
                                    placeholder="Enter question summary"
                                    className={inputClass}
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2">
                                    Description
                                </label>
                                <textarea
                                    name="description"
                                    rows="5"
                                    value={formData.description}
                                    onChange={handleChange}
                                    placeholder="Enter question description (HTML supported)"
                                    className={`${inputClass} resize-none`}
                                />
                            </div>

                            {/* Type and Language */}
                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Type <span className="text-red-400">*</span>
                                    </label>
                                    <select
                                        name="type"
                                        value={formData.type}
                                        onChange={(e) => {
                                            handleChange(e);
                                            setTestCases([]);
                                        }}
                                        required
                                        className={inputClass}
                                    >
                                        {questionTypes.map(t => (
                                            <option key={t.value} value={t.value}>{t.label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Language <span className="text-red-400">*</span>
                                    </label>
                                    <select
                                        name="language"
                                        value={formData.language}
                                        onChange={handleChange}
                                        className={inputClass}
                                    >
                                        {languages.map(l => (
                                            <option key={l.value} value={l.value}>{l.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* Points and Min Time */}
                            <div className="grid grid-cols-2 gap-3 sm:gap-4">
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Points <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="number"
                                        name="points"
                                        step="0.1"
                                        min="0"
                                        value={formData.points}
                                        onChange={handleChange}
                                        required
                                        className={inputClass}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs sm:text-sm font-semibold mb-2">
                                        Min Time (m) <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="number"
                                        name="min_time"
                                        min="0"
                                        value={formData.min_time}
                                        onChange={handleChange}
                                        className={inputClass}
                                    />
                                </div>
                                
                            </div>
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2">
                                    Topic
                                </label>
                                <input
                                    type="text"
                                    name="topic"
                                    value={formData.topic}
                                    onChange={handleChange}
                                    placeholder="Optional topic"
                                    className={inputClass}
                                />
                            </div>
                            

                            {/* Active */}
                            <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                <div className="flex items-center justify-between gap-3">
                                    <div>
                                        <div className="text-sm sm:text-base font-semibold mb-0.5">Active</div>
                                        <div className="text-xs muted">Question is available for use</div>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleChange({ target: { name: 'active', type: 'checkbox', checked: !formData.active } })}
                                        className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${formData.active ? 'bg-green-500' : 'bg-gray-600'
                                            }`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.active ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Right Column - Additional Settings */}
                        <div className="space-y-4">
                            <div>
                                <h3 className="text-base sm:text-lg font-bold mb-1">Additional Settings</h3>
                                <p className="text-xs sm:text-sm muted mb-4">Configure question behavior and code</p>
                            </div>

                            {/* Snippet */}
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2.5">
                                    Code Snippet
                                </label>
                                <textarea
                                    name="snippet"
                                    rows="7"
                                    value={formData.snippet}
                                    onChange={handleChange}
                                    placeholder="Initial code snippet for students"
                                    className={`${inputClass} resize-none font-mono`}
                                />
                            </div>

                            {/* Solution */}
                            <div>
                                <label className="block text-xs sm:text-sm font-semibold mb-2.5">
                                    Solution
                                </label>
                                <textarea
                                    name="solution"
                                    rows="7"
                                    value={formData.solution}
                                    onChange={handleChange}
                                    placeholder="Solution or explanation"
                                    className={`${inputClass} resize-none font-mono`}
                                />
                            </div>

                            {/* Settings Toggles - Matching AddCourseModal toggle pattern */}
                            <div className="space-y-3">

                                {/* Grade Assignment Upload */}
                                <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <div className="text-sm sm:text-base font-semibold mb-0.5">Grade Upload</div>
                                            <div className="text-xs muted">Enable grading for uploaded assignments</div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'grade_assignment_upload', type: 'checkbox', checked: !formData.grade_assignment_upload } })}
                                            className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${formData.grade_assignment_upload ? 'bg-purple-600' : 'bg-gray-600'
                                                }`}
                                        >
                                            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.grade_assignment_upload ? 'translate-x-6' : 'translate-x-1'}`} />
                                        </button>
                                    </div>
                                </div>
                                

                                {/* Partial Grading */}
                                <div className="p-3 sm:p-4 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <div className="text-sm sm:text-base font-semibold mb-0.5">Partial Grading</div>
                                            <div className="text-xs muted">Allow partial marks for answers</div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'partial_grading', type: 'checkbox', checked: !formData.partial_grading } })}
                                            className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-[var(--bg-primary)] ${formData.partial_grading ? 'bg-blue-600' : 'bg-gray-600'
                                                }`}
                                        >
                                            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${formData.partial_grading ? 'translate-x-6' : 'translate-x-1'}`} />
                                        </button>
                                    </div>
                                </div>

                                
                            </div>
                        </div>
                    </div>

                    {/* ── Existing Files (Edit Mode Only) ── */}
                    {isEdit && formData.files && formData.files.length > 0 && (
                        <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 rounded-lg bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center">
                                    <FaFileAlt className="text-blue-400 w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-sm sm:text-base font-bold">Uploaded Files</h3>
                                    <p className="text-xs muted">{formData.files.length} file{formData.files.length !== 1 ? 's' : ''} attached</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {formData.files.map((file) => (
                                    <div key={file.id} className="flex items-center gap-3 flex-wrap p-3 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-all">
                                        {/* Delete */}
                                        <button
                                            type="button"
                                            className="px-3 py-1.5 border-2 border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/10 hover:border-red-500/50 text-xs font-semibold transition-all"
                                            onClick={async () => {
                                                if (window.confirm('Delete this file?')) {
                                                    try {
                                                        await deleteQuestionFile(file.id);
                                                        setFormData(prev => ({
                                                            ...prev,
                                                            files: prev.files.filter(f => f.id !== file.id),
                                                        }));
                                                    } catch {
                                                        alert('Failed to delete file');
                                                    }
                                                }
                                            }}
                                        >
                                            <FaTrash className="inline w-3 h-3 mr-1" /> Delete
                                        </button>

                                        {/* Extract */}
                                        <label className="flex items-center gap-2 text-xs cursor-pointer select-none px-3 py-1.5 rounded-lg hover:bg-[var(--surface-2)] transition">
                                            <input
                                                type="checkbox"
                                                checked={file.extract}
                                                onChange={(e) => {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        files: prev.files.map(f =>
                                                            f.id === file.id ? { ...f, extract: e.target.checked } : f
                                                        ),
                                                    }));
                                                }}
                                                className="w-4 h-4 rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] accent-green-500"
                                            />
                                            <span className="text-[var(--text-secondary)]">Extract</span>
                                        </label>

                                        {/* Hide */}
                                        <label className="flex items-center gap-2 text-xs cursor-pointer select-none px-3 py-1.5 rounded-lg hover:bg-[var(--surface-2)] transition">
                                            <input
                                                type="checkbox"
                                                checked={file.hide}
                                                onChange={(e) => {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        files: prev.files.map(f =>
                                                            f.id === file.id ? { ...f, hide: e.target.checked } : f
                                                        ),
                                                    }));
                                                }}
                                                className="w-4 h-4 rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] accent-orange-500"
                                            />
                                            <span className="text-[var(--text-secondary)]">Hide</span>
                                        </label>

                                        {/* File Link */}
                                        <a
                                            href={file.url?.startsWith('http') ? file.url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${file.url}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex-1 min-w-0 flex items-center gap-2 text-blue-400 hover:text-blue-300 text-xs font-medium truncate px-3 py-1.5 rounded-lg hover:bg-blue-500/10 transition-all"
                                        >
                                            <FaExternalLinkAlt className="w-3 h-3 flex-shrink-0" />
                                            <span className="truncate">{file.name}</span>
                                        </a>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Pending Files Display ── */}
                    {pendingFiles.length > 0 && (
                        <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border-2 border-cyan-500/30 flex items-center justify-center">
                                    <FaFileAlt className="text-cyan-400 w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-sm sm:text-base font-bold">Files to Upload</h3>
                                    <p className="text-xs muted">{pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''} ready</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {pendingFiles.map((fileObj) => (
                                    <div key={fileObj.id} className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-all">
                                        <FaFileAlt className="text-cyan-400 w-4 h-4 flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{fileObj.name}</p>
                                            <p className="text-xs muted">{formatFileSize(fileObj.size)}</p>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => removePendingFile(fileObj.id)}
                                            className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
                                        >
                                            <FaTrash className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* ── Upload File Section ── */}
                    <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-500/10 border-2 border-purple-500/30 flex items-center justify-center">
                                <FaUpload className="text-purple-400 w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm sm:text-base font-bold">Upload Files</h3>
                                <p className="text-xs muted">Attach files to this question</p>
                            </div>
                        </div>
                        <div className="relative group">
                            <input
                                type="file"
                                id="question-file-upload"
                                onChange={handleFileSelect}
                                multiple
                                className="hidden"
                            />
                            <label
                                htmlFor="question-file-upload"
                                className="flex items-center justify-center gap-3 w-full px-6 py-4 border-2 border-dashed border-[var(--border-strong)] rounded-xl cursor-pointer hover:border-purple-500/50 hover:bg-purple-500/5 transition-all duration-200 group-hover:scale-[1.01]"
                            >
                                <FaUpload className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform duration-200" />
                                <div className="text-center">
                                    <span className="text-sm font-medium text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition">
                                        Click to browse or drag and drop
                                    </span>
                                    <p className="text-xs muted mt-1">All file types supported • Multiple files allowed</p>
                                </div>
                            </label>
                        </div>
                    </div>

                    {/* ── Test Cases Section ── */}
                    {formData.type && (
                        <div className="p-4 sm:p-5 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)]">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-green-500/10 border-2 border-green-500/30 flex items-center justify-center">
                                        <FaCheckCircle className="text-green-400 w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="text-sm sm:text-base font-bold">Test Cases</h3>
                                        <p className="text-xs muted">{testCases.length} test case{testCases.length !== 1 ? 's' : ''}</p>
                                    </div>
                                </div>
                                {!(['arrange', 'mcq', 'mcc'].includes(formData.type) && testCases.length >= 1) && (
                                    <button
                                        type="button"
                                        onClick={addTestCase}
                                        className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-green-500/20 hover:shadow-green-500/40 flex items-center gap-2"
                                    >
                                        <FaPlus className="w-3 h-3" />
                                        Add Test Case
                                    </button>
                                )}
                            </div>

                            {testCases.length === 0 ? (
                                <div className="text-center py-8 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-subtle)]">
                                    <div className="w-14 h-14 rounded-full bg-green-500/10 border-2 border-green-500/20 flex items-center justify-center mx-auto mb-3">
                                        <FaCheckCircle className="w-7 h-7 text-green-400" />
                                    </div>
                                    <p className="text-sm text-[var(--text-muted)]">No test cases added yet</p>
                                    <p className="text-xs muted mt-1">Click "Add Test Case" to get started</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {testCases.map((tc, index) => (
                                        <div key={index} className="group rounded-xl p-4 bg-[var(--bg-primary)] border-2 border-[var(--border-subtle)] hover:border-green-500/30 transition-all">
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                                                        <span className="text-sm font-bold text-green-400">{index + 1}</span>
                                                    </div>
                                                    <span className="text-sm font-semibold">Test Case {index + 1}</span>
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => removeTestCase(index)}
                                                    className="opacity-0 group-hover:opacity-100 p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
                                                >
                                                    <FaTrash className="w-4 h-4" />
                                                </button>
                                            </div>

                                            <div className="space-y-3">
                                                {/* MCQ/MCC */}
                                                {(tc.type === 'mcqtestcase' || formData.type === 'mcq' || formData.type === 'mcc') && (
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Options (one per line)(line change by ENTER button)</label>
                                                            <textarea
                                                                value={Array.isArray(tc.options) ? tc.options.join('\n') : (tc.options || '')}
                                                                onChange={(e) => {
                                                                    const options = e.target.value.split('\n');
                                                                    updateTestCase(index, 'options', options);
                                                                }}
                                                                rows="4"
                                                                className={`${inputClass} resize-none`}
                                                                placeholder={"Option 1\nOption 2\nOption 3\nOption 4"}
                                                            />
                                                        </div>
                                                        
                                                        <div>
                                                            <label className="block text-xs font-semibold text-[var(--text-muted)] mb-2">
                                                                Correct {formData.type === 'mcq' ? 'Option' : 'Options'}
                                                            </label>
                                                            {formData.type === 'mcq' ? (
                                                                <select
                                                                    value={tc.correct || 0}
                                                                    onChange={(e) => updateTestCase(index, 'correct', parseInt(e.target.value))}
                                                                    className={inputClass}
                                                                >
                                                                    {(Array.isArray(tc.options) ? tc.options : []).map((_, optIdx) => (
                                                                        <option key={optIdx} value={optIdx}>Option {optIdx + 1}</option>
                                                                    ))}
                                                                </select>
                                                            ) : (
                                                                <div className="space-y-2 p-3 sm:p-4 rounded-xl bg-[var(--bg-primary)] border-2 border-[var(--border-subtle)]">
                                                                    {(Array.isArray(tc.options) ? tc.options : []).map((opt, optIdx) => (
                                                                        <label key={optIdx} className="flex items-center gap-3 text-sm cursor-pointer">
                                                                            <div className="relative">
                                                                                <input
                                                                                    type="checkbox"
                                                                                    checked={(Array.isArray(tc.correct) ? tc.correct : []).includes(optIdx)}
                                                                                    onChange={(e) => {
                                                                                        const current = Array.isArray(tc.correct) ? tc.correct : [];
                                                                                        const newCorrect = e.target.checked
                                                                                            ? [...current, optIdx]
                                                                                            : current.filter(i => i !== optIdx);
                                                                                        updateTestCase(index, 'correct', newCorrect);
                                                                                    }}
                                                                                    className="peer sr-only"
                                                                                />
                                                                                <div className="w-4 h-4 border-2 border-[var(--border-strong)] rounded peer-checked:bg-green-500 peer-checked:border-green-500 transition-all duration-200"></div>
                                                                                <svg className="absolute top-0 left-0 w-4 h-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                                                                                </svg>
                                                                            </div>
                                                                            <span className="text-[var(--text-primary)]">Option {optIdx + 1} <span className="opacity-50 line-clamp-1 text-xs">({opt})</span></span>
                                                                        </label>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Code/StdIO */}
                                                {(tc.type === 'stdiobasedtestcase' || (formData.type === 'code' && !tc.type?.includes('mcq'))) && (
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Expected Input (Optional)</label>
                                                            <textarea
                                                                value={tc.expected_input || ''}
                                                                onChange={(e) => updateTestCase(index, 'expected_input', e.target.value)}
                                                                rows="3"
                                                                className={`${inputClass} resize-none font-mono`}
                                                                placeholder="Input for the program"
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Expected Output *</label>
                                                            <textarea
                                                                value={tc.expected_output || ''}
                                                                onChange={(e) => updateTestCase(index, 'expected_output', e.target.value)}
                                                                required
                                                                rows="3"
                                                                className={`${inputClass} resize-none font-mono`}
                                                                placeholder="Expected output"
                                                            />
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-3">
                                                            <div>
                                                                <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Weight</label>
                                                                <input
                                                                    type="number"
                                                                    step="0.1"
                                                                    min="0"
                                                                    value={tc.weight || 1.0}
                                                                    onChange={(e) => updateTestCase(index, 'weight', parseFloat(e.target.value))}
                                                                    className={inputClass}
                                                                />
                                                            </div>
                                                            <div className="flex items-end pb-1">
                                                                <label className="flex items-center gap-2 cursor-pointer select-none px-3 py-2 rounded-lg hover:bg-[var(--surface-2)] transition">
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={tc.hidden || false}
                                                                        onChange={(e) => updateTestCase(index, 'hidden', e.target.checked)}
                                                                        className="w-4 h-4 rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] accent-orange-500"
                                                                    />
                                                                    <span className="text-sm text-[var(--text-secondary)]">Hidden</span>
                                                                </label>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Upload */}
                                                {(tc.type === 'uploadtestcase' || formData.type === 'assignment_upload') && (
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Description</label>
                                                            <input
                                                                type="text"
                                                                value={tc.description || ''}
                                                                onChange={(e) => updateTestCase(index, 'description', e.target.value)}
                                                                className={inputClass}
                                                                placeholder="Describe what needs to be uploaded"
                                                            />
                                                        </div>
                                                        <label className="flex items-center gap-2 cursor-pointer select-none px-3 py-2 rounded-lg hover:bg-[var(--surface-2)] transition">
                                                            <input
                                                                type="checkbox"
                                                                checked={tc.required !== undefined ? tc.required : true}
                                                                onChange={(e) => updateTestCase(index, 'required', e.target.checked)}
                                                                className="w-4 h-4 rounded border-2 border-[var(--border-strong)] bg-[var(--input-bg)] accent-red-500"
                                                            />
                                                            <span className="text-sm text-[var(--text-secondary)]">Required</span>
                                                        </label>
                                                    </div>
                                                )}

                                                {/* Integer */}
                                                {(tc.type === 'integertestcase' || (formData.type === 'integer' && !tc.type?.includes('mcq'))) && (
                                                    <div>
                                                        <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Correct Answer *</label>
                                                        <input
                                                            type="number"
                                                            value={tc.correct || 0}
                                                            onChange={(e) => updateTestCase(index, 'correct', parseInt(e.target.value))}
                                                            required
                                                            className={inputClass}
                                                        />
                                                    </div>
                                                )}

                                                {/* Float */}
                                                {(tc.type === 'floattestcase' || (formData.type === 'float' && !tc.type?.includes('mcq'))) && (
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Correct Answer *</label>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                value={tc.correct || 0.0}
                                                                onChange={(e) => updateTestCase(index, 'correct', parseFloat(e.target.value))}
                                                                required
                                                                className={inputClass}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Error Margin</label>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                min="0"
                                                                value={tc.error_margin || 0.0}
                                                                onChange={(e) => updateTestCase(index, 'error_margin', parseFloat(e.target.value))}
                                                                className={inputClass}
                                                            />
                                                        </div>
                                                    </div>
                                                )}

                                                {/* String */}
                                                {(tc.type === 'stringtestcase' || (formData.type === 'string' && !tc.type?.includes('mcq'))) && (
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Correct Answer *</label>
                                                            <input
                                                                type="text"
                                                                value={tc.correct || ''}
                                                                onChange={(e) => updateTestCase(index, 'correct', e.target.value)}
                                                                required
                                                                className={inputClass}
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">String Check Type</label>
                                                            <select
                                                                value={tc.string_check || 'lower'}
                                                                onChange={(e) => updateTestCase(index, 'string_check', e.target.value)}
                                                                className={inputClass}
                                                            >
                                                                <option value="lower">Case Insensitive</option>
                                                                <option value="exact">Exact Match</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Arrange */}
                                                {(tc.type === 'arrangetestcase' || (formData.type === 'arrange' && !tc.type?.includes('mcq'))) && (
                                                    <div>
                                                        <label className="block text-xs font-semibold mb-2 text-[var(--text-muted)]">Options (one per line, in correct order)(line change by ENTER button)</label>
                                                        <textarea
                                                            value={Array.isArray(tc.options) ? tc.options.join('\n') : (tc.options || '')}
                                                            onChange={(e) => {
                                                                const options = e.target.value.split('\n');
                                                                updateTestCase(index, 'options', options);
                                                            }}
                                                            rows="4"
                                                            className={`${inputClass} resize-none`}
                                                            placeholder={"Option 1\nOption 2\nOption 3"}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Action Buttons ── */}
                    <div className="flex gap-2 sm:gap-3 justify-end pt-4 border-t-2 border-[var(--border-subtle)]">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-blue-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm"
                            disabled={saving || !formData.type}
                        >
                            {saving ? 'Saving...' : (isEdit ? 'Update Question' : 'Create Question')}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

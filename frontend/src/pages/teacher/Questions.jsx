import React, { useEffect, useState } from 'react';
import { FaSearch, FaEdit, FaTrash, FaBook, FaCode, FaCheckCircle, FaEllipsisV, FaTimes, FaPlus, FaUpload, FaFileAlt, FaExternalLinkAlt, FaPlay, FaRegQuestionCircle } from 'react-icons/fa';
import { FaPersonCircleQuestion } from "react-icons/fa6";
import { CgArrangeFront } from "react-icons/cg";
import { BiSolidSelectMultiple } from "react-icons/bi";
import { MdOutlineFormatColorText } from "react-icons/md";
import { TbCircleDashedNumber1 } from "react-icons/tb";
import { TbDecimal } from "react-icons/tb";
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import Header from '../../components/layout/Header';
import useQuestionsStore from '../../store/questionsStore';
import QuestionActionButtons from '../../components/teacher/QuestionActionButtons';
import AddQuestionModal from '../../components/teacher/AddQuestionModal';
import { useNavigate } from 'react-router-dom';
import useQuizStore from '../../store/quiz_QuestionStore';

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
    min_time: 0,
};

const getDefaultTestCase = (questionType) => {
    switch (questionType) {
        case 'mcq':
            return {
                type: 'mcqtestcase',
                options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                correct: 0 // index of correct option
            };
        case 'mcc':
            return {
                type: 'mcqtestcase',
                options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
                correct: [] // array of indices
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

const Questions = () => {
    const {
        questions,
        loading,
        error,
        filters,
        setFilters,
        loadQuestions,
        deleteQuestion,
        getQuestion,
        updateQuestion
    } = useQuestionsStore();

    const { testQuestion } = useQuizStore(); 
    const navigate = useNavigate(); 


    const [actionMenuOpen, setActionMenuOpen] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [isEditMode, setIsEditMode] = useState(false);
    const [editingQuestionId, setEditingQuestionId] = useState(null);
    const [testingQuestionId, setTestingQuestionId] = useState(null); 



    useEffect(() => {
        loadQuestions();
    }, [filters, loadQuestions]);

    const handleAddClick = () => {
        setIsEditMode(false);
        setEditingQuestionId(null);
        setShowModal(true);
    };

    // Open edit modal and load question data
    const handleEdit = (question) => {
        setIsEditMode(true);
        setEditingQuestionId(question.id);
        setShowModal(true);
    };

    const handleModalSuccess = () => {
        loadQuestions();
        setShowModal(false);
    };

    const handleDelete = async (questionId) => {
        if (!window.confirm('Are you sure you want to delete this question? This will also remove it from all quizzes.')) {
            return;
        }
        try {
            await deleteQuestion(questionId);
        } catch (err) {
            alert('Failed to delete question');
        }
    };

    // Add this handler
    const handleTestQuestion = async (questionId) => {
        setTestingQuestionId(questionId);
        try {
            const result = await testQuestion(questionId);
            // Navigate to test quiz page with the returned IDs
            navigate(`/teacher/test-question/${result.questionpaper_id}/${result.module_id}/${result.course_id}`);
        } catch (error) {
            console.error('Error testing question:', error);
            alert(error.message || 'Failed to create test quiz');
        } finally {
            setTestingQuestionId(null);
        }
    };

    const getQuestionTypeIcon = (type) => {
        switch (type) {
            case 'code':
                return <FaCode className="w-5 h-5" />;
            case 'mcq':
                return <FaCheckCircle className="w-4 h-4" />;
            case 'mcc':
                return <BiSolidSelectMultiple className="w-5 h-5" />;
            case 'integer':
                return <TbCircleDashedNumber1 className="w-6 h-6" />;
            case 'float':
                return <TbDecimal className="w-8 h-8" />;
            case 'string':
                return <MdOutlineFormatColorText className="w-6 h-6" />;
            case 'arrange':
                return <CgArrangeFront className="w-6 h-6" />;
            default:
                return <FaUpload className="w-4 h-4" />;
        }
    };

    const getQuestionTypeColor = (type) => {
        switch (type) {
            case 'code':
                return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
            case 'mcq':
                return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
            case 'mcc':
                return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'integer':
                return 'bg-orange-500/10 text-orange-500 border-orange-500/30';
            case 'float':
                return 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30';
            case 'string':
                return 'bg-green-500/15 text-green-400 border-green-500/30';
            case 'arrange':
                return 'bg-red-500/15 text-red-400 border-red-500/30';
            default:
                return 'bg-pink-500/20 text-pink-400 border-pink-500/30';
        }
    };

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1 w-full lg:w-auto">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Page Header */}
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Questions</h1>
                        <p className="text-sm muted">Create and manage your questions</p>
                    </div>

                    {/* Action Buttons */}
                    <QuestionActionButtons activeButton="library" onAddClick={handleAddClick} />

                    {/* Questions Library Section */}
                    <div className="card-strong p-4 sm:p-5 lg:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                        <div className="mb-5 sm:mb-7 pb-4 border-b-2 border-[var(--border-subtle)] flex items-center gap-3">
                            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0">
                                <FaPersonCircleQuestion className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                            </div>
                            <div>
                                <h2 className="text-lg sm:text-xl font-bold mb-1">Question Library</h2>
                                <p className="text-xs sm:text-sm muted">Browse and manage all your questions</p>
                            </div>
                        </div>

                        {/* Filters and Search */}
                        <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 sm:gap-4 mb-6">
                            <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-5 gap-2 sm:gap-3 md:gap-4 flex-1 p-1.5">
                                <div className="col-span-2 sm:col-span-2 md:col-span-1">
                                    <div className="relative">
                                        <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] w-3.5 h-3.5 transition-colors" />
                                        <input
                                            type="text"
                                            placeholder="Search questions..."
                                            value={filters.search}
                                            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                                            className="w-full pl-9 sm:pl-10 pr-3 sm:pr-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <select
                                        value={filters.type}
                                        onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                                        className="w-full px-2 sm:px-3 md:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                                    >
                                        <option value="">Question Types...</option>
                                        <option value="mcq">Single Correct Choice</option>
                                        <option value="mcc">Multiple Correct Choices</option>
                                        <option value="code">Code</option>
                                        <option value="assignment_upload">Assignment Upload</option>
                                        <option value="integer">Answer in Integer</option>
                                        <option value="string">Answer in String</option>
                                        <option value="float">Answer in Float</option>
                                        <option value="arrange">Arrange in Correct Order</option>
                                    </select>
                                </div>
                                <div>
                                    <select
                                        value={filters.language}
                                        onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                                        className="w-full px-2 sm:px-3 md:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                                    >
                                        <option value="">Program Languages...</option>
                                        <option value="python">Python</option>
                                        <option value="java">Java</option>
                                        <option value="c">C</option>
                                        <option value="cpp">C++</option>
                                        <option value="bash">Bash</option>
                                    </select>
                                </div>
                                <div>
                                    <select
                                        value={filters.active === undefined ? '' : filters.active.toString()}
                                        onChange={(e) => setFilters({
                                            ...filters,
                                            active: e.target.value === '' ? undefined : e.target.value === 'true'
                                        })}
                                        className="w-full px-2 sm:px-3 md:px-4 py-2.5 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm focus:outline-none focus:border-blue-500/50 transition-colors"
                                    >
                                        <option value="">Status...</option>
                                        <option value="true">Active</option>
                                        <option value="false">Inactive</option>
                                    </select>
                                </div>
                                <div className="flex justify-end">
                                    <button
                                        className="px-3 sm:px-5 py-2.5 border-2 border-transparent bg-gradient-to-r from-blue-600 to-blue-500 rounded-xl text-xs sm:text-sm font-semibold hover:shadow-xl hover:shadow-blue-600/30 active:scale-95 transition-all duration-300 flex items-center justify-center gap-2 whitespace-nowrap"
                                        onClick={handleAddClick}
                                    >
                                        <FaPlus className="w-4 h-4" />
                                        <span className="hidden sm:inline">Add Question</span>
                                        <span className="sm:hidden">Add</span>
                                    </button>
                                </div>
                            </div>

                            {/* NEW: Add Question Button aligned with filters */}

                        </div>
                        {/* Loading State */}
                        {loading && (
                            <div className="flex items-center justify-center py-8 sm:py-12">
                                <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-b-2 border-blue-500"></div>
                            </div>
                        )}

                        {/* Error State */}
                        {error && !loading && (
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 sm:p-4 text-red-300 text-center text-xs sm:text-sm">
                                {error}
                            </div>
                        )}


                        {/* Questions List */}
                        {!loading && !error && (
                            <div className="space-y-3 sm:space-y-4">
                                {questions.length > 0 ? (
                                    questions.map((question) => (
                                        <div
                                            key={question.id}
                                            className="card-strong p-4 sm:p-5 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group bg-[var(--surface)] hover:shadow-md rounded-xl"
                                        >
                                            <div className="flex flex-row flex-wrap items-center gap-3 sm:gap-4">
                                                {/* Icon */}
                                                <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center flex-shrink-0 border-2 group-hover:scale-110 transition-all duration-300 ${getQuestionTypeColor(question.type)} shadow-sm bg-opacity-10 dark:bg-opacity-20`}>
                                                    <div className="text-xl sm:text-2xl">
                                                        {getQuestionTypeIcon(question.type)}
                                                    </div>
                                                </div>

                                                {/* Content */}
                                                <div className="flex-1 min-w-0 w-full sm:w-auto">
                                                    <div className="flex flex-wrap items-center gap-2 mb-2 sm:mb-3">
                                                        <h3 className="font-bold text-base sm:text-lg line-clamp-1 group-hover:text-blue-400 transition-colors duration-300">
                                                            {question.summary}
                                                        </h3>
                                                        <span className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${getQuestionTypeColor(question.type)}`}>
                                                            {question.type.toUpperCase()}
                                                        </span>

                                                        <span
                                                            className={`text-[10px] px-2 py-0.5 rounded-md border-2 uppercase font-bold tracking-wider whitespace-nowrap flex-shrink-0 transition-all duration-200 shadow-md ${question.active
                                                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-emerald-500/20'
                                                                : 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30 shadow-orange-500/20'
                                                                }`}
                                                        >
                                                            {question.active ? 'Active' : 'Inactive'}
                                                        </span>
                                                    </div>

                                                    {/* Meta Info (Grid equivalent to courses) */}
                                                    <div className="flex flex-wrap gap-2 sm:gap-4 text-xs muted font-medium">
                                                        <div className="flex items-center gap-1.5">
                                                            <span className="text-[var(--text-secondary)]">Lang:</span>
                                                            <span>{question.language || 'N/A'}</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5">
                                                            <span className="text-[var(--text-secondary)]">Pts:</span>
                                                            <span>{question.points}</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5">
                                                            <span className="text-[var(--text-secondary)]">Tests:</span>
                                                            <span>{question.test_cases_count}</span>
                                                        </div>
                                                        {question.topic && (
                                                            <div className="flex items-center gap-1.5 col-span-2 sm:col-span-1 pt-1.5 sm:pt-0 mt-1 sm:mt-0 border-t border-[var(--border-subtle)] sm:border-t-0">
                                                                <span className="text-[var(--text-secondary)]">Topic:</span>
                                                                <span className="truncate">{question.topic}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                {/* Action Buttons */}
                                                <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto sm:self-start">
                                                    {/* Test Button */}
                                                    <button
                                                        className="flex-1 sm:flex-none px-4 sm:px-5 py-2 sm:py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-lg hover:shadow-lg hover:shadow-purple-500/30 active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-semibold whitespace-nowrap"
                                                        onClick={() => handleTestQuestion(question.id)}
                                                        disabled={testingQuestionId === question.id}
                                                    >
                                                        {testingQuestionId === question.id ? (
                                                            <>
                                                                <svg className="animate-spin h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                                </svg>
                                                                <span className="hidden sm:inline">Creating...</span>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <FaPlay className="w-3 h-3" />
                                                                Test
                                                            </>
                                                        )}
                                                    </button>

                                                    {/* Actions Menu */}
                                                    <div className="relative gs-action-menu">
                                                        <button
                                                            className="p-2 sm:p-2.5 border-2 border-[var(--border-strong)] rounded-lg hover:bg-[var(--input-bg)] hover:border-blue-500/30 active:scale-95 transition-all duration-300 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                                                            onClick={() => setActionMenuOpen(actionMenuOpen === question.id ? null : question.id)}
                                                            aria-label="Actions"
                                                            tabIndex={0}
                                                        >
                                                            <FaEllipsisV className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                                                        </button>
                                                        {actionMenuOpen === question.id && (
                                                            <div className="absolute right-0 mt-2 z-50 w-32 sm:w-36 bg-[var(--card-strong-bg)] border-2 border-[var(--border-strong)] rounded-xl shadow-2xl py-1.5 flex flex-col text-sm animate-fade-in">
                                                                <button
                                                                    className="flex items-center gap-2.5 px-4 py-2.5 hover:bg-blue-500/10 text-blue-400 transition-colors duration-200 font-medium"
                                                                    onClick={() => {
                                                                        setActionMenuOpen(null);
                                                                        handleEdit(question);
                                                                    }}
                                                                >
                                                                    <FaEdit className="w-4 h-4" /> Edit
                                                                </button>
                                                                <button
                                                                    className="flex items-center gap-2.5 px-4 py-2.5 text-red-500 hover:bg-red-500/10 transition-colors duration-200 font-medium"
                                                                    onClick={() => {
                                                                        setActionMenuOpen(null);
                                                                        handleDelete(question.id);
                                                                    }}
                                                                >
                                                                    <FaTrash className="w-4 h-4" /> Delete
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 sm:py-12 text-muted">
                                        <p className="text-sm sm:text-base mb-3 sm:mb-4">No questions found. Create your first question!</p>
                                        <button
                                            onClick={handleAddClick}
                                            className="inline-block bg-blue-600 text-white px-4 sm:px-6 py-2 rounded-lg hover:bg-blue-700 transition text-sm sm:text-base font-medium"
                                        >
                                            Create Question
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Add / Edit Question Modal */}
            {showModal && (
                <AddQuestionModal
                    onCancel={() => setShowModal(false)}
                    questionId={editingQuestionId}
                    isEdit={isEditMode}
                    onSuccess={handleModalSuccess}
                />
            )}
        </div>
    );
};

export default Questions;

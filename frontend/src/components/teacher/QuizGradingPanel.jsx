import React, { useEffect, useState } from 'react';
import { useQuizGradingStore } from '../../store/quizGradeStore';
import useRegradingStore from '../../store/quizRegradeStore';
import { FaArrowLeft, FaUser, FaListOl, FaCheckCircle, FaCalendar, FaChevronLeft, FaEllipsisV, FaBook, FaLayerGroup } from 'react-icons/fa';


const QuizGradingPanel = ({ quiz, course, onBack }) => {
    const {
        quizUsersData,
        userAttemptsData,
        attemptGradingData,
        loading,
        error,
        loadQuizUsers,
        loadUserAttempts,
        loadAttemptGrading,
        clearQuiz,
        clearUserAttempts,
        clearAttemptGrading,
        submitGrades,
    } = useQuizGradingStore();

    const {
        regradeByQuiz,
        regradeByUser,
        regradeByQuestion,
        loading: regradeLoading,
        error: regradeError,
        result: regradeResult,
        reset: resetRegrade
    } = useRegradingStore();

    const [selectedUser, setSelectedUser] = useState(null);
    const [selectedAttempt, setSelectedAttempt] = useState(null);
    const [userSearchQuery, setUserSearchQuery] = useState('');
    const [openMenuQuestionId, setOpenMenuQuestionId] = useState(null);
    const [editedMarks, setEditedMarks] = useState({}); // { [answerId]: value }

    // Load users on mount
    useEffect(() => {
        loadQuizUsers(quiz.id, course.course_id);
        clearUserAttempts();
        clearAttemptGrading();
        setSelectedUser(null);
        setSelectedAttempt(null);
    }, [quiz, course]);

    // Load attempts when user is selected
    useEffect(() => {
        if (selectedUser) {
            loadUserAttempts(quiz.id, selectedUser.id, course.course_id);
            clearAttemptGrading();
            setSelectedAttempt(null);
        }
    }, [selectedUser]);

    // Load attempt grading when attempt is selected
    useEffect(() => {
        if (selectedAttempt) {
            loadAttemptGrading(quiz.id, selectedUser.id, selectedAttempt.attempt_number, course.course_id);
        }
    }, [selectedAttempt]);

    useEffect(() => {
        // Reset editedMarks when attemptGradingData changes
        if (attemptGradingData && attemptGradingData.papers) {
            const newEditedMarks = {};
            attemptGradingData.papers.forEach(paper => {
                (paper.questions || []).forEach(q => {
                    if (q.answer?.id !== undefined) {
                        newEditedMarks[q.answer.id] = q.answer.marks ?? 0;
                    }
                });
            });
            setEditedMarks(newEditedMarks);
        }
    }, [attemptGradingData]);

    // Filter users based on search
    const filteredUsers = (quizUsersData?.users || []).filter(user => {
        const fullName = `${user.first_name} ${user.last_name}`.toLowerCase();
        const username = (user.username || '').toLowerCase();
        const email = (user.email || '').toLowerCase();
        const search = userSearchQuery.toLowerCase();
        return fullName.includes(search) || username.includes(search) || email.includes(search);
    });


    const handleMenuClick = (questionId, e) => {
        e.stopPropagation();
        setOpenMenuQuestionId(openMenuQuestionId === questionId ? null : questionId);
    };

    const [regradeInProgress, setRegradeInProgress] = useState(false);

    const handleRegrade = async (question, paper) => {
        setOpenMenuQuestionId(null);
        if (!selectedUser || !selectedAttempt || !paper) return;
        setRegradeInProgress(true);
        try {
            await regradeByQuestion(
                course.course_id,
                paper.question_paper_id || quiz.id,
                paper.id,
                question.id
            );
            await loadAttemptGrading(quiz.id, selectedUser.id, selectedAttempt.attempt_number, course.course_id);
            alert(`Regrade requested for question ID: ${question.id}`);
        } catch (e) {
            alert("Failed to regrade question: " + (e?.message || "Unknown error"));
        } finally {
            setRegradeInProgress(false);
        }
    };

    const handleRegradeAll = async () => {
        if (!selectedUser || !selectedAttempt || !attemptGradingData?.papers?.[0]) return;
        setRegradeInProgress(true);
        const paper = attemptGradingData.papers[0];
        try {
            await regradeByUser(
                course.course_id,
                paper.question_paper_id || quiz.id,
                paper.id
            );
            await loadAttemptGrading(quiz.id, selectedUser.id, selectedAttempt.attempt_number, course.course_id);
            alert("Regrade requested for all questions in this attempt.");
        } catch (e) {
            alert("Failed to regrade all: " + (e?.message || "Unknown error"));
        } finally {
            setRegradeInProgress(false);
        }
    };

    const handleSaveGrades = async () => {
        if (!selectedUser || !selectedAttempt) return;
        // Collect grades for all questions in this attempt
        const grades = [];
        (attemptGradingData?.papers || []).forEach(paper => {
            (paper.questions || []).forEach(q => {
                grades.push({
                    question_id: q.question.id,
                    marks: parseFloat(editedMarks[q.answer?.id] ?? q.answer?.marks ?? 0)
                });
            });
        });
        try {
            await submitGrades(
                quiz.id,
                selectedUser.id,
                selectedAttempt.attempt_number,
                course.course_id,
                { grades }
            );
            alert("Grades saved successfully.");
        } catch (e) {
            alert(
                e?.response?.data?.error ||
                e?.message ||
                "Failed to save grades. Please try again."
            );
        }
    };




    return (
        <div className="space-y-4">
            {/* Main Card */}
            <div className="card-strong p-5 sm:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                {/* Header Section */}
                <div className="mb-6 pb-5 border-b-2 border-[var(--border-subtle)]">
                    <div className="flex items-start gap-4 mb-4">
                        <button
                            onClick={onBack}
                            className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
                        >
                            <FaChevronLeft className="w-4 h-4" />
                        </button>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 ">
                                <h2 className="text-lg sm:text-xl font-bold mb-1">{quiz.description || quiz.name}</h2>
                                <span className={`text-[10px] px-2.5 py-1 rounded-lg border-2 uppercase font-bold tracking-wider whitespace-nowrap ${quiz.is_exercise
                                    ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                                    : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                                    }`}>
                                    {quiz.is_exercise ? 'Exercise' : 'Quiz'}
                                </span>
                            </div>
                            <div className="flex flex-wrap gap-4 text-xs sm:text-sm muted">
                                <div className="flex items-center gap-1.5">
                                    <FaBook className="w-3 h-3" />
                                    <span className="font-medium">{course.course_name}</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <FaLayerGroup className="w-3 h-3" />
                                    <span className="font-medium">{quiz.module_name}</span>
                                </div>

                                {quiz.start_date && (
                                    <div className="flex items-center gap-1.5">
                                        <FaCalendar className="w-3 h-3" />
                                        <span>{new Date(quiz.start_date).toLocaleDateString()}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                    <p className="text-sm muted">Select a user and their attempt to view and grade submissions</p>
                </div>

                {/* Filters Section */}
                <div className="mb-6">
                    <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3 sm:gap-4">
                        {/* Selected User Details (left, 1/3 width) */}
                        <div className="w-full md:w-1/3 lg:w-1/3">
                            {selectedUser ? (
                                <div className="card p-4 rounded-xl border-2 border-blue-500/30 flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center border-2 border-blue-500/30">
                                        <FaUser className="w-6 h-6 text-blue-500" />
                                    </div>
                                    <div>
                                        <p className="font-bold text-base text-blue-600 dark:text-blue-400 mb-1">
                                            {selectedUser.first_name} {selectedUser.last_name}
                                        </p>
                                        <p className="text-xs text-[var(--text-muted)]">{selectedUser.username} . {selectedUser.email}</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="card p-4 rounded-xl border-2 border-[var(--border-color)] flex items-center gap-4 opacity-60">
                                    <div className="w-12 h-12 rounded-xl bg-[var(--input-bg)] flex items-center justify-center border-2 border-[var(--border-color)]">
                                        <FaUser className="w-6 h-6 text-[var(--text-muted)]" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-base text-[var(--text-muted)] mb-1">No user selected</p>
                                        <p className="text-xs text-[var(--text-muted)]">Select a user to view details</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* User Dropdown (right, 1/3 width) */}
                        <div className="w-full md:w-1/3 lg:w-1/3 ml-auto">
                            <label
                                className="block text-xs font-semibold text-muted mb-1 tracking-wide"
                                htmlFor="user-select"
                            >
                                Select User
                            </label>
                            <div className="relative">
                                <select
                                    id="user-select"
                                    value={selectedUser ? selectedUser.id : ''}
                                    onChange={e => {
                                        const userId = e.target.value;
                                        const user = (quizUsersData?.users || []).find(u => String(u.id) === userId);
                                        setSelectedUser(user || null);
                                        setSelectedAttempt(null);
                                    }}
                                    className="w-full pl-4 pr-10 py-2 bg-[var(--input-bg)] border-2 border-[var(--border-strong)] rounded-xl text-sm font-medium text-[var(--text-primary)] focus:outline-none focus:border-blue-500/50 transition-colors appearance-none"
                                >
                                    <option value="">All Users ({quizUsersData?.users?.length || 0})</option>
                                    {(quizUsersData?.users || []).map(user => (
                                        <option key={user.id} value={user.id}>
                                            {user.first_name} {user.last_name} ({user.username || user.email})
                                        </option>
                                    ))}
                                </select>
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-blue-600 dark:text-blue-400">
                                    <FaUser className="w-4 h-4" />
                                </span>
                            </div>
                        </div>
                    </div>
                    {/* Attempt Filter (only show when user is selected) */}
                    {selectedUser && userAttemptsData && (
                        <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 sm:gap-4 my-6">
                            <div className="flex bg-[var(--input-bg)] p-1.5 rounded-xl overflow-x-auto scrollbar-hide border-2 border-[var(--border-strong)] max-w-full lg:max-w-[50vw] xl:max-w-[75vw]">
                                {[...userAttemptsData.attempts]
                                    .sort((a, b) => a.attempt_number - b.attempt_number)
                                    .map((attempt) => (
                                        <button
                                            key={attempt.id}
                                            onClick={() => setSelectedAttempt(attempt)}
                                            className={`flex-1 sm:flex-none flex-shrink-0 px-4 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 whitespace-nowrap ${selectedAttempt?.id === attempt.id
                                                ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                                                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--card-bg)]'
                                                }`}
                                        >
                                            Attempt {attempt.attempt_number}
                                        </button>
                                    ))}
                            </div>
                        </div>
                    )}
                </div>
                {/* Content Area */}
                <div className="space-y-4">
                    {/* Loading State */}
                    {(loading.quizUsers || loading.userAttempts || loading.attemptGrading) && (
                        <div className="flex items-center justify-center py-12">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                <p className="text-sm text-muted">
                                    {loading.quizUsers ? 'Loading users...' :
                                        loading.userAttempts ? 'Loading attempts...' :
                                            'Loading attempt details...'}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {(error.quizUsers || error.userAttempts || error.attemptGrading) && (
                        <div className="bg-red-500/10 border-2 border-red-500/40 rounded-xl p-4 text-red-600 dark:text-red-400 font-semibold">
                            {error.quizUsers || error.userAttempts || error.attemptGrading}
                        </div>
                    )}



                    {/* Attempt Details/Grading */}
                    {selectedUser && selectedAttempt && !loading.attemptGrading && !error.attemptGrading && attemptGradingData && (
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-base font-bold flex items-center gap-2">
                                    <FaCheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                                    Grading Details
                                </h3>
                                <div className="flex items-center gap-2">
                                    <button
                                        className="text-white px-3 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold bg-green-500/80 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap flex-shrink-0 hover:bg-green-600 transition"
                                        onClick={handleSaveGrades}
                                        disabled={loading.submittingGrades}
                                    >
                                        {loading.submittingGrades ? "Saving..." : "Save"}
                                    </button>
                                    <button
                                        className="text-white px-3 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold bg-blue-500/80 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap flex-shrink-0 hover:bg-blue-600 transition"
                                        onClick={handleRegradeAll}
                                        disabled={loading.submittingGrades}
                                    >
                                        Regrade All
                                    </button>
                                </div>
                            </div>
                            <p className="text-sm text-blue-600 dark:text-blue-400 mb-4 font-medium">
                                <strong className="font-bold">Note:</strong> Only answered questions can be marked. Unanswered questions cannot be externally graded.
                            </p>
                            <div className="space-y-4">
                                {(attemptGradingData?.papers || []).map(paper => (
                                    <div key={paper.id} className="card-strong p-5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--surface)]">
                                        <div className="flex items-center justify-between mb-4 pb-4 border-b-2 border-[var(--border-subtle)]">
                                            <div>
                                                <h4 className="font-bold text-lg text-emerald-600 dark:text-emerald-400">Paper #{paper.id}</h4>
                                                <p className="text-sm text-[var(--text-muted)] mt-1 font-medium">Status: <span className="font-semibold text-[var(--text-primary)]">{paper.status}</span></p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-base font-bold">
                                                    <span className="text-emerald-600 dark:text-emerald-400">{paper.marks_obtained || 0}</span>
                                                    <span className="text-[var(--text-muted)]"> / {paper.total_marks || 0}</span>
                                                </p>
                                                <p className="text-sm text-[var(--text-muted)] mt-1 font-semibold">{paper.percent || 0}%</p>
                                            </div>
                                        </div>
                                        <div className="space-y-3">
                                            {(paper.questions || []).map((q, idx) => {
                                                const { question } = q;
                                                const type = (question.type || "").toLowerCase();
                                                let correctDisplay = <span className="text-[var(--text-muted)]">N/A</span>;

                                                if (type === "mcq" || type === "mcc") {
                                                    // MCQ: show correct options
                                                    const correctOptions = (question.test_cases || [])
                                                        .filter(tc => tc.correct)
                                                        .map(tc => tc.options)
                                                        .filter(Boolean);
                                                    if (correctOptions.length > 0) {
                                                        correctDisplay = (
                                                            <ul className="list-disc ml-4">
                                                                {correctOptions.map((opt, i) => (
                                                                    <li key={i} className="text-emerald-600 dark:text-emerald-400 font-medium">{opt}</li>
                                                                ))}
                                                            </ul>
                                                        );
                                                    } else if (!question.test_cases || question.test_cases.length === 0) {
                                                        correctDisplay = <span className="text-[var(--text-muted)]">No choices provided</span>;
                                                    }
                                                } else if (type === "arrange" || type === "arrangetestcase") {
                                                    // Arrange: show correct order
                                                    const arrangeOrder = (question.test_cases || [])
                                                        .map(tc => tc.options)
                                                        .filter(Boolean);
                                                    if (arrangeOrder.length > 0) {
                                                        correctDisplay = (
                                                            <ol className="list-decimal ml-4">
                                                                {arrangeOrder.map((step, i) => (
                                                                    <li key={i} className="text-emerald-600 dark:text-emerald-400 font-medium">{step}</li>
                                                                ))}
                                                            </ol>
                                                        );
                                                    }
                                                } else if (type === "stdiobasedtestcase" || (question.test_cases && question.test_cases.some(tc => tc.expected_input))) {
                                                    // StdIO: show expected input/output
                                                    const stdioCases = (question.test_cases || [])
                                                        .filter(tc => tc.expected_input !== undefined && tc.expected_output !== undefined)
                                                        .map(tc => `Input: ${tc.expected_input}, Output: ${tc.expected_output}`);
                                                    if (stdioCases.length > 0) {
                                                        correctDisplay = (
                                                            <ul className="list-disc ml-4">
                                                                {stdioCases.map((desc, i) => (
                                                                    <li key={i} className="text-emerald-600 dark:text-emerald-400 font-medium">{desc}</li>
                                                                ))}
                                                            </ul>
                                                        );
                                                    }
                                                }
                                                // Show hook code if present (for code/upload/hooktestcase)
                                                if (question.test_cases && question.test_cases.some(tc => tc.hook_code)) {
                                                    const hookCodes = question.test_cases
                                                        .map(tc => tc.hook_code)
                                                        .filter(Boolean);
                                                    if (hookCodes.length > 0) {
                                                        correctDisplay = (
                                                            <pre className="bg-[var(--input-bg)] text-emerald-600 dark:text-emerald-400 p-3 rounded-lg border-2 border-[var(--border-strong)] font-mono text-xs">{hookCodes.join('\n\n')}</pre>
                                                        );
                                                    }
                                                }
                                                // Show code test_case if present
                                                if ((type === "code" || type === "standardtestcase" || type === "program") && question.test_cases) {
                                                    const testCaseDescriptions = question.test_cases
                                                        .map(tc => tc.test_case)
                                                        .filter(Boolean);
                                                    if (testCaseDescriptions.length > 0) {
                                                        correctDisplay = (
                                                            <ul className="list-disc ml-4">
                                                                {testCaseDescriptions.map((desc, i) => (
                                                                    <li key={i} className="text-emerald-600 dark:text-emerald-400 font-medium">
                                                                        <span dangerouslySetInnerHTML={{ __html: desc }} />
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        );
                                                    }
                                                }
                                                // Default: show correct values
                                                if (!correctDisplay || correctDisplay.props?.children === "N/A") {
                                                    const correctAnswers = (question.test_cases || [])
                                                        .map(tc => tc.correct)
                                                        .filter(ans => ans !== undefined && ans !== null);
                                                    if (correctAnswers.length > 0) {
                                                        correctDisplay = correctAnswers.join(', ');
                                                    }
                                                }

                                                return (
                                                    <div key={question.id} className="card p-4 sm:p-5  border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group bg-[var(--surface-2)] hover:shadow-md hover:shadow-md hover:bg-white/[0.03] rounded-xl">
                                                        <div className="flex items-start justify-between mb-2">
                                                            <div className="flex-1">
                                                                <div className="font-semibold text-blue-600 dark:text-blue-400 mb-3 flex items-start gap-2">
                                                                    <span className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-500/20 border-2 border-blue-500/30 flex items-center justify-center text-sm font-bold text-blue-600 dark:text-blue-400">
                                                                        {idx + 1}
                                                                    </span>
                                                                    <span dangerouslySetInnerHTML={{ __html: question.summary }} />
                                                                </div>
                                                            </div>
                                                            {/* Three dot menu button */}
                                                            <div className="relative">
                                                                <button
                                                                    onClick={e => handleMenuClick(question.id, e)}
                                                                    className="p-2 rounded-lg hover:bg-[var(--input-bg)] border-2 border-[var(--border-color)] hover:border-blue-500/40 transition-all"
                                                                    aria-label="Question Actions"
                                                                >
                                                                    <FaEllipsisV className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                                                </button>
                                                                {openMenuQuestionId === question.id && (
                                                                    <div className="absolute right-0 mt-2 z-50 w-36 bg-[var(--card-strong-bg)] border-2 border-[var(--border-strong)] rounded-xl shadow-2xl py-1.5 animate-fadeIn">
                                                                        <button
                                                                            onClick={() => handleRegrade(question, paper)}
                                                                            className="w-full text-left px-4 py-2.5 text-sm font-semibold hover:bg-blue-500/10 transition-colors text-blue-600 dark:text-blue-400"
                                                                        >
                                                                            Regrade
                                                                        </button>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <div className="text-sm text-[var(--text-secondary)] mb-3 ml-8" dangerouslySetInnerHTML={{ __html: question.description }} />

                                                        <div className="ml-9 space-y-3 text-sm">
                                                            <div className="flex items-start gap-2">
                                                                <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Answer:</span>
                                                                <span className={q.answer?.answer_content ? 'text-[var(--text-primary)] font-medium' : 'text-red-600 dark:text-red-400 font-semibold'}>
                                                                    {q.answer?.answer_content || 'Not answered'}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-start gap-2">
                                                                <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Correct:</span>
                                                                <span className="text-emerald-600 dark:text-emerald-400 font-medium">{correctDisplay}</span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Marks:</span>
                                                                <span>
                                                                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">{q.answer?.marks ?? 0}</span>
                                                                    <span className="text-[var(--text-muted)] font-semibold"> / {question.points}</span>
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-2 justify-between">
                                                                <div className="flex items-center gap-2">
                                                                    <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Status:</span>
                                                                    {q.answer?.correct ? (
                                                                        <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 font-semibold">
                                                                            <FaCheckCircle className="w-3.5 h-3.5" /> Correct
                                                                        </span>
                                                                    ) : q.answer?.skipped ? (
                                                                        <span className="text-yellow-600 dark:text-yellow-400 font-semibold">Skipped</span>
                                                                    ) : (
                                                                        <span className="text-red-600 dark:text-red-400 font-semibold">Incorrect</span>
                                                                    )}
                                                                </div>
                                                                {/* Marks input field */}
                                                                {q.answer?.answer_content && (
                                                                    <div className="hidden lg:flex items-center gap-2 ">
                                                                        <span className="font-bold text-[var(--text-muted)]">Marks:</span>
                                                                        <input
                                                                            type="number"
                                                                            min="0"
                                                                            step="0.1"
                                                                            className="w-24 px-3 py-1.5 rounded-lg bg-[var(--input-bg)] border-2 border-[var(--border-strong)] text-emerald-600 dark:text-emerald-400 font-bold focus:outline-none focus:border-blue-500/50 transition"
                                                                            value={editedMarks[q.answer?.id] ?? q.answer?.marks ?? 0}
                                                                            onChange={e => setEditedMarks(m => ({ ...m, [q.answer?.id]: e.target.value }))}
                                                                        />
                                                                        <span className="text-[var(--text-muted)] font-semibold">/ {question.points}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                            {q.answer?.answer_content && (
                                                                <div className="lg:hidden lg:flex items-center gap-2 ">
                                                                    <span className="font-bold text-[var(--text-muted)]">Marks:</span>
                                                                    <input
                                                                        type="number"
                                                                        min="0"

                                                                        className="w-16 ml-7 px-2 py-1.5 rounded-lg bg-[var(--input-bg)] border-2 border-[var(--border-strong)] text-emerald-600 dark:text-emerald-400 font-bold focus:outline-none focus:border-blue-500/50 transition"
                                                                        value={editedMarks[q.answer?.id] ?? q.answer?.marks ?? 0}
                                                                        onChange={e => setEditedMarks(m => ({ ...m, [q.answer?.id]: e.target.value }))}
                                                                    />
                                                                    <span className="text-[var(--text-muted)] font-semibold">/ {question.points}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
                .scrollbar-hide {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }

                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }

                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }

                .animate-fadeIn {
                    animation: fadeIn 0.2s ease-out;
                }

            `}</style>
        </div>
    );
};

export default QuizGradingPanel;
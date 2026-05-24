import React, { useState, useEffect, useRef } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { FaClock, FaCheck, FaTimes, FaCode, FaPlay, FaDownload, FaArrowLeft, FaLightbulb, FaFileAlt, FaCheckCircle, FaExternalLinkAlt, FaChevronLeft, FaFileCode, FaUpload } from 'react-icons/fa';
import { TbSum } from "react-icons/tb";
import { FaPersonCircleQuestion } from "react-icons/fa6";
import { CgArrangeFront } from "react-icons/cg";
import { BiSolidSelectMultiple } from "react-icons/bi";
import { MdOutlineFormatColorText } from "react-icons/md";
import { TbCircleDashedNumber1 } from "react-icons/tb";
import { TbDecimal } from "react-icons/tb";
import { AiOutlineWarning } from 'react-icons/ai';
import { BiSkipNext } from 'react-icons/bi';
import { MdTimer } from 'react-icons/md';
import useQuizStore from '../../store/quiz_QuestionStore';
import { useAuthStore } from '../../store/authStore';
import TeacherSidebar from '../../components/layout/TeacherSidebar';
import QuestionActionButtons from '../../components/teacher/QuestionActionButtons';
import Header from '../../components/layout/Header';

const TestQuestion = () => {
    const { questionpaperId, moduleId, courseId } = useParams();
    const navigate = useNavigate();
    const { user } = useAuthStore();

    const {
        currentQuestion,
        paper,
        loading,
        error,
        answerResult,
        timeLeft,
        attemptNum,
        startQuiz,
        submitAnswer,
        skipQuestion,
        completeQuiz,
        quitQuiz,
        updateTimeLeft,
        clearError,
        resetQuiz
    } = useQuizStore();

    const [userAnswer, setUserAnswer] = useState('');
    const [showResult, setShowResult] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const timerIntervalRef = useRef(null);
    const initializingRef = useRef(false);

    // Initialize quiz on mount - only once
    useEffect(() => {
        let cancelled = false;

        const init = async () => {
            if (cancelled || initializingRef.current) {
                return;
            }

            if (questionpaperId && moduleId && courseId) {
                initializingRef.current = true;
                clearError();

                try {
                    console.log('Starting test quiz with params:', { questionpaperId, moduleId, courseId });
                    const quizData = await startQuiz(questionpaperId, moduleId, courseId, null);
                    console.log('Quiz started:', quizData);
                } catch (err) {
                    console.error('Failed to initialize test quiz:', err);
                    if (!cancelled) {
                        initializingRef.current = false;
                    }
                }
            }
        };

        init();

        return () => {
            cancelled = true;
        };
    }, [questionpaperId, moduleId, courseId, startQuiz, clearError]);

    // Initialize answer when currentQuestion changes
    useEffect(() => {
        if (currentQuestion) {
            if (currentQuestion.type === 'code' && currentQuestion.snippet) {
                setUserAnswer(currentQuestion.snippet);
            } else if (currentQuestion.type === 'mcc') {
                setUserAnswer([]);
            } else {
                setUserAnswer('');
            }
        }
    }, [currentQuestion]);

    // Timer effect
    useEffect(() => {
        if (timeLeft > 0) {
            timerIntervalRef.current = setInterval(() => {
                updateTimeLeft(timeLeft - 1);
                if (timeLeft <= 1) {
                    handleAutoComplete();
                }
            }, 1000);

            return () => {
                if (timerIntervalRef.current) {
                    clearInterval(timerIntervalRef.current);
                }
            };
        }
    }, [timeLeft, updateTimeLeft]);

    const handleAutoComplete = async () => {
        try {
            await completeQuiz();
            resetQuiz();
            navigate('/teacher/questions');
        } catch (err) {
            console.error('Auto-complete failed:', err);
        }
    };

    const formatTime = (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    };

    const getTimerStatus = () => {
        if (timeLeft < 300) return { color: 'red', bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-400', animate: true };
        if (timeLeft < 600) return { color: 'orange', bg: 'bg-orange-500/10', border: 'border-orange-500/40', text: 'text-orange-400', animate: false };
        return { color: 'cyan', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', text: 'text-cyan-400', animate: false };
    };

    const handleAnswerChange = (value) => {
        setUserAnswer(value);
        setShowResult(false);
    };

    const formatAnswerData = (questionType, answer) => {
        switch (questionType?.toLowerCase()) {
            case 'code':
                return { answer: answer };
            case 'mcq':
                return { answer: answer };
            case 'mcc':
                return { answer: Array.isArray(answer) ? answer : [answer] };
            case 'integer':
                return { answer: parseInt(answer) };
            case 'float':
                return { answer: parseFloat(answer) };
            case 'string':
            default:
                return { answer: answer };
        }
    };

    const handleSubmitAnswer = async () => {
        if (!currentQuestion) return;

        if (!userAnswer || (Array.isArray(userAnswer) && userAnswer.length === 0)) {
            alert('Please provide an answer before submitting.');
            return;
        }

        setSubmitting(true);
        setShowResult(false);

        try {
            const answerData = formatAnswerData(currentQuestion.type, userAnswer);
            console.log('Submitting answer:', answerData);

            const result = await submitAnswer(currentQuestion.id, answerData);
            console.log('Submit result:', result);

            setShowResult(true);

            // Reset answer for next question if there is one
            const nextQ = result.next_question || result.current_question;
            if (nextQ) {
                if (nextQ.type === 'code' && nextQ.snippet) {
                    setUserAnswer(nextQ.snippet);
                } else if (nextQ.type === 'mcc') {
                    setUserAnswer([]);
                } else {
                    setUserAnswer('');
                }
            }
        } catch (err) {
            console.error('Failed to submit answer:', err);
            alert(err.message || 'Failed to submit answer');
        } finally {
            setSubmitting(false);
        }
    };



    const handleCompleteTest = async () => {
        if (window.confirm('Are you sure you want to complete this test?')) {
            try {
                await completeQuiz();
                alert('Test completed successfully!');
                resetQuiz();
                navigate('/teacher/questions');
            } catch (err) {
                console.error('Failed to complete test:', err);
                alert(err.message || 'Failed to complete test');
            }
        }
    };

    const handleQuitTest = async () => {
        if (window.confirm('Are you sure you want to quit this test? Your progress will be saved.')) {
            try {
                await quitQuiz('User quit test');
                resetQuiz();
                navigate('/teacher/questions');
            } catch (err) {
                console.error('Failed to quit test:', err);
                alert(err.message || 'Failed to quit test');
            }
        }
    };


    // Extract options from test_cases for MCQ/MCC/arrage questions
    const getQuestionOptions = () => {
        if (!currentQuestion || !currentQuestion.test_cases) return [];

        const questionType = currentQuestion.type?.toLowerCase();

        if (questionType === 'mcq' || questionType === 'mcc') {
            return currentQuestion.test_cases.map(tc => {
                // Handle if options is a JSON string
                try {
                    return typeof tc.options === 'string' ? JSON.parse(tc.options) : tc.options;
                } catch {
                    return tc.options;
                }
            }).flat();
        }


        if (questionType === 'arrange') {
            return currentQuestion.test_cases.map(tc => tc.options).flat();
        }

        return [];
    };

    const [draggableOptions, setDraggableOptions] = useState([]);
    const [draggedIndex, setDraggedIndex] = useState(null);
     const [initialShuffledOptions, setInitialShuffledOptions] = useState([]);

    //  useEffect for arrange type initialization
    useEffect(() => {
        if (currentQuestion?.type === 'arrange') {
            const options = getQuestionOptions();
            
            if (!userAnswer || userAnswer === '') {
                // SHUFFLE INITIALIZATION
                const shuffledIndices = options.map((_, idx) => idx);
                shuffledIndices.sort(() => Math.random() - 0.5); // Random sort
                
                const shuffledOptions = shuffledIndices.map(idx => options[idx]);
                setDraggableOptions(shuffledOptions);
                setInitialShuffledOptions(shuffledOptions); // <-- ADD THIS
                
                // Set the initial answer to the shuffled state's original indices + 1 (1-based)
                const initialOrder = shuffledIndices.map(idx => idx + 1).join(',');
                setUserAnswer(initialOrder);
            } else {
                // If userAnswer exists, reconstruct draggableOptions from it
                const indices = userAnswer.split(',').map(n => parseInt(n.trim()) - 1);
                if (indices.length === options.length &&
                    indices.every(idx => !isNaN(idx) && idx >= 0 && idx < options.length)) {
                    const reordered = indices.map(idx => options[idx]);
                    if (reordered.every(item => item !== undefined)) {
                        setDraggableOptions(reordered);
                        setInitialShuffledOptions(reordered); // <-- ADD THIS
                    }
                }
            }
        }
    }, [currentQuestion]);

    // Drag and drop handlers for arrange questions
    const handleDragStart = (e, index) => {
        setDraggedIndex(index);
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    //  handleDrop function
    const handleDrop = (e, dropIndex) => {
        e.preventDefault();

        if (draggedIndex === null || draggedIndex === dropIndex) {
            setDraggedIndex(null);
            return;
        }

        const newOptions = [...draggableOptions];
        const draggedItem = newOptions[draggedIndex];

        // Remove the dragged item
        newOptions.splice(draggedIndex, 1);

        // Insert at the drop position
        newOptions.splice(dropIndex, 0, draggedItem);

        setDraggableOptions(newOptions);
        setDraggedIndex(null);

        // Update userAnswer with the original indices of items in new order
        const originalOptions = getQuestionOptions();
        const newOrder = newOptions.map(option => {
            const originalIndex = originalOptions.findIndex(opt => opt === option);
            return originalIndex + 1; // 1-based index
        }).join(',');

        handleAnswerChange(newOrder);
    };

    const handleDragEnd = () => {
        setDraggedIndex(null);
    };




    const renderQuestionInput = () => {
        if (!currentQuestion) return null;

        const questionType = currentQuestion.type?.toLowerCase();
        const options = getQuestionOptions();

        const QuestionHeader = ({ icon, typeLabel, title, tag, colors }) => (
            <div className={`flex items-center justify-between p-4 sm:p-5 rounded-xl border-2 transition-colors ${colors.bg}`}>
                <div className="flex items-center gap-3 sm:gap-4">
                    <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center border ${colors.iconBg}`}>
                        {icon}
                    </div>
                    <div>

                        <span className={`text-sm sm:text-base font-bold ${colors.text}`}>{title}</span>
                        <span className="text-xs sm:text-sm text-[var(--text-muted)] block font-medium mb-0.5">{typeLabel}</span>
                    </div>
                </div>
                {tag && (
                    <span className={`text-xs px-3 py-1.5 rounded-lg border font-semibold tracking-wide ${colors.tag}`}>
                        {tag}
                    </span>
                )}
            </div>
        );

        switch (questionType) {
            case 'integer':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<TbCircleDashedNumber1 className="w-6 h-6 text-orange-600 dark:text-orange-400" />}
                            typeLabel="Input Type"
                            title="Whole Number (No Decimals)"
                            tag="INTEGER"
                            colors={{
                                bg: 'bg-orange-500/5 border-orange-500/20',
                                iconBg: 'bg-orange-500/10 border-orange-500/30',
                                text: 'text-orange-700 dark:text-orange-400',
                                tag: 'bg-orange-500/10 border-orange-500/20 text-orange-700 dark:text-orange-400'
                            }}
                        />
                        <div className="relative group">
                            <input
                                type="number"
                                step="1"
                                className="w-full px-5 py-4 rounded-xl text-base bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border-2 border-[var(--border-color)] focus:border-orange-500/50 focus:ring-4 focus:ring-orange-500/10 transition-all placeholder-[var(--text-muted)] text-[var(--text-primary)] font-medium"
                                placeholder="e.g., 42"
                                value={userAnswer}
                                onChange={(e) => handleAnswerChange(e.target.value)}
                            />
                        </div>
                    </div>
                );

            case 'float':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<TbDecimal className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />}
                            typeLabel="Input Type"
                            title="Decimal Number (Floating Point)"
                            tag="FLOAT"
                            colors={{
                                bg: 'bg-yellow-500/5 border-yellow-500/20',
                                iconBg: 'bg-yellow-500/10 border-yellow-500/30',
                                text: 'text-yellow-700 dark:text-yellow-400',
                                tag: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-400'
                            }}
                        />
                        <div className="relative group">
                            <input
                                type="number"
                                step="any"
                                className="w-full px-5 py-4 rounded-xl text-base bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border-2 border-[var(--border-color)] focus:border-yellow-500/50 focus:ring-4 focus:ring-yellow-500/10 transition-all placeholder-[var(--text-muted)] text-[var(--text-primary)] font-medium"
                                placeholder="e.g., 3.14159"
                                value={userAnswer}
                                onChange={(e) => handleAnswerChange(e.target.value)}
                            />
                        </div>
                    </div>
                );

            case 'string':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<MdOutlineFormatColorText className="w-6 h-6 text-green-600 dark:text-green-400" />}
                            typeLabel="Input Type"
                            title="Text Answer (Case Sensitive)"
                            tag="STRING"
                            colors={{
                                bg: 'bg-green-500/5 border-green-500/20',
                                iconBg: 'bg-green-500/10 border-green-500/30',
                                text: 'text-green-700 dark:text-green-400',
                                tag: 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400'
                            }}
                        />
                        <div className="relative group">
                            <input
                                type="text"
                                className="w-full px-5 py-4 rounded-xl text-base bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border-2 border-[var(--border-color)] focus:border-green-500/50 focus:ring-4 focus:ring-green-500/10 transition-all placeholder-[var(--text-muted)] text-[var(--text-primary)] font-medium"
                                placeholder="Type your precise answer here..."
                                value={userAnswer}
                                onChange={(e) => handleAnswerChange(e.target.value)}
                            />
                        </div>
                    </div>
                );


            case 'mcq':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<FaCheckCircle className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />}
                            typeLabel="Question Type"
                            title="Single Correct Choice"
                            tag={`${options.length} OPTIONS`}
                            colors={{
                                bg: 'bg-indigo-500/5 border-indigo-500/20',
                                iconBg: 'bg-indigo-500/10 border-indigo-500/30',
                                text: 'text-indigo-700 dark:text-indigo-400',
                                tag: 'bg-indigo-500/10 border-indigo-500/20 text-indigo-700 dark:text-indigo-400'
                            }}
                        />
                        <div className="grid grid-cols-1 gap-3">
                            {options.map((option, idx) => {
                                const isSelected = userAnswer === option;
                                return (
                                    <label
                                        key={idx}
                                        className={`group flex items-center gap-4 p-4 sm:p-5 rounded-xl cursor-pointer transition-all duration-300 ${isSelected
                                            ? 'bg-indigo-500/10 border-2 border-indigo-500/50 shadow-sm shadow-indigo-500/10'
                                            : 'bg-[var(--input-bg)] border-2 border-[var(--border-color)] hover:bg-[var(--surface-2)] hover:border-indigo-500/30'
                                            }`}
                                    >
                                        <div className="relative flex-shrink-0">
                                            <input
                                                type="radio"
                                                name={`question-${currentQuestion.id}`}
                                                value={option}
                                                checked={isSelected}
                                                onChange={(e) => handleAnswerChange(e.target.value)}
                                                className="peer sr-only"
                                            />
                                            <div className={`w-5 h-5 sm:w-6 sm:h-6 rounded-full border-2 transition-all duration-300 ${isSelected
                                                ? 'border-indigo-500 bg-indigo-500'
                                                : 'border-[var(--text-muted)] group-hover:border-indigo-400'
                                                }`}>
                                                {isSelected && (
                                                    <div className="w-full h-full rounded-full flex items-center justify-center">
                                                        <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 bg-white rounded-full"></div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex-1 flex items-center justify-between gap-3 min-w-0">
                                            <span className={`text-sm sm:text-base leading-relaxed ${isSelected ? 'text-[var(--text-primary)] font-semibold' : 'text-[var(--text-secondary)] font-medium group-hover:text-[var(--text-primary)]'
                                                }`}>
                                                {option}
                                            </span>
                                        </div>
                                    </label>
                                );
                            })}
                        </div>
                    </div>
                );

            case 'mcc':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<BiSolidSelectMultiple className="w-6 h-6 text-blue-600 dark:text-blue-400" />}
                            typeLabel="Question Type"
                            title="Multiple Correct Choices"
                            tag={`${(Array.isArray(userAnswer) ? userAnswer : []).length}/${options.length} SELECTED`}
                            colors={{
                                bg: 'bg-blue-500/5 border-blue-500/20',
                                iconBg: 'bg-blue-500/10 border-blue-500/30',
                                text: 'text-blue-700 dark:text-blue-400',
                                tag: 'bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-400'
                            }}
                        />
                        <div className="grid grid-cols-1 gap-3">
                            {options.map((option, idx) => {
                                const isChecked = (Array.isArray(userAnswer) ? userAnswer : []).includes(option);
                                return (
                                    <label
                                        key={idx}
                                        className={`group flex items-center gap-4 p-4 sm:p-5 rounded-xl cursor-pointer transition-all duration-300 ${isChecked
                                            ? 'bg-blue-500/10 border-2 border-blue-500/50 shadow-sm shadow-blue-500/10'
                                            : 'bg-[var(--input-bg)] border-2 border-[var(--border-color)] hover:bg-[var(--surface-2)] hover:border-blue-500/30'
                                            }`}
                                    >
                                        <div className="relative flex-shrink-0">
                                            <input
                                                type="checkbox"
                                                checked={isChecked}
                                                onChange={(e) => {
                                                    const current = Array.isArray(userAnswer) ? userAnswer : [];
                                                    const updated = e.target.checked
                                                        ? [...current, option]
                                                        : current.filter((o) => o !== option);
                                                    handleAnswerChange(updated);
                                                }}
                                                className="peer sr-only"
                                            />
                                            <div className={`w-5 h-5 sm:w-6 sm:h-6 rounded border-2 transition-all duration-300 ${isChecked
                                                ? 'border-blue-500 bg-blue-500'
                                                : 'border-[var(--text-muted)] group-hover:border-blue-400'
                                                }`}>
                                                {isChecked && (
                                                    <svg className="w-full h-full text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                                                    </svg>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex-1 flex items-center justify-between gap-3 min-w-0">
                                            <span className={`text-sm sm:text-base leading-relaxed ${isChecked ? 'text-[var(--text-primary)] font-semibold' : 'text-[var(--text-secondary)] font-medium group-hover:text-[var(--text-primary)]'
                                                }`}>
                                                {option}
                                            </span>
                                        </div>
                                    </label>
                                );
                            })}
                        </div>
                    </div>
                );

            case 'arrange':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<CgArrangeFront className="w-6 h-6 text-red-600 dark:text-red-400" />}
                            typeLabel="Question Type"
                            title="Arrange in Correct Order"
                            tag={`${draggableOptions.length} ITEMS`}
                            colors={{
                                bg: 'bg-red-500/5 border-red-500/20',
                                iconBg: 'bg-red-500/10 border-red-500/30',
                                text: 'text-red-700 dark:text-red-400',
                                tag: 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400'
                            }}
                        />
                        <div className="flex items-start gap-3 p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl">
                            <FaLightbulb className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-[var(--text-secondary)]">
                                Drag items to reorder them. The order will be automatically saved representing the original position of each item.
                            </p>
                        </div>
                        <div className="space-y-2.5">
                            {draggableOptions.map((option, idx) => {
                                // Find where it was on the FRONTEND originally, ignoring the backend
                                const originalFrontendIndex = initialShuffledOptions.findIndex(opt => opt === option);

                                return (
                                    <div
                                        key={`${originalFrontendIndex}-${idx}`}
                                        className={`group flex items-center gap-4 p-4 rounded-xl bg-[var(--surface-2)] border-2 transition-all cursor-move shadow-sm ${draggedIndex === idx
                                            ? 'border-red-400 opacity-60 scale-[0.98]'
                                            : 'border-[var(--border-color)] hover:border-red-500/40 hover:shadow-md'
                                            }`}
                                        draggable
                                        onDragStart={(e) => handleDragStart(e, idx)}
                                        onDragOver={handleDragOver}
                                        onDrop={(e) => handleDrop(e, idx)}
                                        onDragEnd={handleDragEnd}
                                    >
                                        <div className="flex items-center gap-3 flex-shrink-0">
                                            <div className="w-8 h-8 rounded-lg bg-[var(--surface)] border border-[var(--border-medium)] flex items-center justify-center shadow-sm">
                                                <span className="text-sm font-bold text-[var(--text-primary)]">{idx + 1}</span>
                                            </div>
                                            <div className="flex flex-col gap-1 px-1 opacity-50 group-hover:opacity-100 transition-opacity">
                                                <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]"></div>
                                                <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]"></div>
                                                <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]"></div>
                                            </div>
                                        </div>
                                        <div className="flex-1">
                                            <pre className="text-sm md:text-base text-[var(--text-primary)] font-mono whitespace-pre-wrap break-all">
                                                {option}
                                            </pre>
                                            <span className="text-xs text-[var(--text-muted)] mt-1.5 block font-medium">
                                                Original position: {originalFrontendIndex + 1}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        
                        
                        <div className="relative pt-2">
                            <label className="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-2 font-semibold tracking-wide">
                                <span>CURRENT ORDER SEQUENCE</span>
                                <span className="text-[10px] px-2 py-0.5 rounded border border-[var(--border-strong)] bg-[var(--surface-2)] text-[var(--text-secondary)]">READ-ONLY</span>
                            </label>
                            <input
                                type="text"
                                className="w-full px-5 py-4 rounded-xl text-base font-mono bg-[var(--input-bg)] border-2 border-[var(--border-color)] text-[var(--text-secondary)] opacity-80 cursor-not-allowed text-center tracking-[0.2em]"
                                value={draggableOptions.map(option => initialShuffledOptions.findIndex(opt => opt === option) + 1).join(', ')}
                                readOnly
                            />
                        </div>
                    </div>
                );

            case 'upload':
            case 'assignment_upload':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<FaUpload className="w-5 h-5 text-pink-600 dark:text-pink-400" />}
                            typeLabel="Question Type"
                            title="File Upload Assignment"
                            tag="FILE UPLOAD"
                            colors={{
                                bg: 'bg-pink-500/5 border-pink-500/20',
                                iconBg: 'bg-pink-500/10 border-pink-500/30',
                                text: 'text-pink-700 dark:text-pink-400',
                                tag: 'bg-pink-500/10 border-pink-500/20 text-pink-700 dark:text-pink-400'
                            }}
                        />
                        {!userAnswer || (typeof userAnswer === 'object' && !userAnswer.name) ? (
                            <div className="relative border-2 border-dashed border-[var(--border-strong)] hover:border-pink-500/50 rounded-2xl p-10 sm:p-14 bg-[var(--input-bg)] hover:bg-[var(--surface-2)] transition-all group overflow-hidden">
                                <input
                                    type="file"
                                    onChange={(e) => {
                                        const file = e.target.files[0];
                                        if (file) handleAnswerChange(file);
                                    }}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                    accept=".pdf,.doc,.docx,.zip,.txt,.py,.java,.cpp,.c"
                                />
                                <div className="text-center relative z-0">
                                    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-[var(--surface)] border-2 border-[var(--border-medium)] flex items-center justify-center mx-auto mb-5 group-hover:border-pink-500/30 group-hover:scale-105 shadow-sm transition-all duration-300 text-pink-500">
                                        <FaDownload className="w-6 h-6 sm:w-8 sm:h-8" />
                                    </div>
                                    <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)] mb-2">
                                        Drop your file here or click to browse
                                    </h3>
                                    <p className="text-xs sm:text-sm text-[var(--text-secondary)] font-medium mb-6">
                                        Maximum file size: 10MB
                                    </p>
                                    <div className="flex flex-wrap gap-2 justify-center max-w-md mx-auto">
                                        {['.pdf', '.docx', '.zip', '.txt', '.py', '.java', '.cpp'].map((ext) => (
                                            <span key={ext} className="text-xs px-2.5 py-1 rounded-md bg-[var(--surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)] font-mono shadow-sm">
                                                {ext}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="border-2 border-emerald-500/30 rounded-xl p-5 bg-emerald-500/5 shadow-sm">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4 flex-1 min-w-0">
                                        <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                                            <FaFileAlt className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm sm:text-base font-bold text-[var(--text-primary)] truncate mb-1">
                                                {userAnswer.name}
                                            </p>
                                            <div className="flex items-center gap-2 sm:gap-3 text-xs text-[var(--text-secondary)] font-medium">
                                                <span>{(userAnswer.size / 1024).toFixed(2)} KB</span>
                                                <span className="opacity-50">•</span>
                                                <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                                                    <FaCheckCircle className="w-3.5 h-3.5" />
                                                    Ready to submit
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleAnswerChange(''); }}
                                        className="w-10 h-10 rounded-xl bg-[var(--surface)] hover:bg-red-500/10 border border-[var(--border-medium)] hover:border-red-500/30 flex items-center justify-center transition-all flex-shrink-0 ml-4 group"
                                        title="Remove file"
                                    >
                                        <FaTimes className="w-4 h-4 text-[var(--text-muted)] group-hover:text-red-500 transition-colors" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                );


            case 'code':
                return (
                    <div className="space-y-5">
                        <QuestionHeader
                            icon={<FaCode className="w-6 h-6 text-purple-600 dark:text-purple-400" />}
                            typeLabel="Language"
                            title={currentQuestion.language ? currentQuestion.language.toUpperCase() : 'PYTHON'}
                            tag="CODE EDITOR"
                            colors={{
                                bg: 'bg-purple-500/5 border-purple-500/20',
                                iconBg: 'bg-purple-500/10 border-purple-500/30',
                                text: 'text-purple-700 dark:text-purple-400',
                                tag: 'bg-purple-500/10 border-purple-500/20 text-purple-700 dark:text-purple-400'
                            }}
                        />

                        <div className={`grid grid-cols-1 ${currentQuestion.test_cases && currentQuestion.test_cases.some(tc => !tc.hidden) ? 'lg:grid-cols-[1fr_1.5fr]' : ''} gap-5 sm:gap-6`}>
                            {currentQuestion.test_cases && currentQuestion.test_cases.some(tc => !tc.hidden) && (
                                <div className="lg:max-h-[700px] lg:overflow-y-auto custom-scrollbar pr-1">
                                    <div className="bg-[var(--surface)] border-2 border-[var(--border-strong)] rounded-2xl p-5 shadow-sm">
                                        <div className="flex items-center gap-2.5 mb-5 pb-3 border-b border-[var(--border-subtle)]">
                                            <FaCheckCircle className="w-5 h-5 text-emerald-500" />
                                            <h4 className="text-base font-bold text-[var(--text-primary)]">
                                                Test Data ({currentQuestion.test_cases.filter(tc => !tc.hidden).length})
                                            </h4>
                                        </div>
                                        <div className="space-y-4">
                                            {currentQuestion.test_cases.filter(tc => !tc.hidden).map((tc, idx) => (
                                                <div key={tc.id} className="bg-[var(--input-bg)] border border-[var(--border-color)] rounded-xl p-4 hover:border-emerald-500/30 hover:shadow-sm transition-all duration-300">
                                                    <div className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
                                                        Test Case #{idx + 1}
                                                    </div>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <div className="text-xs text-[var(--text-muted)] font-semibold mb-1.5 flex items-center gap-2">
                                                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/80"></span>
                                                                Input
                                                            </div>
                                                            <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-lg p-3">
                                                                <pre className="text-xs sm:text-sm text-[var(--text-primary)] font-mono whitespace-pre-wrap break-all opacity-90">
                                                                    {tc.expected_input || 'None'}
                                                                </pre>
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <div className="text-xs text-[var(--text-muted)] font-semibold mb-1.5 flex items-center gap-2">
                                                                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400/80"></span>
                                                                Expected Output
                                                            </div>
                                                            <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-lg p-3">
                                                                <pre className="text-xs sm:text-sm text-[var(--text-primary)] font-mono whitespace-pre-wrap break-all opacity-90">
                                                                    {tc.expected_output}
                                                                </pre>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Code Editor Column */}
                            <div className={currentQuestion.test_cases && currentQuestion.test_cases.some(tc => !tc.hidden) ? '' : 'lg:col-span-2'}>
                                <div className="border-2 border-[var(--border-strong)] rounded-2xl overflow-hidden bg-[var(--surface)] h-full flex flex-col shadow-sm">
                                    <div className="flex items-center justify-between px-5 py-3.5 bg-[var(--input-bg)] border-b-2 border-[var(--border-strong)]">
                                        <div className="flex items-center gap-4">
                                            <div className="flex gap-2">
                                                <div className="w-3.5 h-3.5 rounded-full border border-red-500/30 bg-red-400/80"></div>
                                                <div className="w-3.5 h-3.5 rounded-full border border-yellow-500/30 bg-yellow-400/80"></div>
                                                <div className="w-3.5 h-3.5 rounded-full border border-green-500/30 bg-green-400/80"></div>
                                            </div>
                                            <span className="text-xs sm:text-sm font-semibold text-[var(--text-secondary)] bg-[var(--surface-2)] px-2 py-0.5 rounded border border-[var(--border-color)]">
                                                solution.{currentQuestion.language === 'python' ? 'py' : currentQuestion.language === 'java' ? 'java' : currentQuestion.language === 'cpp' ? 'cpp' : 'txt'}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-3 bg-[var(--surface)] px-3 py-1 rounded-lg border border-[var(--border-color)]">
                                            <span className="text-xs font-mono font-medium text-[var(--text-muted)]">
                                                {(userAnswer || '').split('\n').length} lines
                                            </span>
                                        </div>
                                    </div>

                                    <div className="relative flex-1 bg-[var(--surface-2)]/50">
                                        <textarea
                                            className="w-full h-full px-5 py-5 text-sm sm:text-base font-mono min-h-[600px] resize-y bg-transparent border-0 focus:outline-none focus:ring-0 text-[var(--text-primary)]"
                                            placeholder="// Write your code here..."
                                            value={userAnswer}
                                            onChange={(e) => handleAnswerChange(e.target.value)}
                                            spellCheck={false}
                                            style={{ lineHeight: '1.7', tabSize: 4 }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                );

            default:
                return (
                    <div className="space-y-4">
                        <QuestionHeader
                            icon={<FaLightbulb className="w-6 h-6 text-gray-600 dark:text-gray-400" />}
                            typeLabel="Input Type"
                            title="Detailed Long-Form Answer"
                            tag="TEXT"
                            colors={{
                                bg: 'bg-[var(--input-bg)] border-[var(--border-medium)]',
                                iconBg: 'bg-[var(--surface)] border-[var(--border-strong)]',
                                text: 'text-[var(--text-primary)]',
                                tag: 'bg-[var(--surface-2)] border-[var(--border-strong)] text-[var(--text-secondary)]'
                            }}
                        />
                        <div className="relative group">
                            <textarea
                                className="w-full px-5 py-4 rounded-xl text-base sm:text-lg min-h-[250px] resize-y bg-[var(--input-bg)] hover:bg-[var(--surface-2)] border-2 border-[var(--border-color)] focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10 transition-all placeholder-[var(--text-muted)] text-[var(--text-primary)] font-medium"
                                placeholder="Type your detailed answer here..."
                                value={userAnswer}
                                onChange={(e) => handleAnswerChange(e.target.value)}
                                style={{ lineHeight: '1.8' }}
                            />
                            <div className="absolute bottom-4 right-4 text-xs font-semibold text-[var(--text-secondary)] bg-[var(--surface)] px-3 py-1.5 rounded-lg border border-[var(--border-strong)] shadow-sm">
                                {(userAnswer || '').length} characters
                            </div>
                        </div>
                    </div>
                );
        }
    };

    // Loading state
    if (loading && !currentQuestion) {
        return (
            <div className="flex min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="flex items-center justify-center p-8" style={{ minHeight: 'calc(100vh - 80px)' }}>
                        <div className="flex items-center justify-center py-8 sm:py-12">
                            <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-b-2 border-blue-500"></div>
                            <p className="text-base muted">Initializing test mode...</p>
                        </div>

                    </div>
                </main>
            </div>
        );
    }

    // Error state
    if (error && !currentQuestion) {
        return (
            <div className="flex min-h-screen relative grid-texture">
                <TeacherSidebar />
                <main className="flex-1">
                    <Header isAuth />
                    <div className="flex items-center justify-center p-8" style={{ minHeight: 'calc(100vh - 80px)' }}>
                        <div className="text-center max-w-md mx-auto">
                            <div className="w-16 h-16 bg-red-500/10 rounded-xl border border-red-500/30 flex items-center justify-center mx-auto mb-4">
                                <FaTimes className="w-8 h-8 text-red-400" />
                            </div>
                            <h3 className="text-xl font-bold mb-2">Failed to Load Test</h3>
                            <p className="text-sm muted mb-6">{error}</p>
                            <button
                                onClick={() => {
                                    clearError();
                                    resetQuiz();
                                    navigate('/teacher/questions');
                                }}
                                className="btn-grad text-white px-6 py-3 rounded-lg font-semibold hover:scale-105 active:scale-95 transition-all inline-flex items-center gap-2"
                            >
                                <FaArrowLeft className="w-4 h-4" />
                                Back to Questions
                            </button>
                        </div>
                    </div>
                </main>
            </div>
        );
    }

    const timerStatus = getTimerStatus();

    return (
        <div className="flex min-h-screen relative grid-texture">
            <TeacherSidebar />
            <main className="flex-1 w-full lg:w-auto">
                <Header isAuth />
                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Header */}
                    <div className="mb-6 lg:mb-8">
                        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Questions</h1>
                        <p className="text-sm muted">Create and manage your questions</p>
                    </div>
                    {/* Action buttons */}
                    <QuestionActionButtons activeButton="library" />



                    {/* Main card */}
                    <div className="card-strong p-3 sm:p-6 min-h-[400px] sm:min-h-[600px] w-full max-w-full overflow-x-auto border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
                        {/* Card header with timer and controls */}
                        <div className="flex sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 gap-4 border-b-2 border-[var(--border-subtle)]">

                            <div className="flex items-start gap-4 mb-4">
                                <Link
                                    to="/teacher/questions"
                                    onClick={() => {
                                        resetQuiz();
                                    }}
                                    className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
                                >
                                    <FaChevronLeft className="w-4 h-4" />
                                </Link>
                                <div>
                                    <h2 className="text-lg sm:text-xl font-bold mb-1">
                                        Test Mode
                                    </h2>
                                    <p className="text-xs sm:text-sm muted">
                                        Preview and test this question
                                    </p>
                                </div>
                            </div>


                            <div className="flex items-center gap-1 sm:gap-3 flex-shrink-0">
                                {timeLeft !== null && (
                                    <div className={`flex items-center gap-2 px-2 sm:px-4 py-1.5 sm:py-2.5 rounded-lg border ${timerStatus.bg} ${timerStatus.border}`}>
                                        <MdTimer className={`w-2 h-2 sm:w-4 sm:h-4 ${timerStatus.text} ${timerStatus.animate ? 'animate-pulse' : ''}`} />
                                        <span className={`text-base text-sm font-mono font-semibold ${timerStatus.text} ${timerStatus.animate ? 'animate-pulse' : ''}`}>
                                            {formatTime(timeLeft)}
                                        </span>
                                    </div>
                                )}
                                <button
                                    onClick={handleQuitTest}
                                    className="px-2 sm:px-4 py-2 sm:py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold active:scale-95 transition-all text-sm whitespace-nowrap inline-flex items-center gap-2"
                                >
                                    <FaTimes className="w-4 h-4" />
                                    <span className="hidden sm:inline">Quit Test</span>

                                </button>
                            </div>
                        </div>

                        {currentQuestion ? (
                            <div className="space-y-3 sm:space-y-4">
                                {/* Question header */}
                                <div className="mb-6">
                                    <div className="flex items-center justify-between mb-4 px-1">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center">
                                                <TbSum className="w-5 h-5 text-cyan-400" />
                                            </div>
                                            <div>
                                                <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">
                                                    {currentQuestion.summary}
                                                </h3>

                                                <div className="flex flex-wrap gap-2 sm:gap-4 text-xs sm:text-sm muted">
                                                    {currentQuestion.language && (
                                                        <div className="flex items-center gap-1.5">
                                                            <FaFileCode className="w-3 h-3" />
                                                            <span className="font-medium">{currentQuestion.language}</span>
                                                        </div>
                                                    )}
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="font-medium">Type: {currentQuestion.type}</span>
                                                    </div>
                                                    {paper?.is_trial_mode && (
                                                        <div className="flex items-center gap-1.5">
                                                            <span>Trial Mode</span>
                                                        </div>
                                                    )}
                                                </div>

                                            </div>

                                        </div>

                                        <span className="text-xs font-bold text-[var(--text-secondary)] bg-[var(--input-bg)] border-2 border-[var(--border-color)] px-3 py-1.5 rounded-xl shadow-md">
                                            Points: <span className="text-cyan-600 dark:text-cyan-400">{currentQuestion.points}</span>
                                        </span>

                                    </div>

                                    {answerResult && (
                                        <div className="mb-4 p-4 bg-orange-500/10 border-2 border-orange-500/40 rounded-xl flex items-start gap-4">
                                            <div className='flex items-start gap-3'>
                                                <div className="w-10 h-10 rounded-xl bg-orange-500/20 border-2 border-orange-500/40 dark:border-orange-500/30 flex items-center justify-center flex-shrink-0">
                                                    <AiOutlineWarning className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                                                </div>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm text-orange-700 dark:text-orange-400 font-semibold mb-1">Important Notice</p>
                                                <p className="text-xs text-orange-600 dark:text-orange-400/80">Last submitted answer is considered for evaluation</p>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Question description */}
                                {currentQuestion.description && (
                                    <div className="mb-6 p-5 bg-[var(--surface)] rounded-xl border-2 border-dashed border-[var(--border-color)]">
                                        <div
                                            className="prose prose-invert max-w-none text-sm sm:text-base"
                                            dangerouslySetInnerHTML={{ __html: currentQuestion.description }}
                                        />
                                    </div>
                                )}

                                {/* Available files */}
                                {currentQuestion.files && currentQuestion.files.length > 0 && (
                                    <div className="bg-blue-500/5 rounded-2xl p-5 sm:p-6 border-2 border-blue-500/20">
                                        <div className="flex items-center gap-4 mb-5">
                                            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/20 flex items-center justify-center shadow-sm">
                                                <FaExternalLinkAlt className="w-5 h-5 text-blue-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)] mb-1">Attached Resources</h3>
                                                <p className="text-sm text-[var(--text-secondary)]">{currentQuestion.files.length} file{currentQuestion.files.length !== 1 ? 's' : ''} available</p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                                            {currentQuestion.files.map((file) => (
                                                <a
                                                    key={file.id}
                                                    href={file.url.startsWith('http')
                                                        ? file.url
                                                        : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${file.url}`
                                                    }
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="group flex items-center justify-between p-4 bg-[var(--input-bg)] border-2 border-[var(--border-color)] hover:border-blue-500/50 hover:bg-[var(--surface)] hover:shadow-md rounded-xl transition-all duration-300"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                                                            <FaFileAlt className="w-4 h-4 text-blue-500" />
                                                        </div>
                                                        <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-500 transition-colors line-clamp-1">{file.name}</span>
                                                    </div>
                                                    <div className="w-8 h-8 rounded-full bg-[var(--border-color)] group-hover:bg-blue-500/10 flex items-center justify-center transition-colors ml-2">
                                                        <FaExternalLinkAlt className="w-3.5 h-3.5 text-[var(--text-secondary)] group-hover:text-blue-500" />
                                                    </div>
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Answer input */}
                                <div className="mt-4 pt-6 sm:pt-8 gap-4 border-t-2 border-[var(--border-subtle)]">
                                    <div className="flex items-center gap-3 mb-2">
                                        <label className="text-base sm:text-lg font-bold text-[var(--text-primary)]">
                                            {currentQuestion.type === 'code' ? 'Write Your Program' :
                                                currentQuestion.type === 'mcq' ? 'Select One Answer' :
                                                    currentQuestion.type === 'mcc' ? 'Select All Correct Answers' :
                                                        currentQuestion.type === 'arrange' ? 'Arrange in Correct Order' :
                                                            'Enter Your Answer'}
                                        </label>
                                    </div>
                                    <div className="bg-[var(--surface)] p-1 rounded-xl">
                                        {renderQuestionInput()}
                                    </div>
                                </div>

                                {/* Action buttons */}
                                <div className="flex justify-between sm:gap-3 sm:justify-end gap-3 pt-6 sm:pt-8 border-t-2 border-[var(--border-subtle)] mt-auto">
                                    <button
                                        onClick={handleSubmitAnswer}
                                        disabled={submitting || loading}
                                        className="px-5 sm:px-8 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-500 text-white font-semibold hover:shadow-xl hover:shadow-cyan-600/30 active:scale-95 transition-all duration-300 disabled:opacity-60 text-sm "
                                    >
                                        {submitting ? (
                                            <>

                                                <span>Checking...</span>
                                            </>
                                        ) : (
                                            <>

                                                <span>Check Answer</span>
                                            </>
                                        )}
                                    </button>

                                    <button
                                        onClick={handleCompleteTest}
                                        className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 font-semibold transition-all duration-300 text-sm"
                                    >

                                        <span>Complete Test</span>
                                    </button>
                                </div>

                                {/* Result display */}
                                {showResult && answerResult && (
                                    <div className={`mt-6 rounded-xl p-4 sm:p-5 border-2 transition-all duration-300 ${answerResult.success
                                        ? 'bg-emerald-500/10 border-emerald-500/30'
                                        : 'bg-red-500/10 border-red-500/30'
                                        }`}>
                                        <div className="flex items-start gap-3 sm:gap-4">
                                            <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center flex-shrink-0 border-2 ${answerResult.success
                                                ? 'bg-emerald-500/15 border-emerald-500/30'
                                                : 'bg-red-500/15 border-red-500/30'
                                                }`}>
                                                {answerResult.success ? (
                                                    <FaCheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600 dark:text-emerald-400" />
                                                ) : (
                                                    <FaTimes className="w-5 h-5 sm:w-6 sm:h-6 text-red-600 dark:text-red-400" />
                                                )}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className={`text-base sm:text-lg font-bold mb-1 ${answerResult.success ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-700 dark:text-red-400'
                                                    }`}>
                                                    {answerResult.success ? 'Correct Answer! 🎉' : 'Incorrect Answer'}
                                                </h3>
                                                <p className={`text-xs sm:text-sm mb-0 ${answerResult.success ? 'text-emerald-600/80 dark:text-emerald-300/70' : 'text-red-600/80 dark:text-red-300/70'}`}>
                                                    {answerResult.success ? 'Great job! Your answer matches the expected output.' : 'Your answer did not match. Review and try again.'}
                                                </p>
                                                {answerResult.error_message && (
                                                    <div className="mt-3 p-3 sm:p-4 bg-[var(--input-bg)] rounded-lg border border-[var(--border-color)]">
                                                        <p className="text-xs sm:text-sm font-mono leading-relaxed text-[var(--text-secondary)] whitespace-pre-wrap break-words">{answerResult.error_message}</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-12 sm:py-20 text-center px-4">
                                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-[var(--input-bg)] rounded-xl border-2 border-[var(--border-strong)] flex items-center justify-center mx-auto mb-5">
                                    <AiOutlineWarning className="w-8 h-8 sm:w-10 sm:h-10 text-[var(--text-muted)]" />
                                </div>
                                <h3 className="text-lg sm:text-xl font-bold text-[var(--text-primary)] mb-2">No Question Available</h3>
                                <p className="text-sm text-[var(--text-muted)] mb-6 max-w-sm">There are no questions loaded. Go back to the question library to select one.</p>
                                <button
                                    onClick={() => {
                                        resetQuiz();
                                        navigate('/teacher/questions');
                                    }}
                                    className="px-6 py-2.5 sm:py-3 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] hover:border-[var(--border-medium)] font-semibold active:scale-95 transition-all duration-300 inline-flex items-center gap-2 text-sm"
                                >
                                    <FaArrowLeft className="w-4 h-4" />
                                    <span>Back to Questions</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default TestQuestion;
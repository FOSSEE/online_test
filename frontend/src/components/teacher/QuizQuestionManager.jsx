import React, { useState, useEffect } from 'react';
import { FaPlus, FaTrash, FaChevronUp, FaChevronDown, FaSearch, FaTimes } from 'react-icons/fa';
import { getQuizQuestions, addQuestionToQuiz, removeQuestionFromQuiz, reorderQuizQuestions, fetchTeacherQuestions } from '../../api/api';

const QuizQuestionManager = ({ quizId, onClose, onUpdate }) => {
    const [quizQuestions, setQuizQuestions] = useState({ fixed_questions: [], total_marks: 0 });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showAddQuestions, setShowAddQuestions] = useState(false);
    const [availableQuestions, setAvailableQuestions] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedQuestions, setSelectedQuestions] = useState([]);
    const [loadingQuestions, setLoadingQuestions] = useState(false);

    useEffect(() => {
        loadQuizQuestions();
    }, [quizId]);

    // Debug: Log when quizQuestions changes
    useEffect(() => {
        console.log('quizQuestions state changed:', quizQuestions);
        console.log('quizQuestions?.fixed_questions:', quizQuestions?.fixed_questions);
        console.log('quizQuestions?.fixed_questions?.length:', quizQuestions?.fixed_questions?.length);
    }, [quizQuestions]);

    const loadQuizQuestions = async () => {
        try {
            setLoading(true);
            console.log('Loading quiz questions for quizId:', quizId);
            const data = await getQuizQuestions(quizId);
            console.log('Raw API response:', JSON.stringify(data, null, 2));
            console.log('Type of data:', typeof data);
            console.log('Is data an object?', data && typeof data === 'object');
            setQuizQuestions(data);
        } catch (err) {
            console.error('Failed to load quiz questions:', err);
            console.error('Error response:', err.response);
            console.error('Error message:', err.message);
            alert('Failed to load quiz questions: ' + (err.response?.data?.error || err.message));
            // Set empty state on error
            setQuizQuestions({ fixed_questions: [], total_marks: 0 });
        } finally {
            setLoading(false);
        }
    };

    const loadAvailableQuestions = async () => {
        try {
            setLoadingQuestions(true);
            const questions = await fetchTeacherQuestions({ search: searchTerm });
            console.log('Current selectedQuestions:', selectedQuestions);

            //Filter out questions already in quiz (safely handle null quizQuestioins)
            //Filter out questions already in quiz (safely handle null quizQuestioins)
            // const existingIds = (quizQuestions?.fixed_questions || []).map(q => q.id);
            // const filtered = questions.filter(q => !existingIds.includes(q.id));
            setAvailableQuestions(questions);
        } catch (err) {
            console.error('Failed to load available questions:', err);
            alert('Failed to load available questions: ' + (err.response?.data?.error || err.message));
            setAvailableQuestions([]);
        } finally {
            setLoadingQuestions(false);
        }
    };

    useEffect(() => {
        // Only load questions if quizQuestions has been loaded and Add Questions panel is open
        // Also ensure we're not still loading quiz questions
        if (showAddQuestions && quizQuestions && !loading) {
            if (searchTerm) {
                const timeoutId = setTimeout(() => {
                    loadAvailableQuestions();
                }, 500);
                return () => clearTimeout(timeoutId);
            } else {
                loadAvailableQuestions();
            }
        }
    }, [showAddQuestions, searchTerm, quizQuestions, loading]);

    const handleUpdateQuestions = async () => {
        try {
            setSaving(true);

            const existingIds = (quizQuestions?.fixed_questions || []).map(q => q.id);
            const currentIds = selectedQuestions || [];

            // Calculate differences
            const toAdd = currentIds.filter(id => !existingIds.includes(id));
            const toRemove = existingIds.filter(id => !currentIds.includes(id));

            if (toAdd.length === 0 && toRemove.length === 0) {
                alert('No changes to save.');
                return;
            }

            // Execute additions
            for (const questionId of toAdd) {
                await addQuestionToQuiz(quizId, questionId, true);
            }

            // Execute removals
            for (const questionId of toRemove) {
                await removeQuestionFromQuiz(quizId, questionId);
            }

            setShowAddQuestions(false);
            await loadQuizQuestions();
            if (onUpdate) onUpdate();
        } catch (err) {
            console.error('Failed to update questions:', err);
            alert('Failed to update questions: ' + (err.response?.data?.error || err.message));
        } finally {
            setSaving(false);
        }
    };

    const handleRemoveQuestion = async (questionId) => {
        if (!window.confirm('Are you sure you want to remove this question from the quiz?')) {
            return;
        }
        try {
            await removeQuestionFromQuiz(quizId, questionId);
            await loadQuizQuestions();
            if (onUpdate) onUpdate();
        } catch (err) {
            console.error('Failed to remove question:', err);
            alert('Failed to remove question');
        }
    };

    const handleReorder = async (questionId, direction) => {
        // Safely handle null quizQuestions
        if (!quizQuestions || !quizQuestions.fixed_questions || quizQuestions.fixed_questions.length === 0) {
            return;
        }

        const questions = [...quizQuestions.fixed_questions];
        const currentIndex = questions.findIndex(q => q.id === questionId);
        if (currentIndex === -1) return;

        const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        if (newIndex < 0 || newIndex >= questions.length) return;

        [questions[currentIndex], questions[newIndex]] = [questions[newIndex], questions[currentIndex]];

        try {
            setSaving(true);
            const questionOrder = questions.map(q => q.id);
            await reorderQuizQuestions(quizId, questionOrder);
            await loadQuizQuestions();
        } catch (err) {
            console.error('Failed to reorder questions:', err);
            alert('Failed to reorder questions: ' + (err.response?.data?.error || err.message));
        } finally {
            setSaving(false);
        }
    };

    const toggleQuestionSelection = (questionId) => {
        setSelectedQuestions(prev =>
            prev.includes(questionId)
                ? prev.filter(id => id !== questionId)
                : [...prev, questionId]
        );
    };

    if (loading) {
        return (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                <div className="card-strong rounded-xl p-6 max-w-4xl w-full mx-4 shadow-2xl">
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    </div>
                </div>
            </div>
        );
    }

    // Debug render
    console.log('Rendering QuizQuestionManager with quizQuestions:', quizQuestions);
    console.log('quizQuestions?.fixed_questions in render:', quizQuestions?.fixed_questions);
    console.log('Is array?', Array.isArray(quizQuestions?.fixed_questions));
    console.log('Length:', quizQuestions?.fixed_questions?.length);

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto">
            <div className="card-strong rounded-xl p-6 max-w-6xl w-full mx-4 my-8 shadow-2xl">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h2 className="text-2xl font-bold">Manage Quiz Questions</h2>
                        <p className="text-sm muted mt-1">
                            {Array.isArray(quizQuestions?.fixed_questions) ? quizQuestions.fixed_questions.length : 0} questions • {quizQuestions?.total_marks || 0} total marks
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center hover:bg-white/10 transition"
                    >
                        <FaTimes className="w-5 h-5" />
                    </button>
                </div>

                <div className="space-y-6">
                    {/* Current Questions */}
                    <div>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">Current Questions</h3>
                            <button
                                onClick={() => {
                                    setShowAddQuestions(!showAddQuestions);
                                    // Initialize selected questions with questions already in the quiz
                                    const existingIds = (quizQuestions?.fixed_questions || []).map(q => q.id);
                                    setSelectedQuestions(existingIds);
                                }}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2 text-sm font-medium"
                            >
                                <FaPlus className="w-3 h-3" />
                                Add Questions
                            </button>
                        </div>

                        {quizQuestions?.fixed_questions?.length > 0 ? (
                            <div className="space-y-2">
                                {quizQuestions.fixed_questions.map((question, index) => (
                                    <div
                                        key={question.id}
                                        className="card p-4 flex items-center justify-between"
                                    >
                                        <div className="flex items-center gap-4 flex-1">
                                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-sm">
                                                {index + 1}
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold">{question.summary}</h4>
                                                <div className="flex items-center gap-3 mt-1 text-xs muted">
                                                    <span className="px-2 py-0.5 rounded bg-gray-500/20 border border-gray-500/30 uppercase">
                                                        {question.type}
                                                    </span>
                                                    <span>{question.points} points</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleReorder(question.id, 'up')}
                                                disabled={index === 0 || saving}
                                                className="px-3 py-2 border border-white/10 rounded-lg hover:bg-white/5 transition disabled:opacity-30 disabled:cursor-not-allowed"
                                                title="Move up"
                                            >
                                                <FaChevronUp className="w-3 h-3" />
                                            </button>
                                            <button
                                                onClick={() => handleReorder(question.id, 'down')}
                                                disabled={index === quizQuestions.fixed_questions.length - 1 || saving}
                                                className="px-3 py-2 border border-white/10 rounded-lg hover:bg-white/5 transition disabled:opacity-30 disabled:cursor-not-allowed"
                                                title="Move down"
                                            >
                                                <FaChevronDown className="w-3 h-3" />
                                            </button>
                                            <button
                                                onClick={() => handleRemoveQuestion(question.id)}
                                                className="px-3 py-2 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/20 transition"
                                                title="Remove"
                                            >
                                                <FaTrash className="w-3 h-3" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-8 text-muted">
                                <p>No questions added yet. Click "Add Questions" to add questions to this quiz.</p>
                            </div>
                        )}
                    </div>

                    {/* Add Questions Panel */}
                    {showAddQuestions && (
                        <div className="card-strong p-6 border-t border-white/10">
                            <div className="mb-4">
                                <h3 className="text-lg font-bold mb-3">Add Questions from Question Bank</h3>
                                <div className="relative">
                                    <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-muted w-4 h-4" />
                                    <input
                                        type="text"
                                        placeholder="Search questions..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2 bg-black/20 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-blue-500/50"
                                    />
                                </div>
                            </div>

                            {loadingQuestions ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                                </div>
                            ) : availableQuestions.length > 0 ? (
                                <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
                                    {availableQuestions.map((question) => (
                                        <div
                                            key={question.id}
                                            className={`card p-3 cursor-pointer transition ${selectedQuestions.includes(question.id)
                                                ? 'bg-blue-500/20 border-blue-500/50'
                                                : 'hover:bg-white/5'
                                                }`}
                                            onClick={() => toggleQuestionSelection(question.id)}
                                        >
                                            <div className="flex items-center gap-3">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedQuestions.includes(question.id)}
                                                    onChange={() => toggleQuestionSelection(question.id)}
                                                    className="toggle-checkbox"
                                                />
                                                <div className="flex-1">
                                                    <h4 className="font-semibold text-sm">{question.summary}</h4>
                                                    <div className="flex items-center gap-2 mt-1 text-xs muted">
                                                        <span className="px-2 py-0.5 rounded bg-gray-500/20 border border-gray-500/30 uppercase">
                                                            {question.type}
                                                        </span>
                                                        <span>{question.points} points</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}

                                </div>
                            ) : (
                                <div className="text-center py-8 text-muted">
                                    <p>No questions found. Create questions first.</p>
                                </div>
                            )}

                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => {
                                        setShowAddQuestions(false);
                                        setSelectedQuestions([]);
                                        setSearchTerm('');
                                    }}
                                    className="px-4 py-2 border border-white/10 rounded-lg hover:bg-white/5 transition"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleUpdateQuestions}
                                    disabled={(() => {
                                        const existingIds = (quizQuestions?.fixed_questions || []).map(q => q.id);
                                        const currentIds = selectedQuestions || [];
                                        const toAdd = currentIds.filter(id => !existingIds.includes(id));
                                        const toRemove = existingIds.filter(id => !currentIds.includes(id));
                                        return (toAdd.length === 0 && toRemove.length === 0) || saving;
                                    })()}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {(() => {
                                        const existingIds = (quizQuestions?.fixed_questions || []).map(q => q.id);
                                        const currentIds = selectedQuestions || [];
                                        const toAdd = currentIds.filter(id => !existingIds.includes(id));
                                        const toRemove = existingIds.filter(id => !currentIds.includes(id));

                                        if (saving) return 'Saving...';

                                        const parts = [];
                                        if (toAdd.length > 0) parts.push(`Add ${toAdd.length}`);
                                        if (toRemove.length > 0) parts.push(`Remove ${toRemove.length}`);

                                        if (parts.length === 0) return 'No Changes';
                                        return parts.join(', ');
                                    })()}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default QuizQuestionManager;


import React, { useState, useEffect, useRef } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { FaClock, FaCheck, FaArrowRight, FaTimes } from 'react-icons/fa';
import { AiOutlineWarning } from 'react-icons/ai';
import QuizSidebar from '../components/layout/QuizSidebar';
import { startQuiz, submitAnswer, getAnswerResult, quitQuiz } from '../api/api';

const Quiz = () => {
  const { courseId, quizId } = useParams();
  const navigate = useNavigate();
  const [answerPaper, setAnswerPaper] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [attemptedQuestions, setAttemptedQuestions] = useState(new Set());
  const [evaluatingQuestions, setEvaluatingQuestions] = useState(new Set());
  const [correctAnswers, setCorrectAnswers] = useState(new Set());
  const [incorrectAnswers, setIncorrectAnswers] = useState(new Set());
  const [questionResults, setQuestionResults] = useState({});
  const [showQuitConfirm, setShowQuitConfirm] = useState(false);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
    if (courseId && quizId) {
      loadQuiz();
    }
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [courseId, quizId]);

  useEffect(() => {
    if (timeLeft > 0) {
      timerIntervalRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            handleAutoSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [timeLeft]);

  const loadQuiz = async () => {
    try {
      setLoading(true);
      const data = await startQuiz(courseId, quizId);
      setAnswerPaper(data.answerpaper);
      setTimeLeft(data.time_left || 0);

      // Initialize answers object
      const initialAnswers = {};
      data.answerpaper.questions.forEach((q) => {
        initialAnswers[q.id] = '';
      });
      setAnswers(initialAnswers);

      setError(null);
    } catch (err) {
      console.error('Failed to start quiz:', err);
      setError(err.response?.data?.message || 'Failed to start quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSubmit = async () => {
    // Auto-submit when time expires
    if (answerPaper) {
      await handleQuit();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value
    }));
  };

  // Render code error with detailed information
  const renderCodeError = (error, index) => {
    // Hidden test case
    if (error.hidden) {
      return (
        <div key={index} className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded">
          <p className="font-semibold">🔒 Hidden test case failed</p>
          <p className="text-sm text-gray-400">
            This test case is hidden to prevent reverse engineering the solution.
          </p>
        </div>
      );
    }

    // Assertion error (code exception)
    if (error.type === 'assertion') {
      return (
        <div key={index} className="p-3 bg-red-500/10 border border-red-500/30 rounded">
          <h5 className="font-semibold mb-2">Test Case #{index + 1}</h5>

          {error.test_case && (
            <div className="mb-2">
              <p className="text-sm font-semibold">We tried your code with:</p>
              <pre className="text-sm bg-black/20 p-2 rounded mt-1">
                {error.test_case}
              </pre>
            </div>
          )}

          <div className="mt-2">
            <p className="text-sm font-semibold mb-1">Error occurred:</p>
            <table className="text-sm w-full">
              <tbody>
                <tr>
                  <td className="font-semibold pr-2 py-1">Exception:</td>
                  <td className="text-red-400">{error.exception}</td>
                </tr>
                <tr>
                  <td className="font-semibold pr-2 py-1">Message:</td>
                  <td>{error.message}</td>
                </tr>
                {error.traceback && (
                  <tr>
                    <td className="font-semibold pr-2 py-1 align-top">Traceback:</td>
                    <td>
                      <pre className="text-xs bg-black/20 p-2 rounded mt-1 overflow-auto max-h-40">
                        {error.traceback}
                      </pre>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // stdio error (input/output mismatch)
    if (error.type === 'stdio') {
      return (
        <div key={index} className="p-3 bg-red-500/10 border border-red-500/30 rounded">
          <h5 className="font-semibold mb-2">Test Case #{index + 1}</h5>

          {error.given_input && (
            <div className="mb-2">
              <p className="text-sm">
                <span className="font-semibold">Input:</span> {error.given_input}
              </p>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="text-sm w-full border-collapse">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left p-2">Line</th>
                  <th className="text-left p-2">Expected Output</th>
                  <th className="text-left p-2">Your Output</th>
                  <th className="text-left p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {error.expected_output?.map((expected, i) => {
                  const userOut = error.user_output?.[i] || '';
                  const isError = error.error_line_numbers?.includes(i);

                  return (
                    <tr key={i} className={isError ? 'bg-red-500/10' : ''}>
                      <td className="p-2">{i + 1}</td>
                      <td className="p-2 font-mono text-xs">{expected}</td>
                      <td className="p-2 font-mono text-xs">{userOut}</td>
                      <td className="p-2">
                        {isError ? (
                          <FaTimes className="text-red-500" />
                        ) : (
                          <FaCheck className="text-green-500" />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {error.error_msg && (
            <div className="mt-2 p-2 bg-red-500/20 rounded">
              <p className="text-sm">
                <span className="font-semibold">Error:</span> {error.error_msg}
              </p>
            </div>
          )}
        </div>
      );
    }

    // Generic error (no type)
    return (
      <div key={index} className="p-3 bg-red-500/10 border border-red-500/30 rounded">
        <pre className="text-sm">{typeof error === 'string' ? error : JSON.stringify(error, null, 2)}</pre>
      </div>
    );
  };

  // Render error display based on error type
  const renderErrorDisplay = (error) => {
    // If error is a string, show it directly
    if (typeof error === 'string') {
      return <p className="text-sm">{error}</p>;
    }

    // If error is an array
    if (Array.isArray(error)) {
      // Empty array
      if (error.length === 0) {
        return <p className="text-sm">No error occurred</p>;
      }

      // Simple string array (non-code questions)
      if (typeof error[0] === 'string') {
        return (
          <div className="space-y-1">
            {error.map((err, idx) => (
              <p key={idx} className="text-sm">{err}</p>
            ))}
          </div>
        );
      }

      // Complex error objects (code questions)
      return (
        <div className="space-y-3">
          {error.map((err, idx) => renderCodeError(err, idx))}
        </div>
      );
    }

    // Fallback for unexpected formats
    return <pre className="text-sm overflow-auto max-h-40">{JSON.stringify(error, null, 2)}</pre>;
  };

  // Handle immediate results for non-code questions
  const handleImmediateResult = (questionId, result) => {
    // Mark as attempted
    setAttemptedQuestions((prev) => new Set([...prev, questionId]));

    // Store result for display
    setQuestionResults((prev) => ({
      ...prev,
      [questionId]: result
    }));

    // Update correct/incorrect status
    if (result.success) {
      setCorrectAnswers((prev) => new Set([...prev, questionId]));
      setIncorrectAnswers((prev) => {
        const newSet = new Set(prev);
        newSet.delete(questionId);
        return newSet;
      });
      // Result shown in UI
    } else {
      setIncorrectAnswers((prev) => new Set([...prev, questionId]));
      setCorrectAnswers((prev) => {
        const newSet = new Set(prev);
        newSet.delete(questionId);
        return newSet;
      });

      // Error shown in UI
    }
  };

  // Poll for code evaluation results
  const pollForCodeResult = async (uid, questionId, maxAttempts = 60) => {
    let attempts = 0;

    const poll = async () => {
      try {
        const result = await getAnswerResult(uid);

        if (result.status === 'done') {
          // Evaluation complete - remove from evaluating set
          setEvaluatingQuestions((prev) => {
            const newSet = new Set(prev);
            newSet.delete(questionId);
            return newSet;
          });

          // Parse and handle result
          const parsedResult = JSON.parse(result.result);
          handleImmediateResult(questionId, parsedResult);
          return;
        }

        // Still running - poll again
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000); // Poll every 1 second
        } else {
          // Timeout
          setEvaluatingQuestions((prev) => {
            const newSet = new Set(prev);
            newSet.delete(questionId);
            return newSet;
          });
          // Timeout shown in UI
        }
      } catch (error) {
        console.error('Polling error:', error);
        setEvaluatingQuestions((prev) => {
          const newSet = new Set(prev);
          newSet.delete(questionId);
          return newSet;
        });
        // Error shown in UI
      }
    };

    poll();
  };

  const handleSubmitAnswer = async (questionId) => {
    const answer = answers[questionId];
    const currentQuestion = answerPaper.questions.find(q => q.id === questionId);

    if (!currentQuestion) {
      alert('Question not found');
      return;
    }

    // Validate answer based on question type
    if (currentQuestion.type === 'mcc') {
      // For multiple choice, check if at least one option is selected
      if (!answer || (Array.isArray(answer) && answer.length === 0)) {
        alert('Please select at least one answer');
        return;
      }
    } else {
      // For other types, check if answer is not empty
      if (!answer || (typeof answer === 'string' && answer.trim() === '')) {
        alert('Please enter an answer');
        return;
      }
    }

    try {
      setSubmitting(true);

      // Format answer based on question type
      let formattedAnswer;
      if (currentQuestion.type === 'mcc') {
        formattedAnswer = Array.isArray(answer) ? answer : [answer];
      } else if (currentQuestion.type === 'mcq') {
        formattedAnswer = answer;
      } else {
        formattedAnswer = [answer];
      }

      const result = await submitAnswer(answerPaper.id, questionId, formattedAnswer);

      // Check if it's a code question with async evaluation
      if (result.status === 'running' && result.uid) {
        // Code question - start polling
        setEvaluatingQuestions((prev) => new Set([...prev, questionId]));
        setAttemptedQuestions((prev) => new Set([...prev, questionId]));
        pollForCodeResult(result.uid, questionId);

        // Loading indicator shown in UI
      } else {
        // Non-code question - immediate result
        handleImmediateResult(questionId, result);
      }
    } catch (err) {
      if (err.response?.status === 403 && err.response?.data?.error === 'Time is up!') {
         alert('Time is up! Your exam has ended.');
         navigate(`/student/submission/${answerPaper.id}`);
         return;
      }

      console.error('Failed to submit answer:', err);
      alert(err.response?.data?.error || 'Failed to submit answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuit = () => {
    setShowQuitConfirm(true);
  };

  const confirmQuit = async () => {
    try {
      await quitQuiz(answerPaper.id);
      navigate(`/answerpapers/${answerPaper.id}/submission`);
    } catch (err) {
      console.error('Failed to quit quiz:', err);
      navigate(`/answerpapers/${answerPaper.id}/submission`);
    }
  };

  const handleQuestionClick = (index) => {
    setCurrentQuestionIndex(index);
  };

  const handleErrorModalClose = () => {
    // Navigate back to the modules list
    navigate(`/courses/${courseId}/modules`);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading quiz...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error Modal
  if (error || !answerPaper) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        {/* Modal Overlay */}
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl transform scale-100 transition-all">
            <div className="text-center">
              <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <AiOutlineWarning className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-2xl font-bold mb-2">Unavailable</h3>
              <p className="text-gray-400 mb-8">
                {error || 'This quiz is currently unavailable.'}
              </p>
              <button
                onClick={handleErrorModalClose}
                className="w-full bg-white text-black py-3 rounded-xl font-bold hover:bg-gray-200 transition"
              >
                Back to Modules
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = answerPaper.questions[currentQuestionIndex];
  const totalQuestions = answerPaper.questions.length;
  const attemptedCount = attemptedQuestions.size;

  const renderQuestionInput = () => {
    if (!currentQuestion) return null;

    switch (currentQuestion.type) {
      case 'integer':
      case 'float':
      case 'string':
        return (
          <input
            type={currentQuestion.type === 'integer' ? 'number' : 'text'}
            className="w-full px-4 py-3 text-lg bg-white/5 border border-white/10 rounded-lg"
            placeholder={`Enter ${currentQuestion.type}...`}
            value={answers[currentQuestion.id] || ''}
            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
          />
        );

      case 'mcq':
        return (
          <div className="space-y-3">
            {currentQuestion.options && currentQuestion.options.map((option, idx) => (
              <label key={idx} className="flex items-center gap-3 p-4 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition">
                <input
                  type="radio"
                  name={`question-${currentQuestion.id}`}
                  value={option}
                  checked={answers[currentQuestion.id] === option}
                  onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                  className="w-4 h-4"
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        );

      case 'mcc':
        return (
          <div className="space-y-3">
            {currentQuestion.options && currentQuestion.options.map((option, idx) => (
              <label key={idx} className="flex items-center gap-3 p-4 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition">
                <input
                  type="checkbox"
                  checked={(answers[currentQuestion.id] || []).includes(option)}
                  onChange={(e) => {
                    const current = answers[currentQuestion.id] || [];
                    const updated = e.target.checked
                      ? [...current, option]
                      : current.filter((o) => o !== option);
                    handleAnswerChange(currentQuestion.id, updated);
                  }}
                  className="w-4 h-4"
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        );

      case 'code':
        return (
          <textarea
            className="w-full px-4 py-3 text-lg font-mono bg-white/5 border border-white/10 rounded-lg min-h-[300px]"
            placeholder="Write your code here..."
            value={answers[currentQuestion.id] || ''}
            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
          />
        );

      default:
        return (
          <textarea
            className="w-full px-4 py-3 text-lg bg-white/5 border border-white/10 rounded-lg min-h-[200px]"
            placeholder="Enter your answer..."
            value={answers[currentQuestion.id] || ''}
            onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
          />
        );
    }
  };

  return (
    <div className="flex min-h-screen relative grid-texture">
      <QuizSidebar
        currentQuestion={currentQuestionIndex + 1}
        totalQuestions={totalQuestions}
        attemptedQuestions={Array.from(attemptedQuestions).map((qId) => {
          const index = answerPaper.questions.findIndex((q) => q.id === qId);
          return index >= 0 ? index + 1 : 0;
        }).filter((n) => n > 0)}
        onQuestionClick={handleQuestionClick}
      />

      <main className="flex-1 flex flex-col">
        {/* Quit Confirmation Overlay */}
        {showQuitConfirm && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl">
              <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center bg-yellow-500/20 border border-yellow-500/30">
                  <AiOutlineWarning className="w-8 h-8 text-yellow-400" />
                </div>
                <p className="text-lg text-gray-300 mb-2">Your current answers are saved.</p>
                <h3 className="text-xl font-bold mb-2">Are you sure you want to quit?</h3>
                <p className="text-sm text-gray-400 mb-8">Be sure, as you won't be able to restart this exam.</p>
                <div className="flex justify-center gap-4">
                  <button
                    onClick={confirmQuit}
                    className="bg-red-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-red-700 transition flex items-center gap-2"
                  >
                    <FaTimes className="w-4 h-4" />
                    Yes, Quit
                  </button>
                  <button
                    onClick={() => setShowQuitConfirm(false)}
                    className="bg-white/10 text-white px-8 py-3 rounded-xl font-semibold hover:bg-white/20 transition flex items-center gap-2"
                  >
                    No, Continue
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Top Bar */}
        <header className="px-8 py-4 flex justify-end items-center border-b border-white/6 bg-gradient-to-b from-white/[0.01] to-transparent">
          <div className="flex items-center gap-4">
            <div className="card px-6 py-2 flex items-center gap-3">
              <FaClock className="w-5 h-5 text-indigo-400" />
              <span className="text-md font-mono font-bold">{formatTime(timeLeft)}</span>
            </div>
            <button
              onClick={handleQuit}
              className="bg-red-600 text-white text-md px-6 py-2 rounded-lg font-semibold hover:bg-red-700 transition inline-flex items-center"
            >
              Quit Exam
            </button>
          </div>
        </header>

        {/* Question Content */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-4xl">
            {/* Breadcrumb Navigation */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold">Quiz</h1>
              <p className="text-gray-400 text-sm mt-1">
                <Link to="/courses" className="hover:text-white transition">Courses</Link> /
                <Link to={`/courses/${courseId}/modules`} className="hover:text-white transition"> Course</Link> /
                <span className="text-white"> Quiz</span>
              </p>
            </div>

            {/* Question Header */}
            {currentQuestion && (
              <>
                <div className="mb-6">
                  <h2 className="text-3xl font-bold mb-4">
                    Question {currentQuestionIndex + 1} of {totalQuestions}
                  </h2>
                  <div className="mb-4">
                    <div
                      className="prose prose-invert max-w-none text-gray-300"
                      dangerouslySetInnerHTML={{ __html: currentQuestion.description || currentQuestion.summary }}
                    />
                  </div>

                  <div className="flex flex-wrap gap-4 mb-4">
                    {currentQuestion.language && (
                      <div className="text-sm px-4 py-2 rounded-lg bg-blue-500/10 border border-blue-500/30">
                        <span className="muted">Language:</span>
                        <span className="font-semibold text-blue-400 ml-1">{currentQuestion.language.toUpperCase()}</span>
                      </div>
                    )}
                    <div className="text-sm px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/30">
                      <span className="muted">Type:</span>
                      <span className="font-semibold text-purple-400 ml-1">{currentQuestion.type.toUpperCase()}</span>
                    </div>
                    <div className="text-sm px-4 py-2 rounded-lg bg-green-500/10 border border-green-500/30">
                      <span className="muted">Points:</span>
                      <span className="font-semibold text-green-400 ml-1">{currentQuestion.points || 0}</span>
                    </div>
                  </div>

                  <div className="rounded-lg px-4 py-3 text-sm font-medium bg-red-500/10 border border-red-500/30 text-red-300 flex items-center">
                    <AiOutlineWarning className="w-5 h-5 inline-block mr-2" />
                    LAST SUBMITTED ANSWER IS CONSIDERED FOR EVALUATION
                  </div>
                </div>

                {/* Question Body */}
                <div className="card p-8 mb-6">
                  <label className="block text-sm font-semibold mb-4 soft">
                    {currentQuestion.type === 'integer' ? 'Enter Integer:' :
                      currentQuestion.type === 'float' ? 'Enter Float:' :
                        currentQuestion.type === 'string' ? 'Enter String:' :
                          currentQuestion.type === 'code' ? 'Write Your Code:' :
                            currentQuestion.type === 'mcq' ? 'Select One Answer:' :
                              currentQuestion.type === 'mcc' ? 'Select All Correct Answers:' :
                                'Enter Your Answer:'}
                  </label>
                  {renderQuestionInput()}
                </div>

                {/* Code Evaluation Loading Indicator */}
                {evaluatingQuestions.has(currentQuestion.id) && (
                  <div className="mt-4 mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                      <div>
                        <p className="font-semibold">Evaluating your code...</p>
                        <p className="text-sm text-gray-400">This may take a few seconds. Please wait.</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Result Display — Hidden feedback mode:
                    - Non-code questions: neutral "Answer Submitted" (no correct/incorrect)
                    - Code questions with compilation/runtime errors: show error details as hints
                    - Code questions without errors: neutral "Answer Submitted"
                    To revert to showing correct/incorrect, restore the original block below.
                */}
                {questionResults[currentQuestion.id] && !evaluatingQuestions.has(currentQuestion.id) && (() => {
                  const result = questionResults[currentQuestion.id];
                  const isCodeQuestion = currentQuestion.type === 'code' || currentQuestion.type === 'upload';

                  // Check if code question has real errors (objects with error details, not just simple strings)
                  const hasRealCodeErrors = isCodeQuestion && !result.success && result.error && (
                    (Array.isArray(result.error) && result.error.length > 0 && typeof result.error[0] === 'object') ||
                    (typeof result.error === 'string' && result.error !== 'Incorrect answer')
                  );

                  if (hasRealCodeErrors) {
                    // Code question with real compilation/runtime errors — show error details as a hint
                    return (
                      <div className="mt-4 mb-6 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30">
                        <h4 className="font-bold mb-2 flex items-center gap-2">
                          <AiOutlineWarning className="text-amber-400" /> Code Error — Hint
                        </h4>
                        <div className="mt-2">
                          {renderErrorDisplay(result.error)}
                        </div>
                      </div>
                    );
                  }

                  // All other cases — neutral "Answer Submitted" message
                  return (
                    <div className="mt-4 mb-6 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                      <h4 className="font-bold mb-2 flex items-center gap-2">
                        <FaCheck className="text-blue-400" /> Answer Submitted
                      </h4>
                      <p className="text-sm text-gray-400">
                        Your answer has been recorded and will be evaluated.
                      </p>
                    </div>
                  );
                })()}

                {/* Action Buttons */}
                <div className="flex gap-4 flex-wrap">
                  <button
                    onClick={() => handleSubmitAnswer(currentQuestion.id)}
                    disabled={submitting || !answers[currentQuestion.id]}
                    className="bg-green-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-600 transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <FaCheck className="w-5 h-5" />
                    {submitting ? 'Submitting...' : 'Submit Answer'}
                  </button>
                  {currentQuestionIndex < totalQuestions - 1 && (
                    <button
                      onClick={() => setCurrentQuestionIndex(currentQuestionIndex + 1)}
                      className="bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-600 transition flex items-center gap-2"
                    >
                      Next Question
                      <FaArrowRight className="w-5 h-5" />
                    </button>
                  )}
                  {currentQuestionIndex > 0 && (
                    <button
                      onClick={() => setCurrentQuestionIndex(currentQuestionIndex - 1)}
                      className="bg-gray-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-gray-600 transition flex items-center gap-2"
                    >
                      Previous Question
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Quiz;
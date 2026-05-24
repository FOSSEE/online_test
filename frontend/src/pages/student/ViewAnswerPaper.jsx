import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useAnswerPaperStore from '../../store/student/answerPaperStore';
import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import { FaChevronLeft, FaUser, FaCalendar, FaCheckCircle, FaTimesCircle, FaClock, FaTrophy, FaPercent, FaClipboardList, FaBook, FaLayerGroup } from 'react-icons/fa';
const ViewAnswerPaper = () => {
  const { questionPaperId, courseId } = useParams();
  const navigate = useNavigate();

  const {
    fetchAnswerPaperData,
    quiz,
    courseName,
    moduleName,
    user,
    selectedPaper,
    selectedAttemptNumber,
    selectAttempt,
    getAvailableAttemptNumbers,
    loading,
    error,
    reset
  } = useAnswerPaperStore();

  useEffect(() => {
    if (questionPaperId && courseId) {
      fetchAnswerPaperData(questionPaperId, courseId);
    }

    // Cleanup when component unmounts
    return () => reset();
  }, [questionPaperId, courseId, fetchAnswerPaperData, reset]);

  const availableAttempts = getAvailableAttemptNumbers();

  // Loading and error states with proper layout
  if (loading) {
    return (
      <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-4 sm:p-8">
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-sm muted">Loading your answer paper details...</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-4 sm:p-8">
            <div className="bg-red-500/10 border-2 border-red-500/40 rounded-xl p-6 text-center">
              <p className="text-red-600 dark:text-red-400 font-semibold">{error}</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!selectedPaper) {
    return (
      <div className="flex flex-col md:flex-row min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-4 sm:p-8">
            <div className="card-strong p-6 rounded-xl border-2 border-[var(--border-strong)] text-center">
              <p className="muted">No attempt data found.</p>
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

          {/* Main Card */}
          <div className="space-y-4">
            <div className="card-strong p-5 sm:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
              {/* Header Section */}
              <div className="mb-6 pb-5 border-b-2 border-[var(--border-subtle)]">
                <div className="flex items-start gap-4 mb-4">
                  <button
                    onClick={() => navigate(-1)}
                    className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
                  >
                    <FaChevronLeft className="w-4 h-4" />
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-xl sm:text-2xl font-bold line-clamp-2">{quiz?.description || 'Answer Paper'}</h2>
                      <span className={`text-[10px] px-2.5 py-1 rounded-lg border-2 uppercase font-bold tracking-wider whitespace-nowrap ${quiz?.is_exercise
                          ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                          : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        }`}>
                        {quiz?.is_exercise ? 'Exercise' : 'Quiz'}
                      </span>
                      <span className=" hidden sm:inline text-[10px] px-2.5 py-1 rounded-lg border-2 uppercase font-bold tracking-wider whitespace-nowrap bg-red-orange/20 text-orange-400 border-orange-500/30">
                        Answerpaper
                      </span>
                      <span className="sm:hidden text-[10px] px-2.5 py-1 rounded-lg border-2 uppercase font-bold tracking-wider whitespace-nowrap bg-red-orange/20 text-orange-400 border-orange-500/30">
                        Paper
                      </span>

                    </div>
                    <div className="flex flex-wrap gap-4 text-xs muted">



                      {courseName && (
                        <div className="flex items-center gap-1.5">
                          <FaBook className="w-3.5 h-3.5" />
                          <span className="font-medium">{courseName}</span>
                        </div>
                      )}


                      {moduleName && (
                        <div className="flex items-center gap-1.5">
                          <FaLayerGroup className="w-3.5 h-3.5" />
                          <span className="font-medium">{moduleName}</span>
                        </div>
                      )}

                      <div className="flex items-center gap-1.5">
                        <FaUser className="w-3.5 h-3.5" />
                        <span className="font-medium">{user?.first_name} {user?.last_name} ({user?.username})</span>
                      </div>
                      {/*}
                      {selectedPaper.end_time && (
                        <div className="flex items-center gap-1.5">
                          <FaCalendar className="w-3 h-3" />
                          <span>{new Date(selectedPaper.end_time).toLocaleString()}</span>
                        </div>
                      )}
*/}
                    </div>
                  </div>
                </div>
                <p className="text-xs sm:text-sm muted">View your answers and performance for each attempt</p>
              </div>


              {/* Attempt Tabs */}
              {availableAttempts.length > 0 && (
                <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 sm:gap-4 my-6">
                  <div className="flex bg-[var(--input-bg)] p-1.5 rounded-xl overflow-x-auto scrollbar-hide border-2 border-[var(--border-strong)]  max-w-full lg:max-w-[50vw] xl:max-w-[75vw]">
                    {[...availableAttempts]
                      .sort((a, b) => a - b)
                      .map((attemptNum) => (
                        <button
                          key={attemptNum}
                          onClick={() => selectAttempt(attemptNum)}
                          className={`flex-1 sm:flex-initial flex-shrink-0 px-4 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 whitespace-nowrap ${attemptNum === selectedAttemptNumber
                              ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg'
                              : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--card-bg)]'
                            }`}
                        >
                          Attempt {attemptNum}
                        </button>
                      ))}
                  </div>
                </div>
              )}

              {/* Questions & Answers Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-bold flex items-center gap-2">
                    <FaCheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    Questions & Answers
                  </h3>

                </div>
                <div className="card-strong p-5 rounded-xl border-2 border-[var(--border-strong)] bg-[var(--surface)]">
                  <div className="flex items-center justify-between mb-4 pb-4 border-b-2 border-[var(--border-subtle)]">
                    <div>
                      <h3 className="text-base font-bold flex items-center gap-2 mb-2">
                        Attempt #{selectedAttemptNumber}
                      </h3>
                      <p className="text-sm text-[var(--text-muted)] font-medium">
                        Status: <span className={`font-semibold capitalize ${selectedPaper.status === 'completed'
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-orange-600 dark:text-orange-400'
                          }`}>{selectedPaper.status}</span>
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-base font-bold">
                        <span className="text-emerald-600 dark:text-emerald-400">{selectedPaper.marks_obtained}</span>
                        <span className="text-[var(--text-muted)]"> / {selectedPaper.total_marks}</span>
                      </p>
                      <p className="text-sm text-[var(--text-muted)] mt-1 font-semibold">{selectedPaper.percent}%</p>
                      {selectedPaper.end_time && (
                        <p className="sm:text-xs text-[10px] text-[var(--text-muted)] mt-2 font-medium">
                          <FaCalendar className="sm:w-3 sm:h-3 w-2.5 h-2.5 inline mr-1" />
                          {new Date(selectedPaper.end_time).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    {selectedPaper.questions.map((qData, index) => {
                      const isCorrect = qData.answer.correct;
                      const isSkipped = qData.answer.skipped;

                      return (
                        <div key={index} className="card p-4 sm:p-5  border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 bg-[var(--surface-2)]  transition-all duration-300 group hover:shadow-md hover:bg-white/[0.03] rounded-xl">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="font-semibold text-blue-600 dark:text-blue-400 mb-3 flex items-start gap-2">
                                <span className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-500/20 border-2 border-blue-500/30 flex items-center justify-center text-sm font-bold text-blue-600 dark:text-blue-400">
                                  {index + 1}
                                </span>
                                <span dangerouslySetInnerHTML={{ __html: qData.question.summary || qData.question.description }} />
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-[var(--text-secondary)] mb-3 ml-8" dangerouslySetInnerHTML={{ __html: qData.question.description }} />

                          <div className="ml-9 space-y-3 text-sm">
                            <div className="flex items-start gap-2">
                              <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Answer:</span>
                              <span className={`${isSkipped
                                  ? 'text-yellow-600 dark:text-yellow-400 font-semibold italic'
                                  : qData.answer?.answer_content
                                    ? 'text-[var(--text-primary)] font-medium'
                                    : 'text-red-600 dark:text-red-400 font-semibold'
                                }`}>
                                {isSkipped ? 'Question skipped' : (qData.answer?.answer_content || 'Not answered')}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Marks:</span>
                              <span>
                                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{qData.answer?.marks ?? 0}</span>
                                <span className="text-[var(--text-muted)] font-semibold"> / {qData.question.points}</span>
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-[var(--text-muted)] min-w-[70px]">Status:</span>
                              {isSkipped ? (
                                <span className="text-yellow-600 dark:text-yellow-400 font-semibold">Skipped</span>
                              ) : isCorrect ? (
                                <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 font-semibold">
                                  <FaCheckCircle className="w-3.5 h-3.5" /> Correct
                                </span>
                              ) : (
                                <span className="text-red-600 dark:text-red-400 flex items-center gap-1.5 font-semibold">
                                  <FaTimesCircle className="w-3.5 h-3.5" /> Incorrect
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
};

export default ViewAnswerPaper;
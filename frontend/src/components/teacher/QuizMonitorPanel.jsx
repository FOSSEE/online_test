import React, { useEffect, useState, useRef } from "react";
import { FaChevronLeft, FaUser, FaListOl, FaCalendar, FaDownload, FaUpload, FaFileCsv, FaTimes, FaLayerGroup, FaBook } from "react-icons/fa";
import useMonitorStore from "../../store/quizMonitorStore";
import QuizStatisticsPanel from "./QuizStatisticsPanel";


const formatTimeLeft = secs => {
  if (secs < 0) secs = 0;
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = Math.floor(secs % 60);
  return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
};

const QuizMonitorPanel = ({ quiz, course, onBack }) => {
  const {
    loading,
    error,
    result,
    monitorQuiz,
    downloadCSV,
    extendTime,
    allowSpecial,
    reset,
  } = useMonitorStore();

  const [selectedAttempt, setSelectedAttempt] = useState(null);
  const [timeExtension, setTimeExtension] = useState({});
  const attempts = result?.attempt_numbers?.map(num => ({ attempt_number: num, id: num })) || [];

  const [showStatistics, setShowStatistics] = useState(false);
  const [statsData, setStatsData] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsAttempt, setStatsAttempt] = useState(null);
  const fetchQuizStatistics = useMonitorStore(state => state.fetchQuizStatistics);

  // --- Time left state ---
  const [timeLeft, setTimeLeft] = useState({});
  const timerRef = useRef();

  useEffect(() => {
    // Clear timer on unmount
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      reset();
    };
  }, [reset]);

  useEffect(() => {
    if (quiz && course) {
      monitorQuiz(quiz.id, course.course_id);
    }
  }, [quiz, course, monitorQuiz]);

  useEffect(() => {
    if (attempts.length > 0 && !selectedAttempt) {
      const first = attempts.find(a => a.attempt_number === 1) || attempts[0];
      setSelectedAttempt(first);
    }
  }, [attempts, selectedAttempt]);

  useEffect(() => {
    if (quiz && course && selectedAttempt) {
      monitorQuiz(quiz.id, course.course_id, selectedAttempt.attempt_number);
    }
  }, [quiz, course, selectedAttempt, monitorQuiz]);

  // --- Countdown logic ---
  useEffect(() => {
    if (!result?.papers) return;
    const calcTimeLeft = () => {
      const now = new Date();
      const newTimeLeft = {};
      result.papers.forEach(paper => {
        let end = new Date(paper.end_time);
        if (isNaN(end.getTime())) {
          end = new Date(paper.end_time.replace(/\.\d+/, ""));
        }
        const diff = Math.abs(Math.floor((end - now) / 1000));
        console.log("Paper ID:", paper.id, "end_time:", paper.end_time, "Parsed end:", end, "Now:", now, "Diff:", diff);
        newTimeLeft[paper.id] = diff;
      });
      setTimeLeft(newTimeLeft);
    };
    calcTimeLeft();
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(calcTimeLeft, 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [result?.papers]);

  const [marksCSV, setMarksCSV] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleUploadCSV = async () => {
    if (!marksCSV) return;
    setUploading(true);
    setUploadError(null);
    try {
      await useMonitorStore.getState().uploadCSV(
        course.course_id,
        result?.questionpaper_id || quiz.id,
        marksCSV
      );
      setMarksCSV(null);
      monitorQuiz(quiz.id, course.course_id, selectedAttempt.attempt_number);
    } catch (err) {
      setUploadError("Failed to upload CSV. Please check the file and try again.");
    }
    setUploading(false);
  };

  const handleDownloadCSV = () => {
    downloadCSV(course.course_id, quiz.id, selectedAttempt?.attempt_number || 1);
  };

  const handleExtendTime = async (paperId) => {
    const extraTime = timeExtension[paperId];
    if (!extraTime) return;
    await extendTime(paperId, extraTime);
    setTimeExtension(prev => ({ ...prev, [paperId]: "" }));
    monitorQuiz(quiz.id, course.course_id, selectedAttempt.attempt_number);
  };

  const handleAllowSpecial = async (userId) => {
    try {
      const res = await allowSpecial(userId, course.course_id, quiz.id);
      alert(res?.message || "Special attempt allowed successfully.");
      monitorQuiz(quiz.id, course.course_id, selectedAttempt.attempt_number);
    } catch (err) {
      alert(
        err?.response?.data?.message ||
        err?.message ||
        "Failed to allow special attempt."
      );
    }
  };


  const handleShowStatistics = async () => {
    if (!quiz || !course || !selectedAttempt) return;
    setStatsLoading(true);
    await fetchQuizStatistics(result?.questionpaper_id || quiz.id, course.course_id, selectedAttempt.attempt_number);
    setStatsData(useMonitorStore.getState().result);
    setStatsAttempt(selectedAttempt);
    setShowStatistics(true);
    setStatsLoading(false);
  };

  const handleBackToMonitor = () => {
    setShowStatistics(false);
    setStatsData(null);
    setStatsAttempt(null);
    // Re-fetch monitor data for the selected attempt
    if (quiz && course && selectedAttempt) {
      monitorQuiz(quiz.id, course.course_id, selectedAttempt.attempt_number);
    }
  };

  // Handler to change attempt in statistics panel
  const handleStatsAttemptChange = async (attempt) => {
    setStatsLoading(true);
    setStatsAttempt(attempt);
    await fetchQuizStatistics(result?.questionpaper_id || quiz.id, course.course_id, attempt.attempt_number);
    setStatsData(useMonitorStore.getState().result);
    setStatsLoading(false);
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
              <div className="flex items-center gap-2">
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
                  <span className="font-medium">{course.course_name || course.name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <FaLayerGroup className="w-3 h-3" />
                  <span className="font-medium">{quiz.module_name}</span>
                </div>
                {quiz.start_date && (
                  <div className="flex items-center gap-1.5">
                    <FaCalendar className="w-3 h-3" />
                    <span className="font-medium">{new Date(quiz.start_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          <p className="text-sm muted">Monitor quiz progress, download statistics, and view live data.</p>
        </div>

        {/* Details and Actions */}
        {showStatistics ? (
          <QuizStatisticsPanel
            statsData={statsData}
            onBack={handleBackToMonitor}
            attempts={attempts}
            currentAttempt={statsAttempt?.attempt_number}
            onAttemptChange={handleStatsAttemptChange}
            loading={statsLoading}
          />
        ) : (
          <>
            {result && result.stats && (
              <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
                {/* Details Card */}
                <div className="flex-1">
                  <h3 className="text-sm sm:text-base font-bold flex items-center gap-2 mb-3">
                    Stats :
                  </h3>
                  <div className="card-strong p-5 rounded-xl border-2 border-[var(--border-strong)]">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="text-[var(--text-muted)] text-center mb-2 font-semibold">Total Papers</div>
                        <div className="font-bold text-[var(--text-primary)] text-center text-lg">{result.stats.total_papers}</div>
                      </div>
                      <div>
                        <div className="text-[var(--text-muted)] text-center mb-2 font-semibold">Completed</div>
                        <div className="font-bold text-emerald-600 dark:text-emerald-400 text-center text-lg">{result.stats.completed_papers}</div>
                      </div>
                      <div>
                        <div className="text-[var(--text-muted)] text-center mb-2 font-semibold">In Progress</div>
                        <div className="font-bold text-yellow-600 dark:text-yellow-400 text-center text-lg">{result.stats.inprogress_papers}</div>
                      </div>
                      <div>
                        <div className="text-[var(--text-muted)] text-center mb-2 font-semibold">Questions</div>
                        <div className="font-bold text-blue-600 dark:text-blue-400 text-center text-lg">{result.stats.questions_count}</div>
                      </div>
                    </div>
                  </div>
                </div>
                {/* Actions */}
                <div className="flex flex-row gap-2 md:flex-col md:gap-3 mt-2 md:mt-0">
                  <button
                    className="w-1/2 lg:w-full text-white px-3 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold bg-blue-500/80 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap flex-shrink-0 hover:bg-blue-600 flex items-center gap-2"
                    onClick={handleDownloadCSV}
                  >
                    <FaDownload className="w-4 h-4" />
                    Download CSV
                  </button>
                  <button
                    className="w-1/2 lg:w-full text-center text-white px-3 sm:px-6 py-2 sm:py-2.5 rounded-lg font-semibold bg-green-500/80 active:scale-95 transition text-xs sm:text-sm whitespace-nowrap flex-shrink-0 hover:bg-green-600 flex items-center gap-2"
                    onClick={handleShowStatistics}
                    disabled={!selectedAttempt}
                  >
                    <FaListOl className="w-4 h-4" />
                    {`Statistics (# ${selectedAttempt?.attempt_number || ""})`}
                  </button>
                </div>
              </div>
            )}

            <div className="relative overflow-hidden bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-xl p-5 border-2 border-purple-500/30 mb-6">
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl"></div>
              <div className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-500/20 border-2 border-purple-500/30 flex items-center justify-center">
                    <FaFileCsv className="text-emerald-600 dark:text-emerald-400 w-6 h-6" />
                  </div>
                  <div>
                    <label className="text-base font-bold text-[var(--text-primary)] block">Upload Marks CSV</label>
                    <p className="text-sm text-[var(--text-muted)] font-medium">Upload a CSV file to update marks for this quiz</p>
                  </div>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="file"
                      accept=".csv"
                      id="marks-csv-upload"
                      className="hidden"
                      onChange={e => setMarksCSV(e.target.files[0])}
                    />
                    <label
                      htmlFor="marks-csv-upload"
                      className="flex items-center justify-center gap-2 px-5 py-2.5 border-2 border-dashed border-purple-500/40 rounded-xl cursor-pointer hover:border-purple-500/60 hover:bg-purple-500/10 transition-all duration-200"
                    >
                      <FaUpload className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                      <span className="text-sm font-semibold text-[var(--text-primary)]">{marksCSV ? marksCSV.name : "Choose CSV file"}</span>
                    </label>
                    {marksCSV && (
                      <button
                        type="button"
                        className="ml-1 px-3 py-2 rounded-lg bg-red-500/80 text-white text-sm font-semibold hover:bg-red-600 transition active:scale-95"
                        onClick={() => setMarksCSV(null)}
                        title="Remove selected file"
                      >
                        Remove
                      </button>
                    )}
                    {uploadError && <span className="text-red-600 dark:text-red-400 text-sm ml-2 font-semibold">{uploadError}</span>}
                  </div>
                  <button
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white font-bold hover:from-emerald-700 hover:to-green-700 transition active:scale-95 disabled:opacity-60"
                    onClick={handleUploadCSV}
                    disabled={!marksCSV || uploading}
                  >
                    {uploading ? "Uploading..." : "Upload"}
                  </button>
                </div>
              </div>
            </div>

            {attempts.length > 0 && (
              <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 sm:gap-4 my-6">
                <div className="flex bg-[var(--input-bg)] p-1.5 rounded-xl overflow-x-auto scrollbar-hide border-2 border-[var(--border-strong)] max-w-full lg:max-w-[50vw] xl:max-w-[75vw]">
                  {[...attempts]
                    .sort((a, b) => a.attempt_number - b.attempt_number)
                    .map((attempt) => (
                      <button
                        key={attempt.id}
                        onClick={() => setSelectedAttempt(attempt)}
                        className={`flex-1 sm:flex-initial flex-shrink-0 px-4 py-2.5 rounded-lg text-sm font-bold transition-all duration-300 whitespace-nowrap ${selectedAttempt?.id === attempt.id
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

            {/* Content Area */}
            <div className="space-y-4">
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-sm text-muted">Loading monitoring data...</p>
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-500/10 border-2 border-red-500/40 rounded-xl p-4 text-red-600 dark:text-red-400 font-semibold">
                  {error}
                </div>
              )}

              {/* User Table */}
              {result && result.papers && (
                <div>
                  <h3 className="text-base sm:text-lg font-bold mb-4 flex items-center gap-2">
                    <FaUser className="w-5 h-5" />
                    Attempted Users
                  </h3>
                  <div className="overflow-x-auto rounded-2xl border-2 border-[var(--border-strong)]">
                    <table className="min-w-full card-strong  text-sm">
                      <thead>
                        <tr className="bg-blue-500/10 border-b-2 border-[var(--border-strong)]">
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">SR NO.</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">NAME</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">ROLL NO</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">MARKS</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">QUESTIONS ATTEMPTED</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">TIME LEFT</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">STATUS</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">TIME EXTENSION</th>
                          <th className="px-4 py-3 text-blue-600 dark:text-blue-400 font-bold">SPECIAL ATTEMPT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.papers.map((paper, idx) => (
                          <tr key={paper.id} className="border-b border-[var(--border-subtle)] hover:bg-[var(--input-bg)] transition-colors">
                            <td className="px-4 py-3 text-center font-semibold">{idx + 1}</td>
                            <td className="px-4 py-3 items-center text-center font-semibold">
                              {paper.user.first_name} {paper.user.last_name}
                            </td>
                            <td className="px-4 py-3 text-center font-medium">{paper.user.roll_number}</td>
                            <td className="px-4 py-3 text-center font-bold text-blue-600 dark:text-blue-400">{paper.marks_obtained}</td>
                            <td className="px-4 py-3 text-center font-medium">{paper.questions_attempted_count} out of {result.stats.questions_count}</td>
                            <td className="px-4 py-3 text-center font-semibold">
                              {timeLeft[paper.id] > 0
                                ? <span className="text-emerald-600 dark:text-emerald-400">{formatTimeLeft(timeLeft[paper.id])}</span>
                                : <span className="text-red-600 dark:text-red-400 font-bold">EXPIRED</span>
                              }
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-3 py-1.5 rounded-lg font-bold text-xs border-2 ${paper.status === "completed"
                                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                                : "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30"
                                }`}>
                                {paper.status.toUpperCase()}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <div className="flex items-center gap-2 text-center justify-center">
                                <input
                                  type="text"
                                  className="w-20 px-3 py-1.5 rounded-lg bg-[var(--input-bg)] border-2 border-[var(--border-strong)] text-emerald-600 dark:text-emerald-400 font-bold focus:outline-none focus:border-blue-500/50 transition"
                                  value={timeExtension[paper.id] || ""}
                                  onChange={e => setTimeExtension(prev => ({ ...prev, [paper.id]: e.target.value }))}
                                  placeholder="Time"
                                />
                                <button
                                  className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white font-bold hover:from-emerald-700 hover:to-green-700 transition active:scale-95"
                                  onClick={() => handleExtendTime(paper.id)}
                                >+</button>
                              </div>
                            </td>
                            <td className="px-4 py-3 justify-center text-center">
                              <button
                                className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-green-600 text-white font-bold hover:from-emerald-700 hover:to-green-700 transition active:scale-95"
                                onClick={() => handleAllowSpecial(paper.user.id)}
                              >
                                Allow
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
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
    </div>
  );
};

export default QuizMonitorPanel;
import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import {
  FaPlay,
  FaLayerGroup,
  FaBook,
  FaArrowRight,
  FaCheck,
  FaCheckCircle,
  FaChevronLeft,
  FaFileAlt,
  FaDownload,
  FaVideo,
  FaClock,
  FaBookmark,
  FaUser,
  FaListOl
} from 'react-icons/fa';
import Sidebar from '../../components/layout/Sidebar';
import Header from '../../components/layout/Header';
import { fetchLessonDetail, markLessonComplete } from '../../api/api';
import useManageCourseStore from '../../store/student/manageCourseStore';

const Lesson = () => {
  const { lessonId } = useParams();
  const navigate = useNavigate();
  const { loadCourseModules } = useManageCourseStore();

  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completing, setCompleting] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (lessonId) {
      loadLesson();
    }
  }, [lessonId]);

  useEffect(() => {
    // Load modules for progress tracking
    if (lesson && lesson.course_id) {
      loadCourseModules(lesson.course_id);
    }
  }, [lesson]);

  const loadLesson = async () => {
    try {
      setLoading(true);
      const data = await fetchLessonDetail(lessonId);
      setLesson(data);
      setCompleted(data.is_completed);
      setError(null);
    } catch (err) {
      console.error('Failed to load lesson:', err);
      setError('Failed to load lesson');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      setCompleting(true);
      await markLessonComplete(lessonId);
      setCompleted(true);
      // Reload modules to update progress
      if (lesson && lesson.course_id) {
        loadCourseModules(lesson.course_id);
      }
    } catch (err) {
      console.error('Failed to mark lesson as complete:', err);
      alert('Failed to mark lesson as complete');
    } finally {
      setCompleting(false);
    }
  };

  const getVideoEmbedUrl = (videoUrl) => {
    if (!videoUrl) return null;

    // Check if it's a YouTube URL
    if (videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be')) {
      const youtubeRegex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
      const match = videoUrl.match(youtubeRegex);
      if (match) {
        return `https://www.youtube.com/embed/${match[1]}`;
      }
    }

    // Check if it's a Vimeo URL
    if (videoUrl.includes('vimeo.com')) {
      const vimeoRegex = /(?:vimeo\.com\/)(\d+)/;
      const match = videoUrl.match(vimeoRegex);
      if (match) {
        return `https://player.vimeo.com/video/${match[1]}`;
      }
    }

    // If it's already an embed URL or just an ID, use it directly
    if (videoUrl.includes('embed') || videoUrl.length < 20) {
      return videoUrl.includes('http') ? videoUrl : `https://www.youtube.com/embed/${videoUrl}`;
    }

    return videoUrl;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-8 flex items-center justify-center h-96">
            <div className="text-center">
              <div className="relative w-16 h-16 mb-4 mx-auto">
                <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-t-blue-500 border-r-cyan-400 animate-spin"></div>
              </div>
              <p className="text-[var(--text-muted)] text-sm font-medium">Loading lesson...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="flex min-h-screen relative grid-texture">
        <Sidebar />
        <main className="flex-1">
          <Header isAuth />
          <div className="p-4 sm:p-8">
            <div className="max-w-3xl mx-auto text-center py-16">
              <div className="p-8 rounded-2xl bg-gradient-to-br from-red-500/10 to-red-600/5 border-2 border-red-500/30 shadow-xl">
                <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6 border-2 border-red-500/30">
                  <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-red-600 dark:text-red-400 font-bold text-xl mb-6">{error || 'Lesson not found'}</p>
                <Link
                  to="/courses"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl"
                >
                  <FaChevronLeft className="w-4 h-4" />
                  Back to Courses
                </Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const videoEmbedUrl = getVideoEmbedUrl(lesson.video_url);
  const hasVideo = lesson.video_url || lesson.video_file;

  const handleBack = () => {
    if (lesson.course_id) {
      navigate(`/courses/${lesson.course_id}/manage`);
    } else {
      navigate('/courses');
    }
  };

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

          {/* Lesson Container */}
          <div className="space-y-4">
            {/* Main Card */}
            <div className="card-strong p-5 sm:p-6 min-h-[600px] border-2 border-[var(--border-strong)] shadow-lg rounded-2xl">
              {/* Header Section */}
              <div className="mb-6 pb-5 border-b-2 border-[var(--border-subtle)]">
                <div className="flex items-start gap-4 mb-4">
                  <button
                    onClick={handleBack}
                    className="w-10 h-10 rounded-xl bg-[var(--input-bg)] border-2 border-[var(--border-strong)] flex items-center justify-center hover:border-blue-500/40 hover:bg-blue-500/5 transition-all duration-300 flex-shrink-0 active:scale-95"
                  >
                    <FaChevronLeft className="w-4 h-4" />
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-xl sm:text-2xl font-bold line-clamp-2">{lesson.name}</h2>
                      <span className="text-[10px] px-2.5 py-1 rounded-lg border-2 uppercase font-bold tracking-wider whitespace-nowrap bg-cyan-500/20 text-cyan-400 border-cyan-500/30">
                        Lesson
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-4 text-xs muted">
                      <div className="flex items-center gap-1.5">
                        <FaBook className="w-3.5 h-3.5" />
                        <span className="font-medium">{lesson.course_name}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <FaLayerGroup className="w-3.5 h-3.5" />
                        <span className="font-medium">{lesson.module_name}</span>
                      </div>
                      {completed && (
                        <div className="flex items-center gap-1.5 text-emerald-400">
                          <FaCheckCircle className="w-3.5 h-3.5" />
                          <span className="font-medium">Completed</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-sm muted">Watch the videos, read the attached files to understand the concept better.</p>
              </div>

              {/* Video Section */}
              {hasVideo && (
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <FaVideo className="w-6 h-6 sm:w-7 sm:h-7 text-cyan-400" />
                    <h3 className="text-lg font-bold">Video Content</h3>
                  </div>

                  {/* Video File */}
                  {lesson.video_file && (
                    <div className="mb-4">
                      {lesson.video_file && videoEmbedUrl && (
                        <p className="text-sm font-semibold mb-2 text-[var(--text-muted)]">
                          Uploaded Video
                        </p>
                      )}
                      <div className="aspect-video rounded-xl overflow-hidden shadow-xl border-2 border-[var(--border-color)]">
                        <video
                          className="w-full h-full bg-black"
                          controls
                          controlsList="nodownload"
                          preload="metadata"
                        >
                          <source src={lesson.video_file} type="video/mp4" />
                          <source src={lesson.video_file} type="video/webm" />
                          <source src={lesson.video_file} type="video/ogg" />
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    </div>
                  )}

                  {/* Video URL (YouTube/Vimeo) */}
                  {videoEmbedUrl && (
                    <div className="mb-4">
                      {lesson.video_file && videoEmbedUrl && (
                        <p className="text-sm font-semibold mb-2 text-[var(--text-muted)]">
                          External Video
                        </p>
                      )}
                      <div className="aspect-video rounded-xl overflow-hidden shadow-xl border-2 border-[var(--border-color)]">
                        <iframe
                          className="w-full h-full"
                          src={videoEmbedUrl}
                          title={lesson.name}
                          frameBorder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                          allowFullScreen
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Lesson Description */}
              {lesson.description && (
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    
                    <h3 className="text-lg font-bold">Lesson Description</h3>
                  </div>
                  <div
                    className="prose prose-invert max-w-none text-sm sm:text-base leading-relaxed p-4 sm:p-5 bg-[var(--input-bg)] border-2 border-[var(--border-color)] rounded-xl"
                    dangerouslySetInnerHTML={{ __html: lesson.html_data || lesson.description }}
                  />
                </div>
              )}

              {/* Attached Files */}
              {lesson.files && lesson.files.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <h3 className="text-lg font-bold">Attached Files</h3>
                    <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-amber-500/15 text-amber-600 dark:text-amber-400 border-2 border-amber-500/30">
                      {lesson.files.length} {lesson.files.length === 1 ? 'File' : 'Files'}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {lesson.files.map((file, index) => {
                      const fileUrl = file.file || file.url || file.name;
                      const fileName = file.name || file.file_name || `File ${index + 1}`;

                      return (
                        <a
                          key={file.id || index}
                          href={fileUrl}
                          download={fileName}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-3 p-4 bg-[var(--input-bg)] border-2 border-[var(--border-color)] rounded-xl hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group shadow-md hover:shadow-lg cursor-pointer"
                        >
                          <div className="w-12 h-12 rounded-xl bg-blue-500/10 border-2 border-blue-500/30 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500/20 group-hover:scale-110 transition-all">
                            <FaFileAlt className="w-6 h-6 text-blue-500" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <span className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-500 transition-colors block truncate">
                              {fileName}
                            </span>
                            <span className="text-xs text-[var(--text-muted)]">Click to download</span>
                          </div>
                          <FaDownload className="w-4 h-4 text-[var(--text-muted)] group-hover:text-blue-500 transition-colors flex-shrink-0" />
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Mark as Complete Button */}
              {!completed && (
                <div className="pt-5 border-t-2 border-[var(--border-subtle)]">
                  <button
                    onClick={handleComplete}
                    disabled={completing}
                    className="w-full sm:w-auto px-6 py-3 sm:px-8 sm:py-3.5 rounded-xl font-bold text-sm sm:text-base transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-emerald-600 to-green-500 hover:from-emerald-500 hover:to-green-400 text-white shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:scale-105 border-2 border-emerald-400/30"
                  >
                    {completing ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Completing...</span>
                      </>
                    ) : (
                      <>
                        <FaCheck className="w-4 h-4 sm:w-5 sm:h-5" />
                        <span>Mark as Complete</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Completed Message */}
              {completed && (
                <div className="pt-5 border-t-2 border-[var(--border-subtle)]">
                  <div className="flex items-center gap-3 p-4 sm:p-5 bg-emerald-500/10 border-2 border-emerald-500/30 rounded-xl">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                      <FaCheckCircle className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-bold text-emerald-400 mb-1">Lesson Completed!</p>
                      <p className="text-xs muted">Great job! You've completed this lesson.</p>
                    </div>
                    <Link
                      to={lesson.course_id ? `/courses/${lesson.course_id}/manage` : "/courses"}
                      className="px-4 py-2 rounded-lg font-semibold text-sm transition-all bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/30 hover:bg-emerald-500/30 hover:scale-105"
                    >
                      Continue
                      <FaArrowRight className="inline ml-2 w-3 h-3" />
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Lesson;

import React, { useEffect, useState } from 'react';
import useStudentForumStore from '../../store/student/forumStore';
import useManageCourseStore from '../../store/student/manageCourseStore';
import { FaTimes, FaPaperPlane, FaComments, FaEllipsisV, FaTrash, FaBook, FaVideo, FaUser, FaCalendar } from 'react-icons/fa';

export default function CourseDiscussion({ courseId, showAddPostModal, setShowAddPostModal, closeCreatePost }) {
  const {
    coursePosts,
    lessonPosts,
    comments,
    loadCoursePosts,
    loadLessonPosts,
    loadCourseComments,
    addCoursePost,
    deleteCoursePost,
    addCourseComment,
    clearComments,
    deleteCourseComment,
    loadLessonComments,
    addLessonComment,
    deleteLessonComment,
  } = useStudentForumStore();

  const { activeForumTab, setActiveForumTab } = useManageCourseStore();

  const [selectedPostId, setSelectedPostId] = useState(null);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  const [showAddCommentModal, setShowAddCommentModal] = useState(false);

  useEffect(() => {
    if (courseId) {
      if (activeForumTab === 'Course Forum') {
        loadCoursePosts(courseId);
      } else {
        loadLessonPosts(courseId);
      }
      clearComments();
      setSelectedPostId(null);
    }
  }, [courseId, activeForumTab, loadCoursePosts, loadLessonPosts, clearComments]);

  const posts = activeForumTab === 'Course Forum' ? coursePosts : lessonPosts;

  const handleShowComments = (post) => {
    if (selectedPostId === post.id) {
      setSelectedPostId(null);
      clearComments();
    } else {
      setSelectedPostId(post.id);
      if (activeForumTab === 'Course Forum') {
        loadCourseComments(courseId, post.id);
      } else {
        // use target_id as lessonId for lesson posts
        loadLessonComments(courseId, post.target_id);
      }
    }
  };

  // Add Post (only for Course Forum)
  const handleAddPost = async (postData) => {
    let formData;
    if (postData instanceof FormData) {
      formData = postData;
    } else {
      formData = new FormData();
      formData.append('title', postData.title);
      formData.append('description', postData.description);
      formData.append('anonymous', postData.anonymous);
      if (postData.image) {
        formData.append('image', postData.image);
      }
    }
    await addCoursePost(courseId, formData);
    await loadCoursePosts(courseId);
    setShowAddPostModal(false);
  };

  // Delete Post (only for Course Forum posts owned by student)
  const handleDelete = async (post) => {
    setActionMenuOpen(null);

    if (window.confirm(`Are you sure you want to delete the post "${post.title}"?`)) {
      await deleteCoursePost(courseId, post.id);

      if (selectedPostId === post.id) {
        setSelectedPostId(null);
        clearComments();
      }
    }
  };

  // Add Comment
  const handleAddComment = async (commentData) => {
    if (activeForumTab === 'Course Forum') {
      await addCourseComment(courseId, selectedPostId, commentData);
    } else {
      // Find the lessonId (target_id) from the selected post
      const post = posts.find((p) => p.id === selectedPostId);
      if (post && post.target_id) {
        await addLessonComment(courseId, post.target_id, commentData);
      }
    }
    setShowAddCommentModal(false);
  };

  // Delete Comment
  const handleDeleteComment = async (comment) => {
    if (window.confirm('Are you sure you want to delete this comment?')) {
      if (activeForumTab === 'Course Forum') {
        await deleteCourseComment(courseId, selectedPostId, comment.id);
      } else {
        // Find the lessonId (target_id) from the selected post
        const post = posts.find((p) => p.id === selectedPostId);
        if (post && post.target_id) {
          await deleteLessonComment(courseId, post.target_id, comment.id);
        }
      }
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/15 to-blue-500/15 border-2 border-cyan-500/30 flex items-center justify-center">
          <FaComments className="w-5 h-5 text-cyan-400" />
        </div>
        <div>
          <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">Discussion Forum</h3>
          <p className="text-xs muted">Join the conversation</p>
        </div>
      </div>

      {/* Add Post Modal (Only for Course Forum) */}
      {showAddPostModal && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-1 sm:px-2">
          <div className="card-strong w-full max-w-full sm:max-w-2xl p-2 sm:p-6 relative rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto">
            <button
              className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border border-[var(--border-color)] bg-[var(--input-bg)] hover:bg-white/10 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
              onClick={closeCreatePost}
              aria-label="Close"
            >
              <FaTimes />
            </button>
            <div className="flex flex-col sm:flex-row items-center gap-4 mb-4 sm:mt-0">
              <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <FaPaperPlane className="w-7 h-7 sm:w-8 sm:h-8 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg sm:text-2xl font-bold mb-1 line-clamp-1">
                  Create New Post
                </h2>
                <p className="text-xs sm:text-sm muted line-clamp-2">
                  Ask a question or share something with the class.
                </p>
              </div>
            </div>
            <form
              onSubmit={async e => {
                e.preventDefault();
                const formData = new FormData(e.target);
                formData.set('anonymous', formData.get('anonymous') ? 'true' : 'false');
                await handleAddPost(formData);
                closeCreatePost();
              }}
              className="space-y-4 mt-2"
            >
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium mb-1" htmlFor="post-title">Title:</label>
                <input
                  className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm focus-visible:outline-none"
                  name="title"
                  id="post-title"
                  placeholder="Post Title *"
                  required
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium mb-1" htmlFor="post-description">Description:</label>
                <textarea
                  className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm focus-visible:outline-none"
                  name="description"
                  id="post-description"
                  placeholder="Description"
                  rows={6}
                  required
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium mb-1" htmlFor="post-image">Image (Optional):</label>
                <input
                  type="file"
                  name="image"
                  id="post-image"
                  accept="image/*"
                  className="input"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="anonymous"
                  id="post-anonymous"
                  className="toggle-checkbox"
                />
                <label htmlFor="post-anonymous" className="text-sm">Post Anonymously</label>
              </div>
              <div className="flex gap-2 justify-end mt-6 flex-wrap">
                <button
                  type="button"
                  className="px-5 py-2.5 rounded-xl border-2 border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] hover:border-[var(--border-strong)] font-bold transition-all duration-300 shadow-md"
                  onClick={closeCreatePost}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white font-bold transition-all duration-300 shadow-xl shadow-blue-600/30 hover:shadow-2xl hover:shadow-blue-600/40 border-2 border-blue-500/50 active:scale-95 disabled:opacity-60"
                >
                  Create Post
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Forum Tabs */}
      <div className="w-full sm:w-max overflow-x-auto scrollbar-thin mb-6">
        <div className="flex bg-[var(--input-bg)] border border-[var(--border-subtle)] sm:border-2 p-0.5 sm:p-1 rounded-xl min-w-[280px] sm:min-w-0 w-full sm:w-fit gap-1 sm:gap-2 shadow-inner">
          {['Course Forum', 'Lesson Forum'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveForumTab(tab)}
              className={`flex-1 sm:flex-none px-2 py-1.5 sm:px-4 sm:py-2 rounded-lg text-[11px] sm:text-sm font-bold transition-all duration-300 whitespace-nowrap ${activeForumTab === tab
                ? 'bg-gradient-to-r from-cyan-600 to-blue-500 text-white shadow-lg shadow-cyan-600/30 sm:scale-105 border border-cyan-400/50 sm:border-2'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)] border border-transparent sm:border-2'
                }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Posts List */}
      <div className="p-3 sm:p-4 bg-[var(--surface)] rounded-xl border-2 border-[var(--border-strong)] mt-2 space-y-8">
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              {activeForumTab === 'Course Forum' ? (
                <FaBook className="text-blue-400 w-4 h-4" />
              ) : (
                <FaVideo className="text-blue-400 w-4 h-4" />
              )}
            </div>
            <h3 className="text-base sm:text-lg font-bold text-[var(--text-primary)]">
              {activeForumTab === 'Course Forum' ? 'Course Discussions' : 'Lesson Discussions'}
              <span className="ml-2 text-blue-500 dark:text-blue-400">({posts.length})</span>
            </h3>
          </div>
          {posts.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed border-[var(--border-color)] rounded-xl bg-[var(--input-bg)]">
              <div className="mb-4 p-4 bg-blue-500/10 rounded-full w-16 h-16 mx-auto flex items-center justify-center">
                {activeForumTab === 'Course Forum' ? (
                  <FaBook className="text-blue-400 w-8 h-8" />
                ) : (
                  <FaVideo className="text-blue-400 w-8 h-8" />
                )}
              </div>
              <p className="text-[var(--text-primary)] font-semibold">No posts yet.</p>
              {activeForumTab === 'Course Forum' && (
                <p className="text-sm mt-2 muted">Be the first to start a topic!</p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {posts.map((post) => (
                <div
                  key={post.id}
                  className="card p-2 sm:p-5 flex flex-col gap-2 border-2 border-[var(--border-medium)] hover:shadow-lg hover:border-blue-500/70 dark:hover:border-blue-500/50 transition-all duration-300 group bg-[var(--surface-2)] hover:shadow-md hover:bg-white/[0.03] transition-all rounded-xl"
                >
                  <div className="flex flex-row flex-wrap items-center gap-3 sm:gap-4">

                    <div className="flex-1 min-w-0 w-full sm:w-auto">

                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-blue-500/15 to-purple-500/10 flex items-center justify-center flex-shrink-0 border-2 border-blue-500/30 group-hover:border-blue-500/50 group-hover:scale-110 transition-all duration-300 shadow-lg group-hover:shadow-blue-500/20">
                          <FaPaperPlane className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                        </div>
                        <div>
                          <div>
                            <h3 className="font-bold text-base sm:text-lg line-clamp-1 group-hover:text-blue-400 transition-colors duration-200 text-[var(--text-primary)]">
                              {post.title}
                            </h3>
                            <p className="text-xs sm:text-sm muted">
                              {post.description}
                            </p>
                          </div>
                        </div>

                      </div>
                      <div
                        className="text-xs sm:text-sm text-[var(--text-secondary)] mb-2 sm:mb-3 line-clamp-2"

                      />

                      {post.image && (
                        <div className="my-2">
                          <img
                            src={post.image}
                            alt="Post"
                            className="max-h-48 rounded-lg border border-gray-200 shadow"
                            style={{ objectFit: 'contain', maxWidth: '100%' }}
                          />
                        </div>
                      )}

                      <div className="flex items-center justify-between sm:justify-start gap-4 text-xs text-[var(--text-muted)]">

                        <div className="flex items-center">
                          <FaUser className="w-3 h-3" />
                          <span className="text-xs text-[var(--text-secondary)] ml-2">
                            {post.anonymous ? (post.is_me ? "Anonymous (You)" : "Anonymous") : post.author}
                          </span>
                        </div>

                        {post.created_at && (
                          <div className="flex items-center">
                            <FaCalendar className="w-3 h-3" />
                            <span className="ml-1">
                              {new Date(post.created_at).toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-3 w-full sm:w-auto sm:self-start mt-2 sm:mt-0">
                      <button
                        onClick={() => handleShowComments(post)}
                        className="w-full sm:w-auto px-3 sm:px-4 py-2 border border-[var(--border-color)] rounded-lg text-xs sm:text-sm font-medium hover:bg-[var(--input-bg)] active:scale-95 transition-all duration-200 text-center whitespace-nowrap"
                      >
                        {selectedPostId === post.id ? 'Hide Comments' : 'Comments'}
                      </button>

                      <div className="relative post-action-menu">
                        <button
                          className="p-2 border border-[var(--border-color)] rounded-lg hover:bg-[var(--input-bg)] active:scale-95 transition-all duration-200 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                          onClick={() => setActionMenuOpen(actionMenuOpen === post.id ? null : post.id)}
                          aria-label="Actions"
                          tabIndex={0}
                        >
                          <FaEllipsisV className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                        </button>

                        {actionMenuOpen === post.id && (
                          <div className="absolute right-0 mt-2 z-50 w-32 bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg shadow-lg py-1 flex flex-col text-sm animate-fade-in">
                            <button
                              className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-500/10 transition"
                              onClick={() => handleDelete(post)}
                            >
                              <FaTrash className="w-4 h-4" /> Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Comments Section */}
                  {selectedPostId === post.id && (
                    <div className="mt-4 border-t-2 border-[var(--border-subtle)] pt-4">
                      <h4 className="text-xs sm:text-sm font-bold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
                        <div className="w-6 h-6 rounded-lg bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
                          <FaComments className="text-blue-400 w-3 h-3" />
                        </div>
                        Comments
                      </h4>
                      <div
                        className="overflow-x-auto sm:overflow-y-auto"
                        style={{ maxHeight: '220px' }}
                      >
                        {comments.length === 0 ? (
                          <div className="text-xs text-[var(--text-muted)] p-3 bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg">No comments yet.</div>
                        ) : (
                          <ul className="space-y-3">
                            {comments.map((comment) => (
                              <li
                                key={comment.id}
                                className="bg-[var(--input-bg)] border-2 border-[var(--border-color)] hover:border-blue-500/30 rounded-xl px-2 sm:px-4 py-3 flex flex-col shadow-md hover:shadow-lg transition-all duration-300 relative"
                              >
                                <div className="text-xs sm:text-sm text-[var(--text-primary)] leading-relaxed" style={{ wordBreak: 'break-word' }}>
                                  <span dangerouslySetInnerHTML={{ __html: comment.description }} />
                                </div>
                                <div className="flex items-center gap-2 mt-2 text-[10px] text-[var(--text-muted)]">
                                  {comment.created_at && (
                                    <span>
                                      {new Date(comment.created_at).toLocaleString()}
                                    </span>
                                  )}
                                  <span>-- {comment.anonymous ? (comment.is_me ? "Anonymous (You)" : "Anonymous") : comment.author}</span>
                                </div>
                                {/* Students can delete their own comments */}
                                {comment.is_me && (
                                  <div className="absolute top-2 right-2">
                                    <button
                                      className="p-1 rounded hover:bg-red-100/20 text-red-500"
                                      onClick={() => handleDeleteComment(comment)}
                                      aria-label="Delete Comment"
                                      title="Delete Comment"
                                    >
                                      <FaTrash />
                                    </button>
                                  </div>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <button
                        className="w-full sm:w-auto mt-4 px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white rounded-xl text-xs font-bold transition-all duration-300 shadow-lg shadow-blue-600/30 hover:shadow-xl hover:shadow-blue-600/40 border-2 border-blue-500/50 active:scale-95 flex items-center justify-center gap-2"
                        onClick={() => setShowAddCommentModal(true)}
                      >
                        <FaPaperPlane className="w-3 h-3" /> Add Comment
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Comment Modal */}
      {showAddCommentModal && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-1 sm:px-2">
          <div className="card-strong w-full max-w-full sm:max-w-md p-2 sm:p-6 relative rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto">
            <button
              className="absolute right-4 top-4 text-lg sm:text-xl p-2 rounded-full border border-[var(--border-color)] bg-[var(--input-bg)] hover:bg-white/10 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
              onClick={() => setShowAddCommentModal(false)}
            >
              <FaTimes />
            </button>
            <div className="flex flex-col sm:flex-row items-center gap-4 mb-4 sm:mt-0">
              <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <FaComments className="w-7 h-7 sm:w-8 sm:h-8 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg sm:text-2xl font-bold mb-1">Add Comment</h2>
                <p className="text-xs sm:text-sm muted">Share your thoughts.</p>
              </div>
            </div>
            <form
              onSubmit={async e => {
                e.preventDefault();
                const formData = new FormData(e.target);
                await handleAddComment({
                  description: formData.get('description'),
                  anonymous: formData.get('anonymous') ? 'true' : 'false'
                });
              }}
              className="space-y-4 mt-2"
            >
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium mb-1" htmlFor="comment-desc">Comment:</label>
                <textarea
                  name="description"
                  id="comment-desc"
                  className="input bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-sm focus-visible:outline-none"
                  placeholder="Write your comment..."
                  rows={4}
                  required
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="anonymous"
                  id="comment-anonymous"
                  className="toggle-checkbox"
                />
                <label htmlFor="comment-anonymous" className="text-sm">Anonymous</label>
              </div>
              <div className="flex gap-2 justify-end mt-6 flex-wrap">
                <button
                  type="button"
                  onClick={() => setShowAddCommentModal(false)}
                  className="px-4 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:text-[var(--text-primary)] font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
                >
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
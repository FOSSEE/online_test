/* eslint-disable */
import http from "../http-common";

class ForumService {
  getPosts (course_id) {
    return http.get(`/forum/course_forum/${course_id}/`);
  }

  nextPosts(page, course_id) {
    return http.get(`/forum/course_forum/${course_id}/?${page}`);
  }

  getPost (course_id, post_id) {
    return http.get(`/forum/course_forum/${course_id}/${post_id}/`);
  }

  deletePost (course_id, post_id) {
    return http.delete(`/forum/course_forum/${course_id}/${post_id}/`);
  }

  searchPosts (course_id, search) {
    return http.get(`/forum/course_forum/${course_id}/${search}`)
  }

  createComment (course_id, post_id, data) {
    return http.post(`/forum/course_forum/${course_id}/${post_id}/comments/`, data);
  }

  deleteComment (course_id, post_id, comment_id) {
    return http.delete(`/forum/course_forum/${course_id}/${post_id}/comments/${comment_id}/`)
  }

  create_or_update (course_id, post_id, data) {
    if (post_id) return http.put();
    else return http.post(`/forum/course_forum/${course_id}/`, data);
  }
}

export default new ForumService();

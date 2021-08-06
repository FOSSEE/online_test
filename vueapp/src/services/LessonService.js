import http from "../http-common";

class LessonService {
  get(id) {
      return http.get(`/lesson/${id}`);
  }

  create_or_update(module_id, id, data) {
    if(id) {
        return http.put(`/lesson/${module_id}/${id}`, data);
    } else {
        return http.post(`/lesson/${module_id}`, data);
    }
  }

  delete(id) {
    return http.delete(`/lesson/${id}`);
  }

  add_or_edit_topic(lesson_id, id, data) {
    if(id) {
        return http.put(`/topic/${lesson_id}/${id}`, data);
    } else {
        return http.post(`/topic/${lesson_id}`, data);
    }
  }

  get_toc(lesson_id) {
    return http.get(`/toc/${lesson_id}`);
  }
}

export default new LessonService();

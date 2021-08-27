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

  add_or_edit_toc(lesson_id, id, data) {
    if(id) {
        return http.put(`/toc/${lesson_id}/${id}`, data);
    } else {
        return http.post(`/toc/${lesson_id}`, data);
    }
  }

  get_toc(lesson_id) {
    return http.get(`all/toc/${lesson_id}`);
  }

  delete_toc(lesson_id, id) {
    return http.delete(`/toc/${lesson_id}/${id}`);
  }
}

export default new LessonService();

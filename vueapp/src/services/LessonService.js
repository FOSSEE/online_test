import http from "../http-common";

class LessonService {
    get(id) {
        return http.get(`/lesson/${id}`);
    }

    create_or_update(id, data) {
        if(id) {
            return http.put(`/lesson/${id}`, data);
        } else {
            return http.post(`/lesson`, data);
        }
    }

    delete(id) {
        return http.delete(`/lesson/${id}`);
    }
}

export default new LessonService();

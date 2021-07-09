import http from "../http-common";

class ModuleService {
    getall(course_id) {
        return http.get(`/modules/${course_id}`);
    }

    get(id) {
        return http.get(`/module/${id}`);
    }

    create_or_update(id, data) {
        if(id) {
            return http.put(`/module/${id}`, data);
        } else {
            return http.post("/module", data);
        }
    }

    delete(id) {
        return http.delete(`/course/${id}`);
    }
}

export default new ModuleService();

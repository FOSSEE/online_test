import http from "../http-common";

class CourseService {
    getall() {
        return http.get("/courses");
    }

    get(id) {
        return http.get(`/course/${id}`);
    }

    create_or_update(id, data) {
        if(id) {
            return http.put(`/course/${id}`, data);
        } else {
            return http.post("/course", data);
        }
    }

    delete(id) {
        return http.delete(`/course/${id}`);
    }

    findByName(name, active) {
        return http.get(`/courses?name=${name}&active=${active}`);
    }

    more(page) {
        return http.get(`/courses?${page}`);
    }
}

export default new CourseService();

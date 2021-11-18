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

    modules(id) {
        return http.get(`/modules/${id}`);
    }

    getEnrollments(id, enrollmentStatus) {
        if (enrollmentStatus) {
            return http.get(`/course/enrollments/${id}?status=${enrollmentStatus}`);
        } else {
            return http.get(`/course/enrollments/${id}`);
        }
    }

    setEnrollments(id, data) {
        return http.post(`/course/enrollments/${id}`, data);
    }

    getTeachers(id) {
        return http.get(`/course/teachers/${id}`);
    }

    setTeachers(id, data) {
        return http.post(`/course/teachers/${id}`, data);
    }

    sendMail(id, data) {
        return http.post(`/course/send_mail/${id}`, data);
    }

    getStatistics(id) {
        return http.get(`/course/progress/${id}`);
    }
}

export default new CourseService();

import http from "../http-common";

class ModuleService {
    getall(course_id) {
        return http.get(`/modules/${course_id}`);
    }

    get(course_id, id) {
        return http.get(`/module/${course_id}/${id}`);
    }

    create_or_update(course_id, id, data) {
        if(id) {
            return http.put(`/module/${course_id}/${id}`, data);
        } else {
            return http.post(`/module/${course_id}`, data);
        }
    }

    delete(course_id, id) {
        return http.delete(`/module/${course_id}/${id}`);
    }

    changeUnits(module_id, data) {
        return http.post(`/unit/order/${module_id}`, data)
    }
}

export default new ModuleService();

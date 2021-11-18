import http from "../http-common";

class QuizService {

    get(module_id, id) {
        return http.get(`/quiz/${module_id}/${id}`);
    }

    create_or_update(module_id, id, data) {
        if (id) {
            return http.put(`/quiz/${module_id}/${id}`, data);
        } else {
            return http.post(`/quiz/${module_id}`, data);
        }
    }

    delete(module_id, id) {
        return http.delete(`/quiz/${module_id}/${id}`);
    }

    addQuestions(id, data) {
        console.log(id, data)
    }
}

export default new QuizService;

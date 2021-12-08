import http from "../http-common";

class QuestionService {
    getQuestionTypeandMarks() {
        return http.get(`/filter/questions`);
    }
    
    filterQuestions(data) {
        return http.post(`/filter/questions`, data);
    }
}

export default new QuestionService

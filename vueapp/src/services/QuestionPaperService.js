import http from "../http-common";

class QuestionPaperService {
    getQuestionPaperById(module_id, quiz_id, id) {
        return http.get(`/questionpaper/${module_id}/${quiz_id}/${id}`);
    }
    getAllQuestionPaper(module_id, quiz_id) {
        return http.get(`/questionpaper/${module_id}/${quiz_id}`);
    }
    saveQuestionPaper(module_id, quiz_id, id, data) {
        return http.put(`/questionpaper/${module_id}/${quiz_id}/${id}`, data)
    }
}

export default new QuestionPaperService

import http from "../http-common";

class LoginService {

    validate(username, password) {
        return username != '' && password != '';
    }

    sendForLogin(data) {
        return http.post("/login", data);
    }

    getCourses() {
        return http.get("/courses");
    }
}

export default new LoginService();

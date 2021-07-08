import axios from "axios";

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

export default axios.create({
  baseURL: "http://localhost:8000/api/v2",
  xstfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: {
    "Content-type": "application/json",
    'X-CSRFToken': 'csrftoken',
  }
});

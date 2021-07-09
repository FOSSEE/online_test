import { createStore } from 'vuex';
const store = createStore({
  state() {
    return {
        showLoading: false,
        user_id: '',
        course_id: '',
    }
  },
  mutations: {
    toggleLoader(state, payload) {
      state.showLoading = payload;
    },
    setUserId(state, payload) {
      state.user_id = payload;
    },
    setCourseId(state, payload) {
      state.course_id = payload;
    }
  },
});

export default store;

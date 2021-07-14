import { createStore } from 'vuex';
const store = createStore({
  state() {
    return {
      showLoading: false,
      user_id: '',
      course_id: '',
      module: {},
      lesson: {},
      showModule: false,
      showLesson: false,
      course_modules: [],
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
    },
    setModule(state, payload) {
      state.module = payload
    },
    setLesson(state, payload) {
      state.lesson = payload
    },
    toggleModule(state, payload) {
      state.showModule = payload
    },
    toggleLesson(state, payload) {
      state.showLesson = payload
    },
  },
  actions: {
    setModule({commit}, module) {
      commit('setModule', module)
    },
    setLesson({commit}, module) {
      commit('setLesson', module)
    },
    toggleModule({commit}, isModule) {
      commit('toggleModule', isModule)
    },
    toggleLesson({commit}, isLesson) {
      commit('toggleLesson', isLesson)
    },
    setUserId({commit}, id) {
      commit('setUserId', id)
    },
    setCourseId({commit}, id) {
      commit('setCourseId', id)
    },
  },
});

export default store;

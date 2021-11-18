import { createStore } from 'vuex';
const store = createStore({
  state() {
    return {
      showLoading: false,
      user_id: '',
      course_id: '',
      module: {},
      unit: {},
      showModule: false,
      showLesson: false,
      showQuiz: false,
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
    setUnit(state, payload) {
      state.unit = payload
    },
    toggleModule(state, payload) {
      state.showModule = payload
    },
    toggleUnit(state, payload) {
      state.showLesson = payload.isLesson
      state.showQuiz = payload.isQuiz
    },
  },
  actions: {
    setModule({commit}, module) {
      commit('setModule', module)
    },
    setUnit({commit}, module) {
      commit('setUnit', module)
    },
    toggleModule({commit}, isModule) {
      commit('toggleModule', isModule)
    },
    toggleUnit({commit}, isUnit) {
      commit('toggleUnit', isUnit)
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

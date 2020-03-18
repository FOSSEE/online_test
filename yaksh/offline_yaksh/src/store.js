// Vuex Store
const store = new Vuex.Store({
  state: {
    courseData: courseData,
    questions: [],
    TOKEN: JSON.parse(localStorage.getItem('TOKEN')) || undefined
  },
  mutations: {
    UPDATE_COURSE (state, payload) {
      state.courseData = payload
    }
  },
  actions: {
    getCourse ({commit}) {
      commit('UPDATE_COURSE', courseData)
    },
    getUnit(state, payload) {
      console.log(payload)
    }
  },
  getters: {
    courseData: state => state.courseData,
    getQuestions: state => state.questions,
  }
})

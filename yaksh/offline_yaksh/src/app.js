const routes = [
  {
    path: '',
    component: Course,
    name:'ViewCourse'
  },
  {
    path: '/module/:course_id/:module_id',
    component: Module,
    name: 'ViewModule'
  },
  {
    path: '/:course_id/:quiz_id',
    component: Quiz,
    name: 'QuizModule'
  },
  {
    path: '/:course_id/:unit_id/:quiz_id',
    component: QuizInstructions,
    name: 'QuizInstructions'
  },
]

const router = new VueRouter({routes})

// Vuex Store
const store = new Vuex.Store({
  state: {
    file: '',
    active: '',
    answer: [],
    result: [],
    unitIndex: 0,
    response: [],
    isOnline: false,
    isOffline: false,
    questions: [],
    loading: false,
    moduleIndex: 0,
    unit: undefined,
    module: undefined,
    unitId: undefined,
    moduleId: undefined,
    courseData: data[0],
    question: undefined,
    questionNumber: undefined,
    time_left: undefined,
    quiz:  JSON.parse(sessionStorage.getItem('quiz')) || undefined,
    TOKEN: JSON.parse(localStorage.getItem('TOKEN')) || undefined,
    cmOption: {
      tabSize: 4,
      styleActiveLine: true,
      lineNumbers: true,
      mode: '',
      theme: "monokai"
     }
  },

  mutations: {
    UPDATE_COURSE (state, payload) {
      state.courseData = payload
    },

    UPDATE_LOADING (state, payload) {
      state.loading = payload
    },

    UPDATE_TOKEN (state, payload) {
      state.TOKEN = payload
    },

    UPDATE_MODULE_INDEX (state, payload) {
      state.moduleIndex = payload
    },

    UPDATE_UNIT_INDEX (state, payload) {
      state.unitIndex = payload
    },

    UPDATE_MODULE(state, payload) {
      state.module = payload
    },

    UPDATE_MODULE_ID (state, payload) {
      state.moduleId = payload
    },

    UPDATE_UNIT_ID (state, payload) {
      state.unitId = payload
    },

    UPDATE_UNIT(state, payload) {
      state.unit = payload
    },

    UPDATE_SELECTED_QUESTION(state, payload) {
      if(payload) {
        state.questions = payload;
        state.response = payload;
      } else {
        state.questions = []
        state.response = []
      }
    },

    SET_QUIZ_TIMER (state, payload) {
      state.time_left = payload
    },

    UPDATE_QUIZ_TIMER(state, payload) {
      state.time_left = payload
    },

    UPDATE_QUESTION (state, payload) {
      state.question = payload
    },

    UPDATE_QUESTION_NUMBER (state, payload) {
      state.questionNumber = payload
    },

    UPDATE_CHECKED_ANSWERS (state, payload) {
      state.answer.push(payload)
    },

    REMOVE_CHECKED_ANSWERS (state, payload) {
      state.answer = state.answer.filter(ans => {
          return ans != payload.id
      })
    },

    UPDATE_FILE (state, payload) {
      state.file = payload
    },

    UPDATE_RESPONSE_RESULT (state, payload) {
      state.result = payload
    },

    SET_ANSWER(state, payload) {
      state.answer = payload
    },

    UPDATE_QUIZ(state, payload) {
      state.quiz = payload
    },

    UPDATE_ISONLINE(state, payload) {
      state.isOnline = payload
    },

    UPDATE_ISOFFLINE(state, payload) {
      state.isOffline = payload
    },

    UPDATE_CM_MODE (state, payload) {
      if(payload.language === 'python') {
        state.cmOption.mode = 'text/x-python'
      } else if (payload.language === 'c') {
        state.cmOption.mode = 'text/x-csrc'
      } else if (payload.language === 'cpp') {
        state.cmOption.mode = 'text/x-c++src'
      } else if (payload.language === 'java') {
        state.cmOption.mode = 'text/x-java'
      } else if (payload.language === 'bash') {
        state.cmOption.mode = 'text/x-sh'
      } else if (payload.language === 'scilab') {
        state.cmOption.mode = 'text/x-csrc'
      }
    }
  },

  actions: {
    getCourse ({commit}) {
      commit('UPDATE_COURSE', courseData)
    },

    login (state, payload) {
      const username = payload["username"],
            password = payload["password"]
      axios({
        method: 'POST',
        url: 'http://localhost:8000/api/login/',
        data: {
          username: username,
          password: password
        }
      })
      .then((response) => {
        token = response.data.token
        if (token) {
          localStorage.setItem('TOKEN', JSON.stringify(token))
          state.commit('UPDATE_TOKEN', token)
          location.reload()
        }
      }).catch((error) => {
        console.log(error)
      })
    },

    showQuestion({commit}, payload) {
      this.state.result = []
      this.state.answer = []
      commit('UPDATE_QUESTION', payload.question)
      commit('UPDATE_QUESTION_NUMBER', payload.index + 1)
      commit('UPDATE_CM_MODE', payload.question)
    },

    showModule({commit}, module) {
      this.state.unitIndex = 0
      commit('UPDATE_MODULE', module)
      commit('UPDATE_UNIT_ID', undefined)
    },

    showUnit({commit}, unit) {
      commit('UPDATE_UNIT', unit)
    },

    activeModule ({commit, dispatch}, module_id) {
      commit('UPDATE_MODULE_ID', module_id)
      if(module_id){
        router.push(`${module_id}`).catch(err=>{})
      }
      dispatch('updateModule', module_id)
    },

    activeUnit ({commit}, unit_id) {
      let currModule = this.getters.module
      let units = currModule.learning_unit
      let unitKeys = Object.keys(units)
      if (unit_id) {
        let currUnitIndex = units.findIndex(u => u.id === unit_id)
        if (currUnitIndex === -1 || currUnitIndex > unitKeys.length) {
          currUnitIndex = 0
          commit('UPDATE_UNIT_INDEX', currUnitIndex)
        } else {
          currUnitIndex += 1
          commit('UPDATE_UNIT_INDEX', currUnitIndex)
        }
      }
      commit('UPDATE_UNIT_ID', unit_id)
    },

    getFirstLesson({commit}) {
      let module = this.getters.module
      if(module) {
        let firstUnit = module.learning_unit[0]
        commit('UPDATE_UNIT', firstUnit)
      }
    },

    showQuiz({commit}, quiz) {
      sessionStorage.setItem('quiz', JSON.stringify(quiz))
      commit('UPDATE_QUIZ', quiz)
    },

    updateCheckedAnswers ({commit}, choices) {
      if(choices.checked) {
        commit('UPDATE_CHECKED_ANSWERS', choices.id)
      } else {
        commit('REMOVE_CHECKED_ANSWERS', choices)
      }
    },

    updateModule({commit}, moduleId){
      let modules = this.getters.course_data.learning_module,
          module = modules.filter(module => {
            return module.id == moduleId
          })
      commit('UPDATE_MODULE', module[0])
    },

    async check_status({commit, dispatch}, payload) {
      const question = this.getters.question,
            TOKEN = this.getters.gettoken,
            response = payload.response;
      let count = payload.count,
          MAX_COUNT = payload.MAX_COUNT;

      if (question.type === 'code') {
        const status = response.data.status,
              uid = response.data.uid;

        if ((status === 'running' || status == 'not started') && count < MAX_COUNT) {
          const _response = await axios({
            method: 'GET',
              url: `http://localhost:8000/api/validate/${uid}/`,
              headers: {
                Authorization: 'Token ' + TOKEN
              }
          });

          if (_response) {
            const result = JSON.parse(_response.data.result)
            if (result) {
              commit('UPDATE_RESPONSE_RESULT', result)
              commit('UPDATE_LOADING', false)
            } else {
              count++;
              setTimeout(() => {
                dispatch('check_status', {response, count, MAX_COUNT})
              }, 2000)
            }
          }
        }
      } else {
        commit('UPDATE_LOADING', false)
      }
    },

    async submitAnswer ({commit, dispatch}) {
      const answerPaperId = this.getters.getQuestions.id,
            questionId = this.getters.question.id,
            answer = this.getters.answer,
            TOKEN = this.getters.gettoken;
      commit('UPDATE_LOADING', true)
      const response = await axios({
        method: 'POST',
        url:`http://localhost:8000/api/validate/${answerPaperId}/${questionId}/`,
        headers: {
          Authorization: 'Token ' + TOKEN
        },
        data: {
          answer: answer
        },
      });
      let count = 0,
          MAX_COUNT = 14;
      console.log(response);
      dispatch('check_status', {response, count, MAX_COUNT});
    },

    quit({commit}) {
      const answerPaperId = this.getters.getQuestions.id
      const TOKEN = this.getters.gettoken
      axios({
        method: 'GET',
        url: `http://localhost:8000/api/quit/${answerPaperId}/`,
        headers: {
          Authorization: 'Token ' + TOKEN
        }
      })
        .then((response) => {
          console.log(response)
          if (response.data.status === 'completed') {
            sessionStorage.removeItem('quiz')
            commit('UPDATE_QUIZ_TIMER', undefined)
            commit('UPDATE_SELECTED_QUESTION', undefined)
            commit('UPDATE_QUIZ', undefined)
            commit('UPDATE_QUESTION', undefined)
            commit('UPDATE_RESPONSE_RESULT', undefined)
            router.push('/')
          }
        })
    }
  },

  getters: {
    course_data: state => state.courseData,
    getQuestions: state => state.questions,
    question: state => state.question,
    gettoken: state => state.TOKEN,
    answer: state => state.answer,
    result: state => state.result,
    module: state => state.module,
    unit: state => state.unit,
    quiz: state => state.quiz,
    isOffline: state => state.isOffline,
    isOnline: state => state.isOnline,
    questionNumber: state => state.questionNumber,
    active: state => state.active,
    unitId: state => state.unitId,
    loading: state => state.loading,
    moduleId: state => state.moduleId,
    time_left: state => state.time_left,
    unitIndex: state => state.unitIndex,
    moduleIndex: state => state.moduleIndex,
    cmOption: state => state.cmOption
  }
})

new Vue({
  name: 'App',
  el: '#app',
  router,
  store,
  template : `
  <div>
    <nav class="navbar bg-dark navbar-dark">
      <div class="container-fluid">
        <div class="navbar-header">
          <a class="navbar-brand" href="index.html">
            <img src="@/../static/images/yaksh_banner.png" alt="YAKSH"/>
          </a>
        </div>
        <div class="d-flex flex-row-reverse">
          <AppStatus />
          <Quit />
          <Timer />
        </div>
      </div>
    </nav>
    <router-view/>
  </div>
  `,
})

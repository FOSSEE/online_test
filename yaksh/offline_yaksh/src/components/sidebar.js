const Sidebar = Vue.component('Sidebar', {
  template: `
    <div>
      <nav id="sidebar" :class="{active: active}">
        <div class="sidebar-header" id="sidebar_course_title">
          <center><h3>{{course_data.name}}</h3></center>
        </div>
        <hr />
        <div v-if="time_left">
          <center><h4>{{quiz.description}}</h4></center>
          <hr />
        </div>
        <div v-if="getQuestions">
          <QuestionNumbers
            :questions="getQuestions"
          />
        </div>
        <div v-if="getQuestions.length === 0">
          <ModuleList :modules="course_data"/>
        </div>
      </nav>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
      'getQuestions',
      'gettoken',
      'course_data',
      'active',
      'loading',
      'quiz',
      'time_left'
    ])
  },
  created () {
    const courseId = parseInt(this.$route.params.course_id),
          quizId = parseInt(this.$route.params.quiz_id)
    if (courseId && quizId && this.gettoken !== undefined){
      this.fetchQuestions(courseId, quizId)
    }
  },
  methods: {
    fetchQuestions (course_id, quiz_id) {
      this.$store.commit('UPDATE_LOADING', true)
      axios({
        method: 'get',
        url: `http://localhost:8000/api/start_quiz/${course_id}/${quiz_id}`,
        headers: {
          Authorization: 'Token ' + this.gettoken,
          'Content-Type': 'application/json'
        }
      })
      .then((response) => {
        console.log(response)
        if(response.data.answerpaper){
          let firstQuestion = response.data.answerpaper.questions[0]
          this.$store.commit('UPDATE_SELECTED_QUESTION', response.data.answerpaper)
          this.$store.commit('UPDATE_QUESTION', firstQuestion)
          this.$store.commit('UPDATE_QUESTION_NUMBER', 1)
          this.$store.commit('SET_QUIZ_TIMER', response.data.time_left)
          this.$store.commit('UPDATE_CM_MODE', firstQuestion)
        } else {
          let dict = {}
          dict["message"] = response.data.message
          this.$store.commit('UPDATE_RESPONSE_RESULT', dict)
        }
        this.$store.commit('UPDATE_LOADING', false)
      })
      .catch((error) => {
        console.log(error)
      })
    }
  }
})
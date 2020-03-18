const QuizInstructions = Vue.component('QuizInstructions', {
  template: `
    <div>
      <div id="content">
        <div class="card">
          <div v-if="quiz">
            <div class="card-header">
              <h4>{{quiz.description}}</h4>
            </div>
            <div class="card-body">
              <div class="alert alert-info ">
              You can attempt this Quiz at any time between <strong>{{quiz.start_date_time}}</strong> Asia/Kolkata and <strong>{{quiz.end_date_time}}</strong> Asia/Kolkata
              You are not allowed to attempt the Quiz before or after this duration
              </div>
              <div v-html="quiz.instructions"></div>
              <router-link :to="{name: 'QuizModule', params: {course_id: courseId, quiz_id: quiz.id}}" class="btn btn-primary">Start Quiz</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data () {
      return {
        courseId: undefined,
      }
  },
  computed: {
    ...Vuex.mapGetters([
      'quiz',
    ])
  },
  created () {
    this.courseId = parseInt(this.$route.params.course_id)
  },
})
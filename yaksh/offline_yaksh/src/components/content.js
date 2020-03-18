const Content = Vue.component('Content', {
  template: `
    <div id="content">
      <ToggleButton />
      <br />
      <Login />
      <div v-if="question">
        <div class="card">
          <div class="card-header">
            {{questionNumber}}. <h5><strong>{{question.summary}}</strong></h5>
            <strong>{{question.type}}</strong>              
          </div>
          <div class="card-body">
            <p v-html="question.description"></p>
          </div>
        </div>
        <div class="card">
          <div class="card-body">
            <form @submit="submitForm">
              <input ref="answer" v-if="question.type=='integer' || question.type=='float'">
              <textarea v-if="question.type=='string'" ref="answer"></textarea>
              <div class="form-group" v-if="question.type=='code'">
                <textarea id="codemirror1" ref="answer" rows="10" cols="50" :key="question.id"></textarea>
              </div>
              <div v-if="question.type=='mcq'">
                <div v-for="testcases in question.test_cases" :key="testcases.id">
                    <input type="radio" v-model="answer" name="testcases.options" :value="testcases.options"><div v-html="testcases.options"></div>
                </div>
              </div>
              <div v-if="question.type=='mcc'">
                <div v-for="testcases in question.test_cases" :key="testcases.id">
                    <input type="checkbox" :value="testcases.options" :id="testcases.id" @change="updateCheckedAnswers" > {{testcases.options}}
                </div>
              </div>
              <input type="file" v-if="question.type=='upload'" ref="file" @change="handleFileUpload()" id="file" name="">
              
              <button class="btn btn-success">Submit</button>
              <button class="btn btn-primary">Attempt Later</button>
            </form>
          </div>
          <Error :result="result"/>
        </div>
      </div>
      <Error :result="result"/>
      <div class="card">
        <div v-if="!unit && module">
          <div class="card-header">
            <div class="row">
              <div class="col-md-8">
                {{module.name}}
              </div>
            </div>
          </div>
          <div class="card-body" v-html="module.description"></div>
        </div>
        <div v-if="unit">
          <div v-if="unit.lesson">
            <div v-if="unit.lesson.video_path">
              <div class="card-header">
                <h4>{{unit.lesson.name}}</h4>
              </div>
              <div class="card-body">
                <video :src="unit.lesson.video_path" :key="unit.lesson.id" width="100%" controls></video>
              </div>
            </div>
            <div v-else>
              <div class="card-header">
                <h4>{{unit.lesson.name}}</h4>
              </div>
              <div class="card-body">
                <div v-html="unit.lesson.description"></div>
              </div>
            </div>
          </div>
          <div v-else>
            <div class="card-header">
              <h4>{{unit.quiz.description}}</h4>
            </div>
            <div class="card-body">
              <div v-html="unit.quiz.instructions"></div>
             <center><router-link class="btn btn-primary" v-on:click.native="showQuiz(unit.quiz)" :to="{name: 'QuizInstructions', params: {course_id: courseId, unit_id: unit.id, quiz_id: unit.quiz.id}}" target="_blank"><strong>Start Quiz</strong></router-link></center>
            </div>
          </div>
        </div>
      </div>
      <br/>
      <div v-if="module !== undefined || unit !== undefined">
        <center><button class="btn btn-primary" @click.prevent="next">Next</button></center>
      </div>
    </div>
  `,
  data () {
    return {
      courseId: undefined
    }
  },
  created () {
    this.courseId = parseInt(this.$route.params.course_id)
  },
  computed: {
    ...Vuex.mapGetters([
      'question',
      'answer',
      'result',
      'module',
      'unit',
      'moduleIndex',
      'moduleId',
      'unitIndex',
      'questionNumber'
    ]),
    answer: {
      get () {
        this.$store.state.answer
      },
      set (value) {
        this.$store.commit("SET_ANSWER", value)
      }
    }
  },
  methods: {
    ...Vuex.mapActions([
      'showQuiz',
    ]),
    updateCheckedAnswers (e) {
      e.preventDefault()
      this.$store.dispatch('updateCheckedAnswers', e.target)
    },
    handleFileUpload (e) {
      const file = this.$refs.file.files[0];
      this.$store.commit('UPDATE_FILE', file)
    },
    submitForm(e) {
      e.preventDefault()
      if(this.question.type === 'mcc' || this.question.type === 'mcq') {
        const answer = this.answer
      } else {
        const answer = this.$refs.answer.value
        this.$store.commit('SET_ANSWER', answer)
      }
      this.$store.dispatch('submitAnswer')
    },

    nextModule (currModIndex, moduleKeys, modules) {
      if (currModIndex < moduleKeys.length - 1) {
        currModIndex += 1
      } else {
        currModIndex = 0
      }
      this.$store.commit('UPDATE_MODULE_INDEX', currModIndex)
      let nextModuleKey = moduleKeys[currModIndex],
          nextModule = modules[nextModuleKey],
          nextModuleId = nextModule.id
      this.$store.dispatch('activeModule', nextModuleId)
      this.$store.dispatch('showModule', nextModule)
    },

    nextUnit(currUnitIndex, unitKeys, units, currModIndex, moduleKeys, modules) {
      let nextUnitKey = unitKeys[currUnitIndex],
          nextUnit = units[nextUnitKey]
      if (nextUnit) {
        this.$store.dispatch('activeUnit', nextUnit.id)
        this.$store.dispatch('showUnit', nextUnit)
      } else {
        this.$store.dispatch('activeUnit', undefined)
        this.$store.dispatch('showUnit', undefined)
      }
      if (currUnitIndex <= unitKeys.length - 1) {
        currUnitIndex += 1
      } else {
        currUnitIndex = 0
        this.nextModule(currModIndex, moduleKeys, modules)
      }
      this.$store.commit('UPDATE_UNIT_INDEX', currUnitIndex)
    },

    next () {
      let currModule = this.module,
          currUnit = this.unit,
          modules = this.$store.getters.course_data.learning_module,
          moduleKeys = Object.keys(modules),
          currModIndex = modules.findIndex(module => module.id === currModule.id),
          units = currModule.learning_unit,
          unitKeys = Object.keys(units)
      if (units) {
        let currUnitIndex = this.unitIndex
        this.nextUnit(currUnitIndex, unitKeys, units, currModIndex, moduleKeys, modules)
      }
    },
  }
})

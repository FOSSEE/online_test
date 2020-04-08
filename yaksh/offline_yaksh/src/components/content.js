const Content = Vue.component('Content', {
  template: `
    <div id="content">
      <ToggleButton /> <!--ToggleButton component common for Quiz and Module-->
      <br />
      <Login /> <!--ToggleButton component common for Quiz and Module-->

      <!--Quiz Content Component-->
      <div v-if="question">
        <div class="card">
          <div class="card-header">
            {{questionNumber}}. <h5><strong>{{question.summary}}</strong></h5>
            <strong>{{question.type}}</strong>
          </div>
          <div class="card-body">
            <span v-html="question.description"></span>
          </div>
        </div>
        <div class="card">
          <div class="card-body">
            <form @submit.prevent="submitAnswer">
              <div v-if="question.type=='mcq'">
                <div v-for="testcase in question.test_cases" :key="testcase.id">
                  <input type="radio" name="testcase.id" @change="updateMcqAns(testcase.id)" /> <span v-html="testcase.options"></span>
                </div>
              </div>
              <div v-if="question.type=='mcc'">
                <div v-for="testcase in question.test_cases" :key="testcase.id">
                  <input type="checkbox" :value="testcase.options" :id="testcase.id" @change="updateCheckedAnswers" /> <span v-html="testcase.options"></span>
                </div>
              </div>
              <div v-if="question.type=='code'" class="form-group">
                <!-- <textarea id="codemirror1" :value="codeAns" @input="updateCodeAns" rows="10" cols="50" :key="question.id"></textarea> -->
                <codemirror ref="cm" :value="codeAns" :options="cmOption" @input="updateCodeAns" :key="question.id"/>
              </div>
              <button class="btn btn-success">Submit</button>
            </form>
          </div>
        </div>
      </div>
      <!--End Quiz Content Component-->

      <!--Error Component-->
      <Error :result="result"/>
      <!--End Error Component-->

      <!--Module Content Component-->
      <div class="card">
        <div v-if="!unit && module">
          <div class="card-header">
            <div class="row">
              <div class="col-md-8">
                {{module.name}}
              </div>
            </div>
          </div>
          <div class="card-body">
            <span v-html="module.description"></span>
          </div>
        </div>
        <div v-if="unit">
          <div v-if="unit.lesson">
            <div v-if="unit.lesson.video_path">
              <div class="card-header"><h4>{{unit.lesson.name}}</h4></div>
              <div class="card-body"><video :src="unit.lesson.video_path" :key="unit.lesson.id" width="100%" controls></video></div>
            </div>
            <div v-else>
              <div class="card-header"><h4>{{unit.lesson.name}}</h4></div>
              <div class="card-body"><span v-html="unit.lesson.description"></span></div>
            </div>
          </div>
          <div v-else>
            <div class="card-header"><h4>{{unit.quiz.description}}</h4></div>
            <div class="card-body">
              <span v-html="unit.quiz.instructions"></span>
              <center><router-link class="btn btn-primary" v-on:click.native="showQuiz(unit.quiz)" :to="{name: 'QuizInstructions', params: {course_id: courseId, unit_id: unit.id, quiz_id: unit.quiz.id}}" target="_blank"><strong>Start Quiz</strong></router-link></center>
            </div>
          </div>
        </div>
      </div>
      <br />
      <div v-if="module !== undefined || unit !== undefined">
        <center><button class="btn btn-primary" @click.prevent="next">Next</button></center>
      </div>
      <!--End Module Content Component-->
    </div>
  `,
  data () {
    return {
      courseId: undefined,
      codeAns: 'def fun(): \n     return True',
    }
  },

  created () {
    this.courseId = parseInt(this.$route.params.course_id)
  },

  computed: {
    ...Vuex.mapGetters([
      'question',
      'questionNumber',
      'answer',
      'module',
      'unit',
      'unitIndex',
      'result',
      'cmOption'
    ]),
  },

  methods: {
    ...Vuex.mapActions([
      'submitAnswer',
      'showQuiz'
    ]),

    updateMcqAns(id) {
      id = '' + id;
      this.$store.commit('SET_ANSWER', id);
    },

    updateCheckedAnswers(e) {
      this.$store.dispatch('updateCheckedAnswers', e.target);
    },

    updateCodeAns (value) {
      console.log(value)
      this.$store.commit('SET_ANSWER', value)
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

    next() {
      let currModule = this.module,
          currUnit = this.unit,
          modules = this.$store.getters.course_data.learning_module,
          moduleKeys = Object.keys(modules),
          currModIndex = modules.findIndex(module => module.id === currModule.id),
          units = currModule.learning_unit,
          unitKeys = Object.keys(units);
      if(units) {
        let currUnitIndex = this.unitIndex;
        this.nextUnit(currUnitIndex, unitKeys, units, currModIndex, moduleKeys, modules);
      }
    }
  }
});
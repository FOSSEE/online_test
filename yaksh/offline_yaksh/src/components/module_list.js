var ModuleList = Vue.component('ModuleList', {
  template: `
    <div class="wrapper">
      <ul class="list-unstyled components">
        <div v-for="(module, index) in modules.learning_module" :key="module.id">
          <li :class="{'active': module.id === moduleId }" @click="activeModule(module.id)" :id="'moduleList-' + moduleId">
            <a @click="showModule(module)"><h4><u>{{module.name}}</u></h4></a>
            <ul class="list-unstyled">
              <div v-for="(unit, index) in module.learning_unit" :key="unit.id">
                <li :class="{'active': unit.id === unitId }" @click="activeUnit(unit.id)" :id="'unitList-' + unitId">
                  <div v-if="unit.quiz">
                    <router-link v-on:click.native="showQuiz(unit.quiz)" :to="{name: 'QuizInstructions', params: {course_id: courseId, unit_id: unit.id, quiz_id: unit.quiz.id}}" target="_blank"><strong>{{unit.quiz.description}}</strong></router-link>
                  </div>
                  <div v-if="unit.lesson">
                    <a @click="showUnit(unit)"><strong>{{unit.lesson.name}}</strong></a>
                  </div>
                </li>
              </div>
            </ul>
          </li>
        </div>
      </ul>
    </div>
  `,
  props: ['modules'],
  data () {
    return {
      courseId: undefined,
    }
  },
  created () {
    this.courseId = parseInt(this.$route.params.course_id)
    const moduleId = parseInt(this.$route.params.module_id)
    this.$store.dispatch('updateModule', moduleId)
    this.$store.dispatch('activeModule', moduleId)
    localStorage.removeItem("quiz")
  },
  computed: {
    ...Vuex.mapGetters([
        'moduleId',
        'unitId'
      ])
  },
  methods: {
    ...Vuex.mapActions([
      'showModule',
      'showUnit',
      'showQuiz',
      'activeModule',
      'activeUnit',
    ]),
  }
})

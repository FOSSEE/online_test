var Module = Vue.component('Module', {
  template: `
    <div class="wrapper">
      <Sidebar />
      <Content />
    </div>
  `,
  data () {
      return {
        moduleId: undefined,
        courseId: undefined,
      }
  },
  
  created () {
    this.courseId = parseInt(this.$route.params.course_id)
    this.moduleId = parseInt(this.$route.params.module_id)
  },
  methods: {
      getModule(moduleId){
      
      }
  }
})

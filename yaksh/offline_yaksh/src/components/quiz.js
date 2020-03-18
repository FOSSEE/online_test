var Quiz = Vue.component('Quiz', {
  template: `
    <div class="wrapper">
      <Loading v-if="loading"/>
      <Sidebar/>
      <Content/>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
      'gettoken',
      'loading',
      'module',
      'unit'
    ]),
  },
  methods: {
    submitForm (e) {
      console.log('form submitted')
      e.preventDefault()
      const username = this.$refs.username.value,
            password = this.$refs.password.value,
            payload = {username, password}
      this.$store.dispatch('login', payload)
    }
  }
})

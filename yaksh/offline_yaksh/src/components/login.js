const Login = Vue.component('Login', {
  template: `
    <div>
      <div v-if="gettoken === undefined && module === undefined && unit === undefined">
        <form @submit=submitForm>
          <div class="form-group">
            <input ref="username" type="text" class="form-control" id="username" placeholder="Enter username">
          </div>
          <div class="form-group">
            <input ref="password" type="password" class="form-control" id="password" placeholder="Password">
          </div>
          <button type="submit" class="btn btn-primary">Submit</button>
        </form>
      </div>
    </div>
  `,
  data () {
    return {
    }
  },
  created () {
  },
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

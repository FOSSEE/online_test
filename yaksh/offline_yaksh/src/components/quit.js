const Quit = Vue.component('Quit', {
  template: `
    <div class="p-2" v-if="time_left">
      <button class="btn btn-danger" @click.prevent="quit">Quit</button>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
        'time_left'
      ]),
  },
  methods: {
    ...Vuex.mapActions([
      'quit'
    ])
  }
})
const ToggleButton = Vue.component('ToggleButton', {
  template: `
    <div>
      <button type="button" @click.prevent="toggleActive" id="sidebarCollapse" class="btn btn-info">
        <div id="burger"></div>
        <div id="burger"></div>
        <div id="burger"></div>
      </button>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
      'active'
    ])
  },
  methods: {
    toggleActive () {
      if (this.active === 'active') {
        this.$store.state.active = ''
      } else {
        this.$store.state.active = 'active'
      }
    }
  }
})
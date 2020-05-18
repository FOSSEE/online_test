const AppStatus = Vue.component('AppStatus', {
  template: `
    <div class="p-2">
      <p class="indicator online" v-if="isOnline">Online</p>
      <p class="indicator offline" v-if="isOffline">Offline</p>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
      'isOffline',
      'isOnline'
    ])
  },
  mounted () {
    if (typeof window !== 'undefined') {
      navigator.onLine ? this.$store.commit('UPDATE_ISONLINE', true) : this.$store.commit('UPDATE_ISOFFLINE', true)
      const onlineHandler = () => {
        this.$emit('online')
        this.$store.commit('UPDATE_ISONLINE', true)
        this.$store.commit('UPDATE_ISOFFLINE', false)
      }

      const offlineHandler = () => {
        this.$emit('offline')
        this.$store.commit('UPDATE_ISOFFLINE', true)
        this.$store.commit('UPDATE_ISONLINE', false)
      }

      window.addEventListener('online',  onlineHandler)
      window.addEventListener('offline',  offlineHandler)

      this.$once('hook:beforeDestroy', () => {
        window.removeEventListener('online', onlineHandler)
        window.removeEventListener('offline', offlineHandler)
      })
    }
  }
})
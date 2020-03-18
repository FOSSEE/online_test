const Timer = Vue.component('Timer', {
  template: `
    <div class="navbar-nav ml-auto" v-if="time_left">
      <h4 style="color:#FFF;"><span id='timer' style="font-size:25px;">{{hour}} : {{min}} : {{sec}}</span></h4>
    </div>
  `,
  computed: {
    ...Vuex.mapGetters([
        'time_left'
      ]),
    hour(){
      let h = Math.floor(this.time_left / 3600)
      return h > 9 ? h : '0' + h;
    },
    min(){
      let m = Math.floor(this.time_left % 3600 / 60);
      return m > 9 ? m :'0' + m
    },
    sec(){
      let s = Math.floor(this.time_left % 3600 % 60);
      return s > 9 ? s : '0' + s
    }
  },
  watch: {
    time_left: {
      immediate: true,
      handler (newVal) {
        if(newVal !== undefined){
          let timer = this.time_left
          if (timer > 0) {
            setInterval(() => {
              timer -= 1
              this.$store.commit('UPDATE_QUIZ_TIMER', timer)
            }, 1000)
          } else {
            location.reload()
            console.log("Timer ups")
          }
        }
      }
    }
  }
})
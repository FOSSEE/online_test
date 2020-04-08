const Timer = Vue.component('Timer', {
  template: `
    <div class="p-2" v-if="time_left">
      <h4 style="color:#FFF;"><span id='timer' style="font-size:25px;">{{hour}} : {{min}} : {{sec}}</span></h4>
    </div>
  `,
  data () {
    return {
      timer: 0
    }
  },
  computed: {
    ...Vuex.mapGetters([
        'time_left',
      ]),
    hour(){
      let h = Math.floor(this.timer / 3600)
      return h > 9 ? h : '0' + h;
    },
    min(){
      let m = Math.floor(this.timer % 3600 / 60);
      return m > 9 ? m :'0' + m
    },
    sec(){
      let s = Math.floor(this.timer % 3600 % 60);
      return s > 9 ? s : '0' + s
    }
  },
  watch: {
    time_left: {
      immediate: true,
      handler (newVal) {
        if(newVal !== undefined){
          this.timer = this.time_left
          setInterval(() => {
            this.timer -= 1
            if(this.timer === 0) {
              this.$store.dispatch('quit')
            }
          }, 1000)
        }
      }
    }
  }
})
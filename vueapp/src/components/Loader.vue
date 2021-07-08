<template>
  <loading v-model:active="loading"
   :can-cancel="false"
   :is-full-page="true"/>
</template>

<script>
  import Loading from 'vue-loading-overlay';
  import 'vue-loading-overlay/dist/vue-loading.css';
  import { mapState } from 'vuex';
  export default {
    name: "Loader",
    components: {
      Loading
    },
    computed: {
        ...mapState({
            loading: (state) => state.showLoading,
        }),
      }
    }
</script>

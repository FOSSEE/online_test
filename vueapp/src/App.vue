<template>
    <Loader/>
    <div>
    <router-view />
    </div>
</template>

<script>
import Loader from './components/Loader.vue'

export default {
  name: 'App',
  components: {
    Loader
  },
}
</script>

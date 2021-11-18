<template>
    <div>
    <Loader/>
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
<style>
  .tox-notifications-container {
    display: none !important;
  }
</style>
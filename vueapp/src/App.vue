<template>
    <Course/>
    <Loader/>
</template>

<script>
import Course from './components/course/Course.vue'
import Loader from './components/Loader.vue'

export default {
  name: 'App',
  components: {
    Course, Loader,
  },
}
</script>


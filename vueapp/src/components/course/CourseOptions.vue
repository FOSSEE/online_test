<template>
  <div>
    <ul class="list-group">
        <li class="list-group-item">
            <router-link :to="{name: 'course_enrollments', params: {course_id: course_id}}">
                Enrollments
            </router-link>
        </li>
        <li class="list-group-item">
            <router-link :to="{name: 'course_contents', params: {course_id: course_id}}">
                Contents
            </router-link>
        </li>
    </ul>
  </div>
</template>
<script>

export default {
  name: "CourseOptions",
  props: {
    course_id: String
  },
}
</script>
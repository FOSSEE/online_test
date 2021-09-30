<template>
  <div>
    <ul class="list-group">
      <li class="list-group-item">
        <router-link :to="{name: 'course_contents', params: {course_id: course_id}}">
          Contents
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_enrollments', params: {course_id: course_id}}">
          Enrollments
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Statistics
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Teachers/TA
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_send_mail', params: {course_id: course_id}}">
          Send Mail
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Discussion Forum
        </router-link>
      </li>
      <li class="list-group-item">
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Upload/Download
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
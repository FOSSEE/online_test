<template>
  <div>
    <ul class="list-group">
      <li class="list-group-item">
        <span v-if="contents" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_contents', params: {course_id: course_id}}">
          Contents
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="enrollment" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_enrollments', params: {course_id: course_id}}">
          Enrollments
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="stats" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_statistics', params: {course_id: course_id}}">
          Statistics
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="ta" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Teachers/TA
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="mail" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_send_mail', params: {course_id: course_id}}">
          Send Mail
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="forum" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
        <router-link :to="{name: 'course_teachers', params: {course_id: course_id}}">
          Discussion Forum
        </router-link>
      </li>
      <li class="list-group-item">
        <span v-if="upload" class="badge badge-success"><i class="fas fa-dot-circle"></i></span>
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
    course_id: String,
    activeTab: Number
  },
  data() {
    return {
      contents: false,
      enrollment: false,
      stats: false,
      ta: false,
      mail: false,
      forum: false,
      upload: false,
    }
  },
  mounted() {
    switch(this.activeTab) {
      case 1:
        this.contents = true
        break;
      case 2:
        this.enrollment = true
        break;
      case 3:
        this.stats = true
        break;
      case 4:
        this.ta = true
        break;
      case 5:
        this.mail = true
        break;
      case 6:
        this.forum = true
        break;
      case 7:
        this.upload = true
        break;
    }
  }
}
</script>

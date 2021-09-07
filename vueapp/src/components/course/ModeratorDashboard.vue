<template>
  <div>
    <div class="container">
      <center>
        <h4>
          List of quizzes! Click on the given links to have a look at answer papers for a quiz
        </h4>
      </center>
      <hr>
      <center>
        <a href="#" class="btn btn-success btn-lg">
          <span class="fa fa-plus-circle"></span>&nbsp;Add Course
        </a>
        <a href="#" class="btn btn-primary btn-lg">
          Create Demo Course
        </a>
        <br><br>
        <div>
          <!-- Alert Messages -->
        </div>
      </center>
      <!-- {{courses}} -->
      <div v-for="(course, index) in courses" :key="course.id">
        <div class="card">
          <div class="card-header">
            <div class="row">
              <div class="col-md-4">
                <h4 data-toggle="tooltip">{{course.name}}</h4>
              </div>
              <div class="col-md-2">
                <div v-if="course.active">
                  <span class="badge badge-pill badge-success">
                    Active
                  </span>
                </div>
                <div v-else>
                  <span class="badge badge-pill badge-danger">
                    Inactive
                  </span>
                </div>
              </div>
              <div class="col-md-3">
                <a href="#" class="btn btn-primary">
                  <i class="fa fa-tasks">
                    Manage Course
                  </i>
                </a>
              </div>
              <div class="col-md">
                <a href="#" class="card-link btn btn-outline-info" data-toggle="collapse" :data-target="'#collapse-' + index">
                  Details
                  <i class="fa fa-toggle-down"></i>
                </a>
              </div>
            </div>
          </div>
          <div class="collapse" :id="'collapse-' + index">
            <div class="card-body">
              <span v-html="course.instructions"></span>
            </div>
          </div>
        </div>  
      </div>
    </div>
  </div>
</template>
<script>
import axios from 'axios'

export default {
  name: "ModeratorDasboard",
  data () {
    return {
      courses: ''
    };
  },
  mounted () {
    this.getAllCourses();
  },
  methods: {
    async getAllCourses() {
      const response = await axios({
        methods: 'get',
        url: `http://127.0.0.1:8000/api/v2/moderator_dashboard/`,
        headers: {
          Authorization: 'Token ' + 'e5a266097aa4e56273a71eafb981003dfec1aa7a'
        }
      });
      if (response.status == 200) {
        this.courses = response.data.results
      }
    },
  }
}

</script>
<style scoped>
</style>
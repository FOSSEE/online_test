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
import CourseService from '../../services/CourseService';

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
    getAllCourses() {
      this.$store.commit('toggleLoader', true);
        CourseService.getall().then(response => {
          var data = response.data;
          this.courses = data.results;
          this.previous_page = data.previous;
          this.next_page = data.next;
        })
        .catch(e => {
          this.$toast.error(e.message, {'position': 'top'});
        })
        .finally(() => {
          this.$store.commit('toggleLoader', false);
        });
    }
  }
}

</script>
<style scoped>
</style>
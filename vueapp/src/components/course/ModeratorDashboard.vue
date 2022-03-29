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
        <a href="#" @click="createDemoCourse" class="btn btn-primary btn-lg">
          Create Demo Course
        </a>
        <br><br>
        <div v-if="success">
          <!-- Alert Messages -->
          <div v-if="message" class="alert alert-success" role="alert">
            {{ message }}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
        </div>
        <div v-else>
          <!-- Alert Messages -->
          <div v-if="message" class="alert alert-danger" role="alert">
            {{ message }}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
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
                 <router-link class="btn btn-primary" :to="{name: 'course_contents', params: {course_id: course.id}}">
                    <i class="fa fa-tasks"></i>&nbsp;Manage Course
                  </router-link>
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
      <button
        class="btn btn-primary"
        @click="fetchMoreCourses"
        v-show="hasCourses"
      >Load More</button>
    </div>
  </div>
</template>
<script>
import CourseService from '../../services/CourseService';

export default {
  name: "ModeratorDasboard",
  data () {
    return {
      courses: [],
      nextPage: '',
      message: '',
      success: false,
    };
  },
  mounted () {
    this.getAllCourses();
  },
  computed: {
    hasCourses() {
      return this.courses.length > 0;
    }
  },
  methods: {
    getAllCourses() {
      this.$store.commit('toggleLoader', true);
        CourseService.getall().then(response => {
          var data = response.data;
          this.courses = data.results;
          this.nextPage = data.next;
        })
        .catch(e => {
          this.$toast.error(e.message, {'position': 'top'});
        })
        .finally(() => {
          this.$store.commit('toggleLoader', false);
        });
    },

    appendData(data) {
      data.forEach((course) => {
        this.courses.push(course)
      })
    },

    fetchMoreCourses() {
      if(this.nextPage != null) {
        const page = this.nextPage.split("?")[1];
        CourseService.more(page).then(response => {
          const data = response.data;
          this.appendData(data.results);
          this.nextPage = data.next;
        })
        .catch((e) => {
          console.log(e)
        });
      } else {
        this.$toast.info("No more courses", {'position': 'top'});
      }
    },
    createDemoCourse() {
      CourseService.createDemoCourse().then((response) => {
        const data = response.data;
        this.message = data.message;
        this.success = data.success;
      });
    }
  }
}

</script>
<style scoped>
</style>
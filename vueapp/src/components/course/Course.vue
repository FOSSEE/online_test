<template>
  <h1>{{message}}</h1>
  <div class="col-md-8">
    <button class="btn btn-outline-primary" type="button" @click="showCourse(null, false)">
      <i class="fa fa-plus-circle"></i>&nbsp;Add course
    </button>
  </div>
  <br>
  <div v-if="!courses" class="container">
    <div class="alert alert-info">
        <h3> No Courses Found </h3>
    </div>
  </div>
  <div v-else class="container-fluid">
    <div class="row">
      <div class="col-md-3">
        <form name=frm action="" @submit.prevent="searchCourses">
          <div class="card">
              <div class="card-header bg-secondary">
                  <h3>Search/Filter Courses</h3>
              </div>
              <div class="card-body">
                  <div>
                      <input type="text" name="search_tags" placeholder="Search by course name" class="form-control" v-model="searchName">
                      <br>
                      <select name="search_status" class="custom-select" v-model="searchStatus">
                        <option value="select">Select Status
                        </option>
                        <option value="active">Active</option>
                        <option value="closed">Inactive</option>
                      </select>
                  </div>
                  <br>
                  <button class="btn btn-outline-success" type="submit">
                      <i class="fa fa-search"></i>&nbsp;Search
                  </button>
              </div>
          </div>
        </form>
      </div>
      <div class="col">
        <div class="card" v-for="course in courses" :key="course.id">
          <div class="card-header bg-secondary">
            <div class="row">
              <div class="col-md-4">
                {{course.name}}
              </div>
              <div class="col-md-4">
                <span v-if="course.is_allotted" class="badge badge-pill badge-warning">Allotted Course</span>
                <span v-else class="badge badge-pill badge-primary">
                Created Course
                </span>
              </div>
              <div class="col">
                <li class="nav-item dropdown">
                    <a class="dropdown-toggle nav-link" id="user_dropdown" data-toggle="dropdown" href="#" style="color: blue;">More
                    </a>
                    <div class="dropdown-menu dropdown-menu-right">
                    <a class="dropdown-item" href="#" @click="showCourse(course.id, true)">
                      <i class="fa fa-edit"></i>
                      Edit Course
                    </a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#">
                        <i class="fa fa-clone"></i>
                        Clone Course
                    </a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item" href="#">
                        <i class="fa fa-download"></i>
                        Download CSV
                    </a>
                    </div>
                </li>
              </div>
            </div>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-4">
                <strong>Status:</strong>
                <span v-if="course.active" class="badge badge-pill badge-success">
                Active
                </span>
                <span v-else class="badge badge-pill badge-danger">
                Inactive
                </span>
                <br>
                <strong>Creator:</strong>
                {{course.creator_name}}
                <br>
              </div>
              <div class="col-md-4">
                <strong>Starts On:</strong>
                {{course.start_enroll_time}}
                <br>
                <strong>Ends On:</strong>
                {{course.end_enroll_time}}
              </div>
            </div>
          </div>
        </div>
        <br>
        <button class="btn btn-primary" @click="loadCourses">
        Load More</button>
        <br><br>
      </div>
    </div>
  </div>
  <div class="modal" tabindex="-1" role="dialog" id="courseModal">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Add/Edit Course</h5>
      </div>
      <form @submit.prevent="submitCourse">
      <div class="modal-body">
        <table class="table table-responsive-sm">
          <tr>
            <th>Name:</th>
            <td>
            <input type="text" class="form-control" name="name" v-model="edit_course.name" required="">
            </td>
          </tr>
          <tr>
            <th>Enrollment:</th>
            <td>
            <select required v-model="edit_course.enrollment" name="enrollment" class="custom-select">
              <option value="default">Request</option>
              <option value="open">Open</option>
            </select>
            </td>
          </tr>
          <tr>
            <th>Active:</th>
            <td>
              <input type="checkbox" v-model="edit_course.active" v-bind:id="edit_course.id" name="active">
            </td>
          </tr>
          <tr>
            <th>Code:</th>
            <td>
              <input type="text" class="form-control" name="code" v-model="edit_course.code">
            </td>
          </tr>
          <tr>
            <th>Instructions:</th>
            <td>
              <editor api-key="no-api-key" v-model="edit_course.instructions" />
            </td>
          </tr>
          <tr>
            <th>Enrollment Start Time:</th>
            <td>
              <v-date-picker v-model="edit_course.start_enroll_time" mode="dateTime" :timezone="timezone" :date-formatter="'YYYY-MM-DD h:mm:ss'">
                 <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded" :value="inputValue" v-on="inputEvents" />
                </template>
              </v-date-picker>
            </td>
          </tr>
          <tr>
            <th>Enrollment End Time:</th>
            <td>
              <v-date-picker v-model="edit_course.end_enroll_time" mode="dateTime" :timezone="timezone" :date-formatter="'YYYY-MM-DD h:mm:ss'">
                <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded" :value="inputValue" v-on="inputEvents" />
                </template>
              </v-date-picker>
            </td>
          </tr>
        </table>
      </div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-success">Save
        </button>
        <button type="button" class="btn btn-secondary" data-dismiss="modal" @click="closeModal">Close</button>
      </div>
      </form>
    </div>
  </div>
</div>
</template>
<script>
  import $ from 'jquery';
  import { mapState } from 'vuex';
  import CourseService from "../../services/CourseService"
  import Editor from '@tinymce/tinymce-vue'

  export default {
    name: "Course",
    components: {
      'editor': Editor
    },
    data() {
      return {
        message: "Courses",
        courses: [],
        next_page: '',
        course_name: '',
        course_status: '',
        edit_course: '',
        timezone: 'Asia/Kolkata',
        index: '',
        searchName: '',
        searchStatus: '',
      }
    },
    computed: {
      ...mapState({
          user: (state) => state.user_id,
      }),
    },
    mounted() {
      try {
        var user_id = document.getElementById("user_id").getAttribute("value");
      } catch {console.log("User error")}
      this.$store.commit('setUserId', user_id);
      this.getAllCourses();
    },
    methods: {
      appendData(data) {
        data.forEach((value) => {
          this.courses.push(value);
        });
      },
      searchCourses() {
        this.$store.commit('toggleLoader', true);
        CourseService.findByName(this.searchName, this.searchStatus).then(response => {
          this.$store.commit('toggleLoader', false);
          var data = response.data;
          this.courses = data.results
          this.next_page = data.next;
        })
        .catch(e => {
          this.$store.commit('toggleLoader', false);
          this.$toast.error(e.message, {'position': 'top'});
        });
      },
      loadCourses() {
        if (this.next_page != null) {
          var page = this.next_page.split("?")[1];
          this.$store.commit('toggleLoader', true);
          CourseService.more(page, this.searchName, this.searchStatus).then(response => {
            this.$store.commit('toggleLoader', false);
            var data = response.data;
            this.appendData(data.results);
            this.count = this.courses.length;
            this.next_page = data.next;
          })
          .catch(e => {
            this.$store.commit('toggleLoader', false);
            this.$toast.error(e.message, {'position': 'top'});
          });
        } else {
          this.$toast.info("No more courses", {'position': 'top'});
        }
      },
      showCourse(course, is_edit) {
        if(is_edit) {
          this.edit_course = this.getCourse(course)[0]
          this.index = this.courses.findIndex(x => x.id===course);
        } else {
          this.edit_course = {'owner': this.user}
        }
        $("#courseModal").show();
      },
      closeModal() {
        $("#courseModal").hide();
      },
      submitCourse() {
        this.$store.commit('toggleLoader', true);
        CourseService.create_or_update(this.edit_course.id, this.edit_course).then(response => {
            this.$store.commit('toggleLoader', false);
            var data = response.data;
            if (this.edit_course.id) {
              this.courses[this.index] = data
            }
            $("#courseModal").hide();
            this.$toast.success("Course saved successfully ", {'position': 'top'});
          })
          .catch(e => {
            this.$store.commit('toggleLoader', false);
            this.$toast.error(e.message, {'position': 'top'});
          });
      },
      getCourse(course) {
        var courses = JSON.parse(JSON.stringify(this.courses))
        return courses.filter((item) => {
          return (item.id === course)
        });
      },
      getAllCourses() {
        this.$store.commit('toggleLoader', true);
        CourseService.getall().then(response => {
          this.$store.commit('toggleLoader', false);
          var data = response.data;
          this.courses = data.results;
          this.previous_page = data.previous;
          this.next_page = data.next;
        })
        .catch(e => {
          this.$store.commit('toggleLoader', false);
          this.$toast.error(e.message, {'position': 'top'});
        });
      }
    },
  }
</script>
<style>
  .modal-dialog {
      overflow-y: initial !important
  }
  .modal-body {
      height: 80vh;
      overflow-y: auto;
  }
  .tox-notifications-container {
    display: none !important;
  }
</style>
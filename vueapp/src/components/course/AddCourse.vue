<template>
  <div>
      <h4>Add Course</h4>
    <div class="row">
      <div class="col-md-8">
        <ul class="nav nav-pills" id="course_tabs">
          <li class="nav-item">
            <a href="" class="nav-link">
              My Courses
            </a>
          </li>
          <li class="nav-item">
            <a href="" class="nav-link active">
              Add/Edit Course
            </a>
          </li>
          <li class="nav-item">
            <a href="" class="nav-link">
              Add/View Grading System
            </a>
          </li>
        </ul>
      </div>
    </div>
    <hr>
    <div class="container">
      <div v-if="error">
        <div
          v-if="message"
          class="alert alert-danger"
          role="alert">
          {{message}}
        </div>
      </div>
      <div v-else>
        <div
          v-if="message"
          class="alert alert-success"
          role="alert">
          {{message}}
        </div>
      </div>
      <form @submit.prevent="submitCourse">
        <table class="table table-responsive-sm">
          <tr>
            <th>Name:</th>
            <td>
            <input 
              type="text"
              class="form-control"
              v-model="courseName" requireds>
            <br>
            <strong class="text-danger"></strong>
            </td>
          </tr>
          <tr>
            <th>Enrollment:</th>
            <td>
            <select
              name="enrollment"
              class="custom-select"
              v-model="courseEnrollmentType">
              <option value="default">Request</option>
              <option value="open">Open</option>
            </select>
            <br>
            <strong class="text-danger"></strong>
            </td>
          </tr>
          <tr>
            <th>Active:</th>
            <td>
              <input
                type="checkbox"
                name="active"
                v-model="courseStatus">
              <br>
              <strong class="text-danger"></strong>
            </td>
          </tr>
          <tr>
            <th>Code:</th>
            <td>
              <input
                type="text"
                class="form-control"
                name="code"
                v-model="courseCode">
              <br>
              <strong class="text-danger"></strong>
            </td>
          </tr>
          <tr>
            <th>Instructions:</th>
            <td>
              <editor 
                api-key="no-api-key"
                v-model="courseInstructions"/>
              <br>
              <strong class="text-danger"></strong>
            </td>
          </tr>
          <tr>
            <th>Enrollment Start Time:</th>
            <td>
              <v-date-picker
                mode="dateTime"
                :timezone="timezone"
                :date-formatter="'YYYY-MM-DD h:mm:ss'"
                v-model="courseStartEnrollTime">
                  <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded"
                    :value="inputValue"
                    v-on="inputEvents" />
                  <br>
                  <strong class="text-danger">
                  </strong>
                </template>
              </v-date-picker>
            </td>
          </tr>
          <tr>
            <th>Enrollment End Time:</th>
            <td>
              <v-date-picker
                mode="dateTime"
                :timezone="timezone"
                :date-formatter="'YYYY-MM-DD h:mm:ss'"
                v-model="courseEndEnrollTime">
                <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded"
                    :value="inputValue"
                    v-on="inputEvents" />
                  <br>
                  <strong class="text-danger"></strong>
                </template>
              </v-date-picker>
            </td>
          </tr>
        </table>
        <button type="submit" class="btn btn-success">Save
        </button>
      </form>
    </div>
  </div>
</template>
<script>
import CourseService from "../../services/CourseService"
import Editor from '@tinymce/tinymce-vue';
import axios from 'axios';

axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

export default {
  name: "AddCourse",
  data () {
    return {
      toggleLoader: false,
      timezone: 'Asia/Kolkata',
      courseName: '',
      courseEnrollmentType: '',
      courseStatus: '',
      courseCode: '',
      courseInstructions: '',
      courseStartEnrollTime: '',
      courseEndEnrollTime: '',
      message: '',
      error: false,
    };
  },
  components: {
    'editor': Editor
  },
  mounted () {
  },
  methods: {
    async submitCourse () {
      const user_id = document.getElementById("user_id").getAttribute("value");
      const data = {
          'name': this.courseName,
          'enrollment': this.courseEnrollmentType,
          'active': this.courseStatus,
          'code': this.courseCode,
          'instructions': this.courseInstructions,
          'start_enroll_time': this.courseStartEnrollTime,
          'end_enroll_time': this.courseEndEnrollTime,
          'owner': user_id
      }
      this.toggleLoader = true;
      CourseService.create_or_update(null, data)
        .then((response) => {
          if (response.status == 201) {
            this.error = false;
            console.log('successfully created course');
            this.message = 'successfully created course'
          } else {
            this.error = true;
            console.log('Some error occured while creating course');
            this.message = 'Some error occured while creating course'
          }
        });
      this.toggleLoader = false;
    }
  },
}
</script>

<style scoped>
</style>
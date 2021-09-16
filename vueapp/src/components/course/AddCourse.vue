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
              v-model="fields.courseName" requireds>
            <br>
            <strong class="text-danger">{{ fieldErrors.courseName }}</strong>
            </td>
          </tr>
          <tr>
            <th>Enrollment:</th>
            <td>
            <select
              name="enrollment"
              class="custom-select"
              v-model="fields.courseEnrollmentType">
              <option value="default">Request</option>
              <option value="open">Open</option>
            </select>
            <br>
            <strong class="text-danger">{{ fieldErrors.courseEnrollmentType }}</strong>
            </td>
          </tr>
          <tr>
            <th>Active:</th>
            <td>
              <input
                type="checkbox"
                name="active"
                v-model="fields.courseStatus">
              <br>
            </td>
          </tr>
          <tr>
            <th>Code:</th>
            <td>
              <input
                type="text"
                class="form-control"
                name="code"
                v-model="fields.courseCode">
              <br>
            </td>
          </tr>
          <tr>
            <th>Instructions:</th>
            <td>
              <editor 
                api-key="no-api-key"
                v-model="fields.courseInstructions"/>
              <br>
            </td>
          </tr>
          <tr>
            <th>Enrollment Start Time:</th>
            <td>
              <v-date-picker
                mode="dateTime"
                :timezone="timezone"
                :date-formatter="'YYYY-MM-DD h:mm:ss'"
                v-model="fields.courseStartEnrollTime">
                  <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded"
                    :value="inputValue"
                    v-on="inputEvents" />
                  <br>
                  <strong class="text-danger">{{ fieldErrors.courseStartEnrollTime }}</strong>
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
                v-model="fields.courseEndEnrollTime">
                <template #default="{ inputValue, inputEvents }">
                  <input class="px-3 py-1 border rounded"
                    :value="inputValue"
                    v-on="inputEvents" />
                  <br>
                  <strong class="text-danger">{{ fieldErrors.courseEndEnrollTime }}</strong>
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
      error: false,
      message: '',
      timezone: 'Asia/Kolkata',
      fields: {
        courseName: '',
        courseEnrollmentType: '',
        courseStatus: '',
        courseCode: '',
        courseInstructions: '',
        courseStartEnrollTime: '',
        courseEndEnrollTime: '',
      },
      fieldErrors: {
        courseName: undefined,
        courseEnrollmentType: undefined,
        courseStartEnrollTime: undefined,
        courseEndEnrollTime: undefined
      }
    };
  },
  components: {
    'editor': Editor
  },
  methods: {
    async submitCourse () {
      const user_id = document.getElementById("user_id").getAttribute("value");
      this.fieldErrors = this.validateForm(this.fields);
      if(Object.keys(this.fieldErrors).length) return;
      const data = {
          'name': this.fields.courseName,
          'enrollment': this.fields.courseEnrollmentType,
          'active': this.fields.courseStatus,
          'code': this.fields.courseCode,
          'instructions': this.fields.courseInstructions,
          'start_enroll_time': this.fields.courseStartEnrollTime,
          'end_enroll_time': this.fields.courseEndEnrollTime,
          'owner': user_id
      }
      this.$store.commit('toggleLoader', true);
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
        this.$store.commit('toggleLoader', false);
    },
    validateForm (fields) {
      const errors = {};
      if(!fields.name) errors.courseName = 'Course name is required';
      if(!fields.enrollment) errors.courseEnrollmentType = 'Plase specify type of enrollment';
      if(!fields.start_enroll_time) {
        errors.courseStartEnrollTime = 'Please specify the start time for enrollment';
      }
      if(!fields.end_enroll_time) {
        errors.courseEndEnrollTime = 'Please specify the end time for enrollment';
      }
      return errors
    }
  },
}
</script>

<style scoped>
</style>
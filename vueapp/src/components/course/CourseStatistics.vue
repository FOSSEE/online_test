<template>
  <div>
    <CourseHeader v-if=is_ready v-bind:course_name=course_name />
    <div class="container-fluid">
      <div class="row">
        <div class="col-md-3">
            <CourseOptions v-if="is_ready" v-bind:course_id="course_id" v-bind:activeTab="active"/>
        </div>
        <div class="col">
          <table class="table table-responsive">
            <thead>
              <tr>
                <th>Sr No.</th>
                <th>Name</th>
                <th>Email</th>
                <th>Roll No</th>
                <th>Grade</th>
                <th>Percentage Completed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, idx) in statistics" :key="entry.id">
                <td> {{idx+1}} </td>
                <td> {{getFullName(entry.user.first_name, entry.user.last_name)}} </td>
                <td> {{ entry.user.email}} </td>
                <td> {{entry.user.profile.roll_number}} </td>
                <td> {{entry.grade}} </td>
                <td> {{entry.percent_completed}} </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  import CourseService from "../../services/CourseService"
  import CourseOptions from '../course/CourseOptions.vue';
  import CourseHeader from '../course/CourseHeader.vue';

  export default {
    name: "CourseStatistics",
    components: {
      CourseOptions, CourseHeader
    },
    data() {
      return {
        course_id: "",
        is_ready: false,
        course_name: "",
        statistics: [],
        active: 3
      }
    },
    mounted() {
      this.course_id = this.$route.params.course_id
      this.course_name = localStorage.getItem("course_"+this.course_id)
      this.is_ready = true;
      this.$store.commit('toggleLoader', true);
      CourseService.getStatistics(this.course_id).then(response => {
        this.statistics = response.data;
      })
      .catch(e => {
        this.$toast.error(e.message, {'position': 'top'});
      })
      .finally(() => {
        this.$store.commit('toggleLoader', false);
      });
    },
    methods: {
      getFullName(first_name, last_name) {
        return first_name + " " + last_name
      },
    }
  }
</script>
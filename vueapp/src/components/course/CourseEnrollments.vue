<template>
    <div>
        <div class="col-md-3">
            <router-link :to="{name: 'courses'}" class="btn btn-outline-primary btn-sm">
            <i class="fa fa-arrow-left"></i>&nbsp;Back
            </router-link>
        </div>
        <div class="course">
            <h1>{{course_name}}</h1>
        </div>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3">
                    <CourseOptions v-if=is_ready v-bind:course_id=course_id />
                </div>
                <div class="col-md-9">
                    <div class="row">
                        <div class="col-md-2">
                            <h3>Filter By:</h3>
                        </div>
                        <div class="col-md-3">
                            <div class="btn-group" role="group" aria-label="Basic example">
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(3)">Enrolled</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(2)">Rejected</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(1)">Pending</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(0)">All</button>
                            </div>
                        </div>
                    </div>
                    <br><br>
                    <table class="table table-responsive">
                        <thead>
                            <tr>
                            <th v-show="has_filtered"><input type="checkbox" v-model="allSelected" @change="selectAll()">&nbsp;Select all</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Roll Number</th>
                            <th>Institute</th>
                            <th>Department</th>
                            <th>Status</th>
                            <th>Requested time</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="enroll in filtered"
                                :key="enroll.id"
                            >
                                <td><input type="checkbox" :value="enroll.id" v-model="selected" @change="select()" /></td>
                                <td>{{getFullName(enroll.student.user.first_name, enroll.student.user.last_name)}}</td>
                                <td>{{enroll.student.user.email}}</td>
                                <td>{{enroll.student.roll_number}}</td>
                                <td>{{enroll.student.institute}}</td>
                                <td>{{enroll.student.department}}</td>
                                <td>
                                    <span :class="Badge(enroll.status)">
                                        {{getEnrollmentStatus(enroll.status)}}
                                    </span>
                                </td>
                                <td>{{enroll.requested_on}}</td>
                            </tr>
                        </tbody>
                    </table>
                    <br>
                    <button class="btn btn-success btn-md" @click="submitEnrollment(3)" v-show="has_filtered" :disabled="!has_selected">
                        Enroll
                    </button>
                    <button class="btn btn-warning btn-md" @click="submitEnrollment(2)" v-show="has_filtered" :disabled="!has_selected">
                        Reject
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
<script>

import CourseService from "../../services/CourseService"
import CourseOptions from '../course/CourseOptions.vue';

export default {
    name: "CourseEnrollments",
    components: {
        CourseOptions
    },
    data() {
        return {
            students: [],
            course_id: '',
            is_ready: false,
            course_name: "",
            enrollment_status: {
                1: "Pending",
                2: "Rejected",
                3: "Enrolled"
            },
            filtered: [],
            selected: [],
            allSelected: false,
        }
    },
    computed: {
      has_filtered() {
        return this.filtered.length > 0;
      },
      has_selected() {
        return this.selected.length > 0;
      }
    },
    mounted() {
        this.course_id = this.$route.params.course_id
        this.course_name = localStorage.getItem("course_"+this.course_id)
        this.is_ready = true;
        this.$store.commit('toggleLoader', true);
        CourseService.getEnrollments(this.course_id).then(response => {
          var data = response.data;
          this.students = data;
          this.filtered = data;
        })
        .catch(e => {
          this.$toast.error(e.message, {'position': 'top'});
        })
        .finally(() => {
          this.$store.commit('toggleLoader', false);
        });
    },
    methods: {
        getEnrollmentStatus(status) {
            return this.enrollment_status[status];
        },
        Badge(status) {
            var badge = "";
            switch (status) {
                case 1:
                    badge = "badge badge-warning"
                    break;
                case 2:
                    badge = "badge badge-danger"
                    break;
                case 3:
                    badge = "badge badge-success"
                    break;
                default:
                    break;
            }
            return badge
        },
        getFullName(first_name, last_name) {
            return first_name + " " + last_name
        },
        filterStudents(status) {
            if(status==0) {
                this.filtered = this.students
            } else {  
                this.filtered = this.students.filter(student => {
                    return student.status == status;
                });
            }
        },
        submitEnrollment(status) {
            var data = {"students": this.selected, "status": status}
            this.$store.commit('toggleLoader', true);
            CourseService.setEnrollments(this.course_id, data).then(response => {
                var data = response.data;
                this.students = data;
                this.filtered = data;
                this.selected = [];
                this.allSelected = false;
                this.$toast.success("Enrollments updated successfully", {'position': 'top'});
            })
            .catch(e => {
                this.$toast.error(e.message, {'position': 'top'});
            })
            .finally(() => {
                this.$store.commit('toggleLoader', false);
            });
        },
        selectAll() {
            this.selected = [];
            if (this.allSelected) {
                for(var user in this.students) {
                    this.selected.push(this.students[user].id);
                }
            }
        },
        select() {
            this.allSelected = false;
        }
    }
}
</script>
<style scoped>
  .course {
    display: flex;
    justify-content: center;
  }
</style>
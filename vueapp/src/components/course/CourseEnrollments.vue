<template>
    <div>
        <CourseHeader v-if=is_ready v-bind:course_name=course_name />
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3">
                    <CourseOptions v-if=is_ready v-bind:course_id=course_id />
                </div>
                <div class="col">
                    <div class="row">
                        <div class="col-md-2">
                            <h3>Filter By:</h3>
                        </div>
                        <div class="col-md-3">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(3)">Enrolled</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(2)">Rejected</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(1)">Pending</button>
                                <button type="button" class="btn btn-secondary btn-md" @click="filterStudents(0)">All</button>
                            </div>
                        </div>
                    </div>
                    <br><br>
                    <div v-show="has_filtered">
                    <input type="checkbox" v-model="allSelected" @change="selectAll()">&nbsp;Select all
                    </div>
                    <div class="list-group">
                        <DynamicScroller
                            class="scroller"
                            :items="filtered"
                            :min-item-size="54"
                            key-field="id"
                            >
                                <template v-slot="{ item, index, active }">
                                    <DynamicScrollerItem
                                        :item="item"
                                        :active="active"
                                        :size-dependencies="[
                                            item.student.profile.institute,
                                        ]"
                                        :data-index="index"
                                    >
                                        <div class="list-group-item flex-column align-items-start user">
                                            <div class="row">
                                                <div class="col-md-1">
                                                    <input type="checkbox" :value="item.id" v-model="selected" @change="select()" />
                                                </div>
                                                <div class="col-md-3">
                                                    {{getFullName(item.student.first_name, item.student.last_name)}}
                                                </div>
                                                <div class="col-md-4">
                                                    {{item.student.email}}
                                                </div>
                                                <div class="col-md-4">
                                                    {{item.student.profile.roll_number}}
                                                </div>
                                            </div>
                                            <div class="d-flex w-100 justify-content-end">
                                            <small>
                                                <span :class="Badge(item.status)">
                                                {{getEnrollmentStatus(item.status)}}
                                                </span>
                                            </small>
                                            <small>&nbsp;{{item.created_on}}</small>
                                            </div>
                                        </div>
                                    </DynamicScrollerItem>
                                </template>
                        </DynamicScroller>
                    </div>
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
import CourseHeader from '../course/CourseHeader.vue';
import { DynamicScroller, DynamicScrollerItem } from 'vue3-virtual-scroller';
import 'vue3-virtual-scroller/dist/vue3-virtual-scroller.css'

export default {
    name: "CourseEnrollments",
    components: {
        CourseOptions, DynamicScroller, DynamicScrollerItem,
        CourseHeader
    },
    data() {
        return {
            students: [],
            course_id: '',
            is_ready: false,
            course_name: "",
            filtered: [],
            selected: [],
            enrollment_status: {
                1: "Pending",
                2: "Rejected",
                3: "Enrolled"
            },
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
    watch: {
        allSelected: function() {
            this.selectAll();
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
        },
        showPopover(institute, department) {
            alert(institute + department);
        }
    }
}
</script>
<style scoped>
.scroller {
height: 100vh;
}
</style>
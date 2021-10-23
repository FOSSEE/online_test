<template>
    <div>
        <CourseHeader v-if=is_ready v-bind:course_name=course_name />
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3">
                    <CourseOptions v-if="is_ready" v-bind:course_id="course_id" v-bind:activeTab="active"/>
                </div>
                <div class="col">
                    <div>
                        <h3>Existing Teachers/TAs</h3>
                    </div>
                    <div v-show="has_current">
                        <table class="table table-responsive">
                            <thead>
                                <tr>
                                <th>Select</th>
                                <th>Name</th>
                                <th>Email</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr
                                    v-for="item in current_teachers"
                                    :key="item.id"
                                >
                                    <td><input type="checkbox" :value="item.id" v-model="selected"></td>
                                    <td>{{getFullName(item.teacher.first_name, item.teacher.last_name)}}</td>
                                    <td>{{item.teacher.email}}</td>
                                </tr>
                            </tbody>
                        </table>
                        <div>
                            <button class="btn btn-danger btn-sm" @click="removeTeachers()" v-show="has_current" :disabled="!has_selected">
                                Remove
                            </button>
                        </div>
                    </div>
                    <div v-show="!has_current">
                        <span class="badge badge-warning">No Teachers/TAs added</span>
                    </div>
                    <hr>
                    <h3>Search Users</h3>
                    <form @submit.prevent="searchTeachers">
                    <div class="input-group mb-3">
                        <input type="text" class="form-control" placeholder="Search by username, email and name" v-model="search_text" required>
                        <div class="input-group-append">
                            <select class="custom-select" v-model="search_by">
                                <option value="">Search By</option>
                                <option value="name">Name</option>
                                <option value="email">Email</option>
                                <option value="username">Username</option>
                            </select>
                            <button type="submit" class="btn btn-outline-primary">Search</button>
                        </div>
                    </div>
                    </form>
                    <div v-show="has_filtered">
                        <div>
                            <span class="badge badge-success"> Found {{SearchCount}} user(s)</span>
                        </div>
                        <br>
                        <div>
                            <input type="checkbox" v-model="allSelected" @change="selectAll()">&nbsp;Select all
                        </div>
                        <div class="list-group">
                            <DynamicScroller
                                class="scroller"
                                :items="search_teachers"
                                :min-item-size="54"
                                key-field="id"
                                >
                                <template v-slot="{ item, index, active }">
                                    <DynamicScrollerItem
                                        :item="item"
                                        :active="active"
                                        :size-dependencies="[
                                            item.profile.institute,
                                        ]"
                                        :data-index="index"
                                    >
                                        <div class="list-group-item flex-column align-items-start user">
                                            <div class="row">
                                                <div class="col-md-1">
                                                    <input type="checkbox" :value="item.id" v-model="to_add" />
                                                </div>
                                                <div class="col-md-3">
                                                    {{getFullName(item.first_name, item.last_name)}}
                                                </div>
                                                <div class="col-md-4">
                                                    {{item.email}}
                                                </div>
                                            </div>
                                            <div class="d-flex w-100 justify-content-start">
                                                {{item.profile.institute}}
                                            </div>
                                        </div>
                                    </DynamicScrollerItem>
                                </template>
                            </DynamicScroller>
                        </div>
                        <br>
                        <button class="btn btn-success btn-md" @click="addTeachers()" v-show="has_filtered" :disabled="!has_added">
                            Submit
                        </button>
                    </div>
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
    name: "CourseTeachers",
    components: {
        CourseHeader, CourseOptions, DynamicScroller,
        DynamicScrollerItem
    },
    data() {
        return {
            current_teachers: [],
            search_teachers: [],
            course_name: "",
            is_ready: false,
            selected: [],
            to_add: [],
            remove: [],
            allSelected: false,
            search_by: "",
            search_text: "",
            course_id: '',
            active: 4
        }
    },
    computed: {
      has_selected() {
        return this.selected.length > 0;
      },
      has_added() {
          return this.to_add.length > 0;
      },
      has_filtered() {
        return this.search_teachers.length > 0;
      },
      has_current() {
        return this.current_teachers.length > 0;
      },
      SearchCount() {
          return this.search_teachers.length
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
        CourseService.getTeachers(this.course_id).then(response => {
          this.current_teachers = response.data;
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
        searchTeachers() {
            var data = {"search_by": this.search_by, "action": "search",
                        "u_name": this.search_text}
            this.$store.commit('toggleLoader', true);
            CourseService.setTeachers(this.course_id, data).then(response => {
                this.search_teachers = response.data;
            })
            .catch(e => {
                this.$toast.error(e.message, {'position': 'top'});
            })
            .finally(() => {
                this.$store.commit('toggleLoader', false);
            });
        },
        addTeachers() {
            var data = {"users": this.to_add, "action": "add"}
            this.$store.commit('toggleLoader', true);
            CourseService.setTeachers(this.course_id, data).then(response => {
                this.current_teachers = response.data;
                this.to_add = [];
                this.search_teachers = [];
                this.allSelected = false;
                this.$toast.success("Teachers updated successfully", {'position': 'top'});
            })
            .catch(e => {
                this.$toast.error(e.message, {'position': 'top'});
            })
            .finally(() => {
                this.$store.commit('toggleLoader', false);
            });
        },
        removeTeachers() {
            var data = {"users": this.selected, "action": "delete"}
            this.$store.commit('toggleLoader', true);
            CourseService.setTeachers(this.course_id, data).then(response => {
                this.current_teachers = response.data;
                this.selected = [];
                this.allSelected = false;
                this.$toast.success("Teachers updated successfully", {'position': 'top'});
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
                for(var user in this.search_teachers) {
                    this.selected.push(this.search_teachers[user].id);
                }
            }
        },
    }
}
</script>
<style>
.scroller {
    height: 100vh;
}
</style>
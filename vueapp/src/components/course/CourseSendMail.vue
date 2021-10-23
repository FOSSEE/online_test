<template>
    <div>
        <CourseHeader v-if=is_ready v-bind:course_name=course_name />
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3">
                    <CourseOptions v-if="is_ready" v-bind:course_id="course_id" v-bind:activeTab="active"/>
                </div>
                <div class="col">
                    <div class="alert alert-warning"  v-show="!has_filtered">
                        No Students Found
                    </div>
                    <br><br>
                    <div v-show="has_filtered">
                    <input type="checkbox" v-model="allSelected" @change="selectAll()">&nbsp;Select all
                    </div>
                    <div class="list-group">
                        <DynamicScroller
                            class="scroller"
                            :items="students"
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
                                                    <input type="checkbox" :value="item.student.id" v-model="selected" @change="select()" />
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
                                        </div>
                                    </DynamicScrollerItem>
                                </template>
                        </DynamicScroller>
                    </div>
                    <br>
                    <form @submit.prevent="sendMail()"  v-show="has_filtered">
                    <div class="card">
                        <div class="card-body">
                            <textarea v-model="subject" placeholder="Enter email subject" class="form-control" required></textarea>
                            <br>
                            <editor api-key="no-api-key" v-model="body"/>
                        </div>
                    </div>
                    <br>
                    <button type="submit" class="btn btn-success btn-md" :disabled="!enableButton">
                        Send
                    </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
    import CourseService from "../../services/CourseService"
    import CourseOptions from '../course/CourseOptions.vue';
    import CourseHeader from '../course/CourseHeader.vue';
    import Editor from '@tinymce/tinymce-vue'
    import { DynamicScroller, DynamicScrollerItem } from 'vue3-virtual-scroller';
    import 'vue3-virtual-scroller/dist/vue3-virtual-scroller.css'

    export default {
        name: "CourseSendMail",
        components: {
            CourseOptions, DynamicScroller, DynamicScrollerItem,
            CourseHeader, 'editor': Editor
        },
        data() {
            return {
                students: [],
                course_id: '',
                is_ready: false,
                course_name: "",
                selected: [],
                allSelected: false,
                subject: "",
                body: "",
                active: 5
            }
        },
        computed: {
            has_filtered() {
                return this.students.length > 0;
            },
            has_selected() {
                return this.selected.length > 0;
            },
            enableButton() {
                return this.has_selected && this.subject !== "" && this.body !== "";
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
            CourseService.getEnrollments(this.course_id, 3).then(response => {
                var data = response.data;
                this.students = data;
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
            sendMail() {
                var data = {"students": this.selected, "subject": this.subject, "body": this.body}
                this.$store.commit('toggleLoader', true);
                CourseService.sendMail(this.course_id, data).then(response => {
                    var data = response.data;
                    this.selected = [];
                    this.allSelected = false;
                    this.subject = ""
                    this.body = ""
                    this.$toast.info(data.message, {'position': 'top'});
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
                        this.selected.push(this.students[user].student.id);
                    }
                }
            },
            select() {
                this.allSelected = false;
            }
        }
    }
</script>

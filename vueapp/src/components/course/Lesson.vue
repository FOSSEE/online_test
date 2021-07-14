<template>
  <div class="modal" tabindex="-1" role="dialog" id="lessonModal">
    <div class="modal-dialog mw-100 w-75" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add/Edit Lesson</h5>
        </div>
        <div class="row">
          <div class="col-md-6">
            <form @submit.prevent="submitLesson">
              <div class="modal-body">
                <table class="table table-responsive-sm">
                  <tr>
                    <th>Name:</th>
                    <td>
                    <input type="text" class="form-control" name="name" v-model="lesson.name" required="">
                    <br>
                    <strong class="text-danger" v-show="error.name">{{error.name}}</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Description:</th>
                    <td>
                      <editor api-key="no-api-key" v-model="lesson.description" />
                    <br>
                    <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Active:</th>
                    <td>
                      <input type="checkbox" v-model="lesson.active" v-bind:id="lesson.id" name="active">
                      <br>
                      <strong class="text-danger" v-show="error.active">{{error.active}}</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Video Source:</th>
                    <td>
                      <select name="video_option" class="custom-select" v-model="video_src">
                        <option value="---">Select Video Option</option>
                        <option value="youtube" selected="">Youtube</option>
                        <option value="vimeo">Vimeo</option>
                        <option value="others">Others</option>
                      </select>
                      <strong class="text-danger" v-show="error.video_path">{{error.video_path}}</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Video Id/URL:</th>
                    <td>
                      <input type="input" v-model="video_id" class="form-control" />
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
          <div class="col-md-5">
            <div class="card">
              <div class="card-header">
                Table of Contents
              </div>
              <div class="card-body">
                
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  import $ from 'jquery';
  import { mapState } from 'vuex';
  import Editor from '@tinymce/tinymce-vue'
  import LessonService from "../../services/LessonService"
  export default {
    name: "Lesson",
    components: {
      'editor': Editor
    },
    computed: {
      ...mapState({
          user: (state) => state.user_id,
          course_id: (state) => state.course_id,
          lesson: (state) => state.lesson
      }),
      existing() {
        return 'id' in this.lesson
      },
    },
    data() {
      return {
        error: {},
        video_src: '',
        video_id: ''
      }
    },
    mounted() {
      $("#lessonModal").show();
      this.lesson["video_path"] = {"youtube": "3-wJZj8LeGA"}
      try{
      this.video_src = Object.keys(this.lesson["video_path"])[0];
      this.video_id = this.lesson["video_path"][this.video_src]
      } catch(e) {
        console.log(e)
      }
    },
    methods: {
      closeModal() {
        this.$store.dispatch('toggleLesson', false)
      },
      submitLesson() {
        this.$store.commit('toggleLoader', true);
        this.lesson["video_path"] = {video_src: this.video_id}
        LessonService.create_or_update(this.lesson.id, this.lesson).then(response => {
            this.$store.commit('toggleLoader', false);
            this.$emit("updateLessons", {"data": response.data, "existing": this.existing})
            this.$toast.success("Lesson saved successfully ", {'position': 'top'});
          })
          .catch(e => {
            this.$store.commit('toggleLoader', false);
            console.log(e)
            var data = e.response.data;
            if (data) {
              this.showError(e.response.data)
            } else {
              this.$toast.error(e.message, {'position': 'top'});
            }
          });
      },
      showError(err) {
        if ("detail" in err) {
          this.$toast.error(err.detail, {'position': 'top'});
        } else {
          this.error = err
        }
      },
    }
  }
</script>
<style scoped>
  .modal {
    width:  100%;
  }
</style>
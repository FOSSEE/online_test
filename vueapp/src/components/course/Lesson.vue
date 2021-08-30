<template>
  <div class="modal" tabindex="-1" role="dialog" id="lessonModal">
    <div class="modal-dialog mw-100 w-78" role="document">
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
                    <input type="text" class="form-control"  v-model="lesson.name" required="">
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
                      <input type="checkbox" v-model="lesson.active" v-bind:id="lesson.id">
                      <br>
                      <strong class="text-danger" v-show="error.active">{{error.active}}</strong>
                    </td>
                  </tr>
                  <tr>
                    <th>Video Source:</th>
                    <td>
                      <select class="custom-select" v-model="video_src">
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
                <div>
                  <button type="submit" class="btn btn-success">Save
                  </button>
                  <button type="button" class="btn btn-secondary" data-dismiss="modal" @click="closeModal">Close
                  </button>
                </div>
              </div>
            </form>
          </div>
          <div class="col-md-5">
            <toc v-if="has_video" :video_src="video_src" :video_id="video_id" :is_others="is_others" :lesson_id="lesson.id">
            </toc>
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
  import TableOfContents from "../course/TableOfContents.vue"
  export default {
    name: "Lesson",
    components: {
      'editor': Editor,
      'toc': TableOfContents,
    },
    computed: {
      ...mapState({
        user: (state) => state.user_id,
        course_id: (state) => state.course_id,
        lesson: (state) => state.lesson
      }),
      existing() {
        return 'id' in this.lesson
      }
    },
    data() {
      return {
        error: {},
        video_src: '',
        video_id: '',
        module_id: '',
        player: {},
        player_data: {},
        is_others: false,
        has_video: false
      }
    },
    mounted() {
      $("#lessonModal").show();
      this.updateSource();
      this.module_id = this.lesson['module_id']
    },
    methods: {
      closeModal() {
        this.$store.dispatch('toggleLesson', false)
      },
      submitLesson() {
        this.$store.commit('toggleLoader', true);
        this.lesson["video_path"] = {[this.video_src]: this.video_id}
        LessonService.create_or_update(this.module_id, this.lesson.id, this.lesson).then(response => {
            if(this.lesson && !this.lesson.id) {
              this.closeModal();
            }
            this.$emit("updateLessons", {"data": response.data, "existing": this.existing})
            this.$toast.success("Lesson saved successfully ", {'position': 'top'});
          })
          .catch(e => {
            var data = e.response.data;
            if (data) {
              this.showError(e.response.data)
            } else {
              this.$toast.error(e.message, {'position': 'top'});
            }
          })
          .finally(() => {
            this.$store.commit('toggleLoader', false);
          });
        try {
          this.has_video = false
          this.updateSource();
        } catch (e) {
          console.log(e)
        }
      },
      showError(err) {
        if ("detail" in err) {
          this.$toast.error(err.detail, {'position': 'top'});
        } else {
          this.error = err
        }
      },
      setPlayersource() {
        var source;
        if(this.video_src=="others") {
          this.is_others = true;
          source = [{src: this.video_id, type: 'video/mp4'}]
        } else {
          this.is_others = false;
          source = [{src: this.video_id, provider: this.video_src}]
        }
        this.player.source = {type: "video", sources: source}
      },
      updateSource() {
        try {
          this.video_src = Object.keys(this.lesson["video_path"])[0];
          if(this.video_src=="others") {
            this.is_others = true;
          }
          this.video_id = this.lesson["video_path"][this.video_src]
          this.has_video = true
        } catch(e) {
          console.log(e)
        }
      },
    }
  }
</script>
<style scoped>
  .modal {
    width:  100%;
    overflow-y: scroll;
  }
</style>
<template>
<div>
  <div class="card">
    <div class="card-header">
      Table of Contents
    </div>
    <div class="card-body">
      <table class="table table-responsive" v-show="containsTOC">
        <tr v-for="content in contents" :key="content.id">
          <td v-if="content.ctype == 'Topic'">{{content.name}}</td>
          <td v-else>{{content.summary}}</td>
          <td>{{content.ctype}}</td>
          <td>{{content.time}}</td>
          <td>
            <button class="btn btn-outline-info btn-sm" @click="editToc(content, content.ctype)">
              <i class="fa fa-edit"></i>&nbsp;Edit
            </button>
          </td>
          <td>
            <button class="btn btn-outline-danger btn-sm" @click="deleteToc(content.toc_id, content.ctype)">
              <i class="fa fa-trash"></i>&nbsp;Delete
            </button>
          </td>
        </tr>
      </table>
      <div class="no-contents">
        <span class="badge badge-warning" v-show="!containsTOC">No content found
        </span>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      Add Table of Contents
    </div>
    <div class="card-body">
      <div v-if="is_others">
        <video id="player" playsinline controls >
          <source :src="video_id" />
        </video>
      </div>
      <div v-else>
        <div id="player" :data-plyr-provider="video_src" :data-plyr-embed-id="video_id">
        </div>
      </div>
      <br>
      <form @submit.prevent="addToc">
        <div class="row">
          <div class="col-md-3">
              <input type="text" class="form-control" v-model="time" required="">
          </div>
          <div class="col-md-5">
            <select class="custom-select" required="" v-model="content_type">
                <option value="0" selected="">Select Content Type</option>
                <option value="1">Topic</option>
                <option value="2">Graded Quiz</option>
                <option value="3">Exercise</option>
                <option value="4">Poll</option>
            </select>
          </div>
        </div>
      </form>
      <hr>
      <topic v-if="enable_topic" v-bind:lesson_id="lessonId" v-bind:topic="topic" v-bind:time="time" v-on:updateToc="updateToc">
      </topic>
      <question v-if="enable_ques" v-bind:lesson_id="lessonId" v-bind:question="question" v-bind:time="time" v-on:updateToc="updateToc" v-bind:content_type="content_type">
      </question>
    </div>
  </div>
</div>
</template>
<script>
  import { mapState } from 'vuex';
  import Plyr from 'plyr'
  import Topic from "../course/Topic.vue"
  import Question from "../question/Question.vue"
  import Utils from "../../services/Utils"
  import LessonService from "../../services/LessonService"
  export default {
    name: "TableOfContents",
    components: {
      'topic': Topic,
      'question': Question
    },
    props: {
      is_others: Boolean,
      video_src: String,
      video_id: String,
      lesson_id: Number,
    },
    computed: {
      ...mapState({
          user: (state) => state.user_id,
      }),
      containsTOC() {
        return this.contents.length > 0
      }
    },
    data() {
      return {
        time: "00:00:00",
        content_type: "0",
        enable_ques: false,
        lessonId: -1,
        enable_topic: false,
        topic: {},
        question: {},
        contents: []
      }
    },
    watch: {
      content_type(val) {
        if(val === "0") {
          this.enable_ques = false
          this.enable_topic = false
        }
        else if (val === "1") {
          this.enable_ques = false
          this.topic = {"time": this.time}
          this.enable_topic = true
        }
        else {
          this.enable_topic = false
          this.question = {"time": this.time, "test_cases": [], "ctype": val, "user": this.user}
          this.enable_ques = true
        }
      },
      time(val) {
        this.player.currentTime = Utils.convertToSeconds(val)
      },
      video_id(val) {
        var source;
        if(this.video_src=="others") {
          source = [{src: val, type: 'video/mp4'}]
        } else {
          source = [{src: val, provider: this.video_src}]
        }
        this.player.source = {type: "video", sources: source}
      },
    },
    mounted() {
      this.lessonId = this.lesson_id;
      this.$store.commit('toggleLoader', true);
      LessonService.get_toc(this.lesson_id).then(response => {
          this.contents = response.data
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
      this.$nextTick(() => {
        this.player = new Plyr('#player');
        this.player.on('timeupdate', () => {
          this.time = Utils.convertFromSeconds(parseInt(this.player.currentTime))
        });
      });
    },
    methods: {
      showError(err) {
        if ("detail" in err) {
          this.$toast.error(err.detail, {'position': 'top'});
        }
      },
      deleteToc(toc_id, type) {
        LessonService.delete_toc(this.lesson_id, toc_id)
          .then(response => {
            this.$store.commit('toggleLoader', false);
            this.contents = response.data
            this.$toast.success(`${type} deleted successfully`, {'position': 'top'});
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
      },
      editToc(toc, type) {
        if(type == 'Topic') {
          this.topic = toc
          this.enable_topic = true
          this.enable_ques = false
        } else {
          this.question = toc
          this.enable_topic = false
          this.enable_ques = true
        }
      },
      updateToc(data) {
        this.contents = data.tocs
        this.enable_topic = false
        this.enable_ques = false
      }
    }
  }
</script>
<style scoped>
  .no-contents {
    text-align: center;
  }
</style>
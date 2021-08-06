<template>
  <div class="card">
    <div class="card-header">
      Table of Contents
    </div>
    <div class="card-body">
      <table class="table table-responsive-sm">
        <tr>
          <th>Sr No.</th>
          <th>Name</th>
          <th>Type</th>
          <th>Time</th>
        </tr>
        <tr v-for="(content, idx) in contents" :key="content.id">
          <td>{{idx+1}}</td>
          <td>{{content.name}}</td>
          <td>{{content.type}}</td>
          <td>{{content.time}}</td>
        </tr>
      </table>
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
          <div class="col-md-4">
            <select class="custom-select" required="" v-model="content_type">
                <option value="" selected="">Select Content Type</option>
                <option value="1">Topic</option>
                <option value="2">Graded Quiz</option>
                <option value="3">Exercise</option>
                <option value="4">Poll</option>
            </select>
          </div>
          <div class="col-md-4">
            <select name="type" class="custom-select" :required="is_que" :disabled="!is_que">
              <option value="" selected="">Select question type</option>
              <option value="mcq">Single Correct Choice</option>
              <option value="mcc">Multiple Correct Choices</option>
              <option value="integer">Answer in Integer</option>
              <option value="string">Answer in String</option>
              <option value="float">Answer in Float</option>
            </select>
          </div>
        </div>
      </form>
      <hr>
      <topic v-if="enable_topic" v-model:lesson_id="lessonId" v-model:time="time">
      </topic>
    </div>
  </div>
</template>
<script>
  import Plyr from 'plyr';
  import Topic from "../course/Topic.vue"
  import Utils from "../../services/Utils"
  import LessonService from "../../services/LessonService"
  export default {
    name: "TableOfContents",
    components: {
      'topic': Topic,
    },
    props: {
      is_others: Boolean,
      video_src: String,
      video_id: String,
      lesson_id: Number,
    },
    data() {
      return {
        time: "00:00:00",
        content_type: "",
        is_que: false,
        lessonId: -1,
        enable_topic: false,
        video_data: {
          others: false,
          src: "",
          id: ""
        },
        contents: []
      }
    },
    watch: {
      content_type(val) {
        if(val === "") {
          this.is_que = false
          this.enable_topic = false
        }
        else if (val === "1") {
          this.is_que = false
          this.enable_topic = true
        }
        else {
          this.enable_topic = false
          this.is_que = true
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
      LessonService.get_toc(this.lesson_id).then(response => {
          this.contents = response.data
        })
        .catch(e => {
          this.$store.commit('toggleLoader', false);
          var data = e.response.data;
          if (data) {
            this.showError(e.response.data)
          } else {
            this.$toast.error(e.message, {'position': 'top'});
          }
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
      }
    }
  }
</script>
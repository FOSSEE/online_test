<template>
<div>
  <h3>Add/Edit Topic</h3>
  <form @submit.prevent="submitTopic">
    <p>
      <label for="id_name">Summary:</label> <input type="text" v-model="topic_data.name" maxlength="255" class="form-control" placeholder="Name" required="" id="id_name">
      <strong class="text-danger" v-show="error.name">{{error.name}}
      </strong>
    </p>
    <p>
      <label for="id_description">Description:</label> <editor api-key="no-api-key" v-model="topic_data.description" id="id_description" />
    </p>
      <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
      <p><label for="id_timer">Timer:</label> <input type="text" v-model="topic_data.time" class="form-control" placeholder="Time" required="" id="id_timer"></p>
    <br>
    <button type="submit" class="btn btn-success">
      Save
    </button>
  </form>
</div>
</template>
<script>
  import Editor from '@tinymce/tinymce-vue'
  import LessonService from "../../services/LessonService"
  export default {
    name: "Topic",
    components: {
      'editor': Editor,
    },
    props: {
      time: String,
      lesson_id: Number,
      topic: Object
    },
    emits: ["updateToc"],
    watch: {
      time(val) {
        this.topic_data.time = val
      },
      topic(val) {
       this.topic_data = val
      }
    },
    data() {
      return {
        error: {},
        topic_data: {}
      }
    },
    mounted() {
      this.topic_data = this.topic
    },
    methods: {
      submitTopic() {
        this.topic_data["ctype"] = 1
        LessonService.add_or_edit_toc(this.lesson_id, this.topic_data.toc_id, this.topic_data).then(response => {
            console.log(response.data)
            this.$toast.success("Topic saved successfully ", {'position': 'top'});
            this.$emit("updateToc", {"tocs": response.data})
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
      showError(err) {
        if ("detail" in err) {
          this.$toast.error(err.detail, {'position': 'top'});
        } else {
          this.error = err
        }
      }
    }
  }
</script>
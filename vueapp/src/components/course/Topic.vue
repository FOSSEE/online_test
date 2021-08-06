<template>
  <h3>Add/Edit Topic</h3>
  <form @submit.prevent="submitTopic">
    <p>
      <label for="id_name">Name:</label> <input type="text" v-model="topic_data.name" maxlength="255" class="form-control" placeholder="Name" required="" id="id_name">
      <strong class="text-danger" v-show="error.name">{{error.name}}</strong>
    </p>
    <p>
      <label for="id_description">Description:</label> <textarea v-model="topic_data.description" cols="40" rows="10" class="form-control" placeholder="Description" id="id_description"></textarea></p>
      <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
      <p><label for="id_timer">Timer:</label> <input type="text" v-model="topic_data.time" class="form-control" placeholder="Time" required="" id="id_timer"></p>
    <br>
    <button type="submit" class="btn btn-success">
      Save
    </button>
  </form>
</template>
<script>
  import LessonService from "../../services/LessonService"
  export default {
    name: "Topic",
    props: {
      video_src: String,
      video_id: String,
      lesson_id: Number,
      time: String,
    },
    watch: {
      time(val) {
        this.topic_data.time = val
      }
    },
    data() {
      return {
        error: {},
        topic_data : {
          name: "",
          description: "",
          time: "",
          type: 1
        }
      }
    },
    mounted() {
      this.topic_data.time = this.time
    },
    methods: {
      submitTopic() {
        LessonService.add_or_edit_topic(this.lesson_id, this.topic_data.id, this.topic_data).then(response => {
            console.log(response.data)
            this.$store.commit('toggleLoader', false);
            this.$toast.success("Topic saved successfully ", {'position': 'top'});
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
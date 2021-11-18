<template>
  <div>
    <h3>Add/Edit Question</h3>
    <form @submit.prevent="submitQuestion">
      <p>
        <label for="id_summary">Name:</label> <input type="text" v-model="que_data.summary" maxlength="255" class="form-control" placeholder="Name" required="" id="id_summary">
        <strong class="text-danger" v-show="error.summary">{{error.summary}}</strong>
      </p>
      <p>
        <label for="id_description">Description:</label> <editor api-key="no-api-key" v-model="que_data.description" id="id_description" />
        <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
      </p>
      <p v-show="!isLesson">
        <label for="id_active">Active:</label>
        <input type="checkbox" v-model="que_data.active" id="id_active">
        <strong class="text-danger" v-show="error.active">{{error.active}}</strong>
      </p>
      <p v-show="!isLesson">
        <label for="id_points">Points:</label> <input type="number" v-model="que_data.points" class="form-control" :required="!isLesson" id="id_points">
        <strong class="text-danger" v-show="error.points">{{error.points}}</strong>
      </p>
      <p>
        <label for="id_language">Language:</label>
        <select class="custom-select" required="" v-model="que_data.language" id="id_language">
          <option value="" selected="">Select Language</option>
          <option value="python">Python</option>
          <option value="bash">Bash</option>
          <option value="c">C</option>
          <option value="cpp">C++</option>
          <option value="java">Java</option>
          <option value="scilab">Scilab</option>
          <option value="r">R</option>
          <option value="other">Other</option>
        </select>
        <strong class="text-danger" v-show="error.language">{{error.language}}</strong>
      </p>
      <p>
        <label for="id_topic">Topic:</label> <input type="text" v-model="que_data.topic" class="form-control" id="id_topic">
        <strong class="text-danger" v-show="error.topic">{{error.topic}}</strong>
      </p>
      <p>
        <label for="id_type">Type:</label>
        <select class="custom-select" v-model="que_data.type" id="id_type" :disabled="isPoll">
          <option value="" selected="">Select Type</option>
          <option value="mcq">Single Correct Choice</option>
          <option value="mcc">Multiple Correct Choice</option>
          <option value="code" v-show="!isLesson">Code</option>
          <option value="upload" v-show="!isLesson">Upload</option>
          <option value="integer">Integer</option>
          <option value="float">Float</option>
          <option value="string">String</option>
          <option value="arrange" v-show="!isLesson">Arrange the options</option>
        </select>
        <strong class="text-danger" v-show="error.type">{{error.type}}</strong>
      </p>
      <p>
        <label for="id_snippet">Snippet:</label>
        <textarea v-model="que_data.snippet" cols="40" rows="10" class="form-control" placeholder="Snippet" id="id_snippet">
        </textarea>
        <strong class="text-danger" v-show="error.snippet">{{error.snippet}}</strong>
      </p>
      <p v-show="!isLesson">
        <label for="id_partial_grading">Partial Grading:</label>
        <input type="checkbox" v-model="que_data.partial_grading" id="id_partial_grading">
        <strong class="text-danger" v-show="error.partial_grading">{{error.partial_grading}}</strong>
      </p>
      <p v-show="!isLesson">
        <label for="id_grade_assignment">Grading Assignment Upload:
        </label>
        <input type="checkbox" v-model="que_data.grade_assignment_upload" id="id_grade_assignment">
        <strong class="text-danger" v-show="error.grade_assignment_upload">{{error.grade_assignment_upload}}
        </strong>
      </p>
      <p>
        <label for="id_min_time">Minimum Time:</label>
        <input type="number" v-model="que_data.min_time" class="form-control" id="id_min_time">
        <strong class="text-danger" v-show="error.min_time">{{error.min_time}}
        </strong>
      </p>
      <p>
        <label for="id_solution">Solution:</label>
        <textarea v-model="que_data.solution" cols="40" rows="10" class="form-control" placeholder="Solution" id="id_solution">
        </textarea>
        <strong class="text-danger" v-show="error.solution">{{error.solution}}
        </strong>
      </p>
      <p>
        <label for="id_timer">Timer:</label>
        <input type="text" v-model="que_data.time" class="form-control" placeholder="Time" required="" id="id_timer">
        <strong class="text-danger" v-show="error.time">{{error.time}}
        </strong>
      </p>
      <p>
        <mcqtype v-if="isMCC" v-bind:que_tc="que_data.test_cases" />
      </p>
      <p>
        <stringtype v-if="isString" v-bind:que_tc="que_data.test_cases" />
      </p>
      <p>
        <integertype v-if="isInteger" v-bind:que_tc="que_data.test_cases" />
      </p>
      <p>
        <floattype v-if="isFloat" v-bind:que_tc="que_data.test_cases" />
      </p>
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
  import McqType from "../question/McqType.vue"
  import StringType from "../question/StringType.vue"
  import IntegerType from "../question/IntegerType.vue"
  import FloatType from "../question/FloatType.vue"
  export default {
    name: "Question",
    components: {
      'editor': Editor,
      'mcqtype': McqType,
      'stringtype': StringType,
      'integertype': IntegerType,
      'floattype': FloatType
    },
    props: {
      time: String,
      lesson_id: Number,
      question: Object,
      content_type: String
    },
    computed: {
      isLesson() {
        return this.lesson_id != undefined
      },
      isMCC() {
        return this.que_data.type == "mcq" || this.que_data.type == "mcc"
      },
      isString() {
        return this.que_data.type == "string"
      },
      isInteger() {
        return this.que_data.type == "integer"
      },
      isFloat() {
        return this.que_data.type == "float"
      }
    },
    data() {
      return {
        error: {},
        que_data: {},
        que_tc: [],
        isPoll: false
      }
    },
    emits: ["updateToc"],
    watch: {
      time(val) {
        this.que_data.time = val
      },
      question(val) {
       this.que_data = val 
      },
      content_type(val) {
        this.setUp(val)
      }
    },
    mounted() {
      this.setUp(this.question.ctype)
    },
    methods: {
      submitQuestion() {
        this.$store.commit('toggleLoader', true);
        LessonService.add_or_edit_toc(this.lesson_id, this.que_data.toc_id, this.que_data).then(response => {
            this.$toast.success("Question saved successfully ", {'position': 'top'});
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
      },
      setUp(val) {
        this.que_data = this.question
        if(val === "4") {
          this.que_data.type = "mcq"
          this.isPoll = true
        } else {
          this.isPoll = false
        }
      }
    }
  }
</script>
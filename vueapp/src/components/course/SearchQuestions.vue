<template>
  <div>
    <div class="row" id="selectors">
      <div class="col-md-8">
        <h5>Please select Question type and Marks</h5>
      </div>
      <div class="col-md-6">
        <select class="custom-select" v-model="questionType">
          <option value="" selected>Select Question type</option>
          this.questionFilterData
          <option v-bind:key="value[0]" v-bind:value="value[0]" v-for="value in question_types">
            {{value[1]}}
          </option>
        </select>
      </div>
      <div class="col-md-4">
        <select class="custom-select" v-model="marks">
          <option value="" selected>Select Marks</option>
          <option v-bind:key="value" v-bind:value="value" v-for="value in getMarks()">
            {{value}}
          </option>
        </select>
      </div>
      <div class="col-md-2">
        <button class="btn btn-primary" id="_filterbtn" @click="filterQuestions()">
          <i class="fa fa-filter"></i>&nbsp;Filter
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import QuestionService from "../../services/QuestionService"

export default {
  name: "SearchQuestions",
  data() {
    return {
      questionType: "",
      marks: "",
      questionFilterData: {},
      question_types: ""
    }
  },
  mounted() {
    QuestionService.getQuestionTypeandMarks().then(response => {
      this.questionFilterData = response.data;
      this.question_types = this.getQuestionTypes()
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
  methods: {
    getQuestionTypes() {
      return Object.entries(this.questionFilterData.question_types);
    },
    getMarks() {
      return this.questionFilterData.marks;
    },
    filterQuestions() {
      if(this.questionType == "" || this.marks == "") {
        this.$toast.error("Please select the question type or marks", {'position': 'top'});
      } else {
          this.$store.commit('toggleLoader', true);
          var data = {
            "type": this.questionType, "points": this.marks,
          };
          QuestionService.filterQuestions(data).then((response) => {
            console.log(response)
            const availableQuestions = response.data;
            this.$store.commit('UPDATE_AVAILABLE_QUESTIONS', availableQuestions);
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
        }
    }
  }
}
</script>
<style scoped>
#_filterbtn {
  margin-bottom: 1em;
  padding: 10% 10% 10% 10%;
}
</style>
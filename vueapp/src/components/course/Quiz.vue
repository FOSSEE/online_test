<template>
  <div>
     <div class="modal" tabindex="-1" role="dialog" id="quizModal">
       <div class="modal-dialog mw-100 w-78" role="document">
         <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Add/Edit Quiz</h5>
            </div>
            <div class="modal-body">
              <div class="card">
                <div class="card-header"><b>Quiz Details</b></div>
                <div class="card-body">
                  <form @submit.prevent="submitQuiz">
                    <table class="table table-responsive">
                      <tr>
                        <th>Description:</th>
                        <td>
                        <input type="text" class="form-control"  v-model="quiz.description" required="" />
                        <br>
                        <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
                        </td>
                      </tr>
                      <tr>
                        <th>Instructions:</th>
                        <td>
                        <editor api-key="no-api-key" v-model="quiz.instructions" />
                        <br>
                        <strong class="text-danger" v-show="error.instructions">{{error.instructions}}</strong>
                        </td>
                      </tr>
                      <tr>
                      <th>Active:</th>
                      <td>
                        <input type="checkbox" v-model="quiz.active" v-bind:id="quiz.id">
                        <br>
                        <strong class="text-danger" v-show="error.active">{{error.active}}</strong>
                      </td>
                      </tr>
                      <tr>
                        <th>Start Time:</th>
                        <td>
                          <v-date-picker v-model="quiz.start_date_time" mode="dateTime" :timezone="timezone" :date-formatter="'YYYY-MM-DD HH:mm:ss'" is24hr>
                            <template #default="{ inputValue, inputEvents }">
                              <input class="px-3 py-1 border rounded" :value="inputValue" v-on="inputEvents" />
                              <br>
                              <strong class="text-danger" v-show="error.start_date_time">{{error.start_date_time}}
                              </strong>
                            </template>
                          </v-date-picker>
                        </td>
                      </tr>
                      <tr>
                        <th>End Time:</th>
                        <td>
                          <v-date-picker v-model="quiz.end_date_time" mode="dateTime" :timezone="timezone" :date-formatter="'YYYY-MM-DD HH:mm:ss'" is24hr>
                            <template #default="{ inputValue, inputEvents }">
                              <input class="px-3 py-1 border rounded" :value="inputValue" v-on="inputEvents" />
                              <br>
                              <strong class="text-danger" v-show="error.end_date_time">{{error.end_date_time}}
                              </strong>
                            </template>
                          </v-date-picker>
                        </td>
                      </tr>
                      <tr>
                        <th>Duration in minutes:</th>
                        <td>
                          <input type="number" v-model="quiz.duration" class="form-control"/>
                        </td>
                        <br>
                        <strong class="text-danger" v-show="error.duration">{{error.duration}}</strong>
                      </tr>
                      <tr>
                        <th>Passing Percentage:</th>
                        <td>
                          <input type="number" v-model="quiz.pass_criteria" class="form-control"/>
                        </td>
                        <br>
                        <strong class="text-danger" v-show="error.pass_criteria">{{error.pass_criteria}}</strong>
                      </tr>
                      <tr>
                        <th>Attempts Allowed:</th>
                        <td>
                        <select class="custom-select" v-model="quiz.attempts_allowed">
                          <option value="">Select number of Attempts</option>
                          <option value="1">1</option>
                          <option value="2">2</option>
                          <option value="3">3</option>
                          <option value="4">4</option>
                          <option value="5">5</option>
                          <option value="-1">Infinite</option>
                        </select>
                        </td>
                        <br>
                        <strong class="text-danger" v-show="error.attempts_allowed">{{error.attempts_allowed}}</strong>
                      </tr>
                      <tr>
                        <th>Time between quiz attempts in hours:</th>
                        <td>
                          <input type="number" v-model="quiz.time_between_attempts" class="form-control"/>
                        </td>
                        <br>
                        <strong class="text-danger" v-show="error.time_between_attempts">{{error.time_between_attempts}}</strong>
                      </tr>
                      <tr>
                        <th>Allow students to view answerpaper:</th>
                        <td>
                        <input type="checkbox" v-model="quiz.view_answerpaper" v-bind:id="quiz.id">
                        <br>
                        <strong class="text-danger" v-show="error.view_answerpaper">{{error.view_answerpaper}}</strong>
                        </td>
                      </tr>
                      <tr>
                        <th>Allow students to skip questions:</th>
                        <td>
                        <input type="checkbox" v-model="quiz.allow_skip" v-bind:id="quiz.id">
                        <br>
                        <strong class="text-danger" v-show="error.allow_skip">{{error.allow_skip}}</strong>
                        </td>
                      </tr>
                      <tr>
                        <th>Weightage in Percentage:</th>
                        <td>
                          <input type="number" v-model="quiz.weightage" class="form-control"/>
                        </td>
                        <br>
                        <strong class="text-danger" v-show="error.weightage">{{error.weightage}}</strong>
                      </tr>
                    </table>
                    <div>
                      <button type="submit" class="btn btn-success">Save
                      </button>
                      <button type="button" class="btn btn-secondary" data-dismiss="modal" @click="closeModal">Close
                      </button>
                    </div>
                  </form>
                </div>
              </div>
              <!-- Question paper -->
              <div class="card">
                <div class="card-header"><b>Question Paper Details</b></div>
                <div class="card-body">
                  <div>
                    <QuestionPaper :quizId="quiz.id" :moduleId="quiz.module_id"></QuestionPaper>
                  </div>
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
import QuizService from "../../services/QuizService"
import QuestionPaper from "./QuestionPaper"

export default {
  name: "Quiz",
  components: {
    'editor': Editor,
    QuestionPaper
  },
  computed: {
    ...mapState({
      user: (state) => state.user_id,
      course_id: (state) => state.course_id,
      quiz: (state) => state.unit
    }),
    existing() {
      return 'id' in this.quiz
    }
  },
  data() {
    return {
      error: {},
      module_id: '',
      timezone: 'Asia/Kolkata',
    }
  },
  mounted() {
    $("#quizModal").show();
    this.module_id = this.quiz['module_id']
  },
  methods: {
    closeModal() {
      this.$store.dispatch('toggleUnit', false)
    },
    submitQuiz() {
        this.$store.commit('toggleLoader', true);
        QuizService.create_or_update(this.module_id, this.quiz.id, this.quiz).then(response => {
            this.$emit("updateUnits", {"data": response.data, "existing": this.existing})
            this.$toast.success("Quiz saved successfully ", {'position': 'top'});
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
  }
}
</script>
<style scoped>
  .modal {
    width:  100%;
    overflow-y: scroll;
  }
</style>
<template>
  <div>
    <div class="row">
      <div class="col-md-6">
        <div id="fixed-available-wrapper">
          <p><u>Select questions to add:</u></p>
          <div id="fixed-questions">
            <div v-if="availableQuestions">
                <h5><input type="checkbox" id="add_checkall" name="add_checkall">&nbsp; Select All</h5>
                <div v-for="question in availableQuestions" :key="question.id">
                    <label>
                      <input
                        type="checkbox"
                        name="questions"
                        data-qid="question.id"
                        :value="question.id"
                        @change="updateCheckedQuestions" />
                      &nbsp;
                      <span v-if="userId == question.user.id">
                          <!-- TODO: A router link to edit question page. -->
                          {{question.summary}}
                      </span>
                      <span v-else>
                        {{question.summary}}
                      </span>
                      <span>
                        &nbsp; <strong>{{question.points}}</strong>
                      </span>
                    </label> 
                </div>
            </div>
          </div>
        </div>
        <br>
      <button id="add-fixed" name="add-fixed" class="btn btn-success" type="submit">
        <i class="fa fa-plus-square"></i>&nbsp; Add to paper
      </button>
      </div>
      <div class="col-md-6">
        <div id="fixed-added-wrapper">
          <p><u>Fixed questions currently in paper:</u></p>
          <div id="fixed-added">
              <h5><input type="checkbox" id="remove_checkall">&nbsp; Select All</h5>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { mapGetters } from 'vuex';
export default {
  name: "FixedQuestions",
  data () {
    return{
      fixedQuestions: [],
    }
  },
  mounted () {
    var user_id = document.getElementById("user_id").getAttribute("value");
    this.$store.commit('setUserId', user_id);
  },
  computed: {
    ...mapGetters([
      'availableQuestions',
      'userId'
    ]),
  },
  methods: {
    updateCheckedQuestions(e) {
      console.log(e.target);
      const choices = e.target;
      if(choices.checked) {
        // update checked questions
        this.fixedQuestions.push(choices.value);
      } else {
        // remove checked questions
        this.fixedQuestions.splice(this.fixedQuestions.indexOf(choices.value), 1);
      }
    }
  }
}
</script>
<style scoped>
#fixed-available-wrapper, #fixed-added-wrapper {
  background-color: #ccc6c6;
  height: auto;
  padding: 10px;
  border-radius: 20px;
}
</style>
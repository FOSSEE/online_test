<template>
    <div>
        <div class="tab-base">
            <nav class="nav nav-pills nav-fill">
                <a data-toggle="tab" role="tab" class="nav-item nav-link active" @click="toggleNav('fixed')">
                    STEP 1<br>
                    Add Fixed Questions
                </a>
                <a data-toggle="tab" role="tab" class="nav-item nav-link" @click="toggleNav('random')">
                    STEP 2<br>
                    Add Random Questions
                </a>
                <a data-toggle="tab" role="tab" class="nav-item nav-link" @click="toggleNav('finish')">
                    STEP 3<br>
                    Finish
                </a>
            </nav>
        </div>
        <br>
        <div v-show="activeTab!='finish'">
            <SearchQuestions v-on:availableQuestions="availableQuestions">
            </SearchQuestions>
        </div>
        <div id="fixed-questions" v-show="activeTab=='fixed'">
            <FixedQuestions :key="refreshComponent" :filtered="filteredQuestions" :questionPaper="questionPaperData"></FixedQuestions>
        </div>
        <div id="random-questions" v-show="activeTab=='random'">
            <RandomQuestions :key="refreshComponent" :filtered="filteredQuestions" :questionPaper="questionPaperData"></RandomQuestions>
        </div>
        <div id="finish" v-show="activeTab=='finish'">
            Finished
        </div>
    </div>
</template>

<script>
import FixedQuestions from "./FixedQuestions"
import RandomQuestions from "./RandomQuestions"
import SearchQuestions from "./SearchQuestions"
import QuestionPaperService from "../../services/QuestionPaperService"


export default {
    name: "QuestionPaper",
    props: {
        quizId: Number,
        moduleId: Number
    },
    components: {
        FixedQuestions, RandomQuestions, SearchQuestions
    },
    data() {
        return {
            activeTab: 'fixed',
            isready: false,
            isFixed: false,
            isRandom: false,
            filteredQuestions: [],
            questionPaperData: {},
            refreshComponent: 0,
        }
    },
    mounted() {
        this.$store.commit('toggleLoader', true);
        QuestionPaperService.getAllQuestionPaper(this.moduleId, this.quizId).then(response => {
            this.questionPaperData = response.data[0];
            console.log(this.questionPaperData);
            this.refreshComponent += 1
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
        showError(err) {
            if ("detail" in err) {
            this.$toast.error(err.detail, {'position': 'top'});
            } else {
            this.error = err
            }
        },
        toggleNav(current_nav) {
            this.activeTab = current_nav;
        },
        availableQuestions(data) {
            console.log(data)
            this.filteredQuestions = data;
            this.refreshComponent += 1
            this.isFixed = this.activeTab == "fixed"
            this.isRandom = this.activeTab == "random"
        }
    }
}
</script>

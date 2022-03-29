<template>
  <div>
    Random Questions
    {{questionPaper}}
  </div>
</template>
<script>
  export default {
    name: "RandomQuestions",
    props: {
      filtered: Array,
      questionPaper: Object
    }
  }
</script>
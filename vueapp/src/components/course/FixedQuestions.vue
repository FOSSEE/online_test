<template>
    <div>
        Fixed Questions
        {{questionPaper}}
    </div>
</template>
<script>
    export default {
        name: "FixedQuestions",
        props: {
            filtered: Array,
            questionPaper: Object
        }
    }
</script>
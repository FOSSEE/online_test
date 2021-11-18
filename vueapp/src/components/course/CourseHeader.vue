<template>
    <div>
        <div class="col-md-3">
            <router-link :to="{name: 'courses'}" class="btn btn-outline-primary btn-sm">
            <i class="fa fa-arrow-left"></i>&nbsp;Back
            </router-link>
        </div>
        <div class="course">
            <h1>{{course_name}}</h1>
        </div>
        <br>
    </div>
</template>
<script>

export default {
    name: "CourseHeader",
    props: {
        course_name: String
    },
}
</script>
<style scoped>
.course {
display: flex;
justify-content: center;
}
</style>

<template>
  <div class="col-md-3">
    <router-link :to="{name: 'courses'}" class="btn btn-primary">
      <i class="fa fa-arrow-left"></i>&nbsp;Back
    </router-link>
  </div>
  <div class="container-fluid">
    <div class="course">
      <h1>{{course_name}}</h1>
    </div>
    <br>
    <div class="container">
      <div class="col-md-12">
        <button class="btn btn-outline-primary" type="button" @click="showModule(null, false)">
          <i class="fa fa-plus-circle"></i>&nbsp;Add Module
        </button>
      </div>
    </div>
    <br>
    <div class="container">
      <div class="alert alert-info course" v-show="!has_modules">
        No Modules found
      </div>
      <div class="card" v-for="module in modules" :key="module.id">
        <div class="card-header bg-secondary">
          <a href="#">{{module.name}}</a>
        </div>
        <div class="card-body">
          
        </div>
      </div>
      {{modules}}
    </div>
  </div>
  <div class="modal" tabindex="-1" role="dialog" id="moduleModal">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add/Edit Course</h5>
        </div>
        <form @submit.prevent="submitModule">
        <div class="modal-body">
          <table class="table table-responsive-sm">
            <tr>
              <th>Name:</th>
              <td>
              <input type="text" class="form-control" name="name" v-model="edit_module.name" required="">
              <br>
              <strong class="text-danger" v-show="error.name">{{error.name}}</strong>
              </td>
            </tr>
            <tr>
              <th>Description:</th>
              <td>
                <textarea class="form-control" v-model="edit_module.description">
                </textarea>
              <br>
              <strong class="text-danger" v-show="error.description">{{error.description}}</strong>
              </td>
            </tr>
            <tr>
              <th>Active:</th>
              <td>
                <input type="checkbox" v-model="edit_module.active" v-bind:id="edit_module.id" name="active">
                <br>
                <strong class="text-danger" v-show="error.active">{{error.active}}</strong>
              </td>
            </tr>
          </table>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-success">Save
          </button>
          <button type="button" class="btn btn-secondary" data-dismiss="modal" @click="closeModal">Close</button>
        </div>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
  import ModuleService from "../../services/ModuleService"
  export default {
    name: "CourseDetail",
    data() {
      return {
        course_name: '',
        modules: [],
        edit_module: {},
        error: {}
      }
    },
    computed: {
      has_modules() {
        return this.modules.length > 0
      },
    },
    mounted() {
      var course_id = this.$route.params.course_id
      this.course_name = localStorage.getItem("course_"+course_id)
      this.$store.commit('toggleLoader', true);
      ModuleService.getall(course_id).then(response => {
          this.$store.commit('toggleLoader', false);
          var data = response.data;
          this.modules = data;
        })
        .catch(e => {
          this.$store.commit('toggleLoader', false);
          this.$toast.error(e.message, {'position': 'top'});
        });
    },
    methods: {

    }
  }
</script>
<style scoped>
  .course {
    display: flex;
    justify-content: center;
  }
</style>
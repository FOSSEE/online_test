<template>
  <div class="modal" tabindex="-1" role="dialog" id="moduleModal">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Add/Edit Module</h5>
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
                <editor api-key="no-api-key" v-model="edit_module.description" />
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
  import $ from 'jquery';
  import { mapState } from 'vuex';
  import ModuleService from "../../services/ModuleService"
  import Editor from '@tinymce/tinymce-vue'
  export default {
    name: 'Module',
    components: {
      'editor': Editor
    },
    data() {
      return {
        error: {},
      }
    },
    computed: {
      ...mapState({
          user: (state) => state.user_id,
          course_id: (state) => state.course_id,
          edit_module: (state) => state.module
      }),
      existing() {
        return 'id' in this.edit_module
      },
    },
    mounted() {
      $("#moduleModal").show();
    },
    methods: {
      closeModal() {
        this.$store.dispatch('toggleModule', false)
      },
      submitModule() {
        this.$store.commit('toggleLoader', true);
        ModuleService.create_or_update(this.course_id, this.edit_module.id, this.edit_module).then(response => {
            this.$store.commit('toggleLoader', false);
            this.$emit("updateModules", {"data": response.data, "existing": this.existing})
            this.$store.dispatch('toggleModule', false)
            this.$toast.success("Module saved successfully ", {'position': 'top'});
          })
          .catch(e => {
            this.$store.commit('toggleLoader', false);
            console.log(e)
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
      },
    }
  }
</script>

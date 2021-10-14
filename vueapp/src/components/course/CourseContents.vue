<template>
<div>
  <CourseHeader v-if=is_ready v-bind:course_name=course_name />
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-3">
        <CourseOptions v-if=is_ready v-bind:course_id=course_id />
      </div>
      <div class="col-md-7">
        <Module v-if="isModule" v-on:updateModules="updateModules"></Module>
        <Lesson v-if="isLesson" v-on:updateUnits="updateUnits"></Lesson>
        <Quiz v-if="isQuiz" v-on:updateUnits="updateUnits"></Quiz>
          <button class="btn btn-outline-primary" type="button" @click="showModule(null, false)">
            <i class="fa fa-plus-circle"></i>&nbsp;Add Module
          </button>
          <br><br>
          <div class="alert alert-info course" v-show="!has_modules">
            No Modules found
          </div>
          <div class="card" v-for="(module, index) in modules" :key="module.id">
            <div class="card-header bg-secondary">
              {{index+1}}.
              <a href="#" @click="showModule(index, true)"> {{module.name}}
              </a>
            </div>
            <div class="card-body">
              <div>
                <button class="btn btn-primary btn-sm" type="button" @click="showUnit(module, 0, false, 'Lesson')">
                  <i class="fa fa-plus-circle"></i>&nbsp;Add Lesson
                </button>
                <button class="btn btn-primary btn-sm" type="button" @click="showUnit(module, 0, false, 'Quiz')">
                  <i class="fa fa-plus-circle"></i>&nbsp;Add Quiz/Exercise
                </button>
              </div>
              <br>
              <table class="table table-responsive" v-show="module.has_units">
                <thead>
                  <tr>
                    <th></th>
                    <th>Sr No.</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Order</th>
                    <th>Statistics</th>
                  </tr>
                </thead>
                <draggable tag="tbody" v-model="module.units" @change="updateOrder(module.units, $event)">
                  <tr
                    v-for="(unit, idx) in module.units"
                    :key="unit.id"
                  >
                    <td>
                    <i class="fa fa-align-justify handle"></i>
                    </td>
                    <td>{{idx+1}}</td>
                    <td v-if="unit.type == 'Lesson'">
                      <a href="#" @click="showUnit(module, idx, true)">{{unit.name}}
                      </a>
                    </td>
                    <td v-else>
                      <a href="#" @click="showUnit(module, idx, true)">{{unit.description}}
                      </a>
                    </td>
                    <td>
                      {{unit.type}}
                    </td>
                    <td>
                      <input type="text" class="form-control form-control-sm" v-model="unit.order" />
                    </td>
                    <td>
                      Statistics
                    </td>
                  </tr>
                </draggable>
              </table>
              <br>
              <button class="btn btn-outline-success btn-sm" @click="submitUnits(module.id, module.units)" v-show="module.has_units">
                Save Units
              </button>
              <br>
              <div class="course" v-show="!module.has_units">
                <span class="badge badge-warning">
                  No Lesson/quiz/exercies are added
                </span>
              </div>
            </div>
          </div>
      </div>
    </div>
  </div>
</div>
</template>
<script>
  import { mapState } from 'vuex';
  import { VueDraggableNext } from 'vue-draggable-next'
  import ModuleService from "../../services/ModuleService"
  import CourseHeader from '../course/CourseHeader.vue';
  import Module from './Module.vue'
  import Lesson from './Lesson.vue'
  import Quiz from './Quiz.vue'
  import CourseOptions from './CourseOptions.vue'

  export default {
    name: "CourseContents",
    components: {
      Module, Lesson, Quiz,
      "draggable": VueDraggableNext,
      CourseOptions, CourseHeader
    },
    data() {
      return {
        course_name: '',
        modules: [],
        edit_module: {},
        edit_unit: {},
        error: {},
        course_id: '',
        last_module_order: '',
        is_ready: false
      }
    },
    computed: {
      ...mapState({
          user: (state) => state.user_id,
          isModule: (state) => state.showModule,
          isLesson: (state) => state.showLesson,
          isQuiz: (state) => state.showQuiz,
      }),
      has_modules() {
        return this.modules.length > 0
      },
    },
    mounted() {
      try {
        var user_id = document.getElementById("user_id").getAttribute("value");
        this.$store.dispatch('setUserId', user_id);
      } catch {console.log("User error")}
      this.course_id = this.$route.params.course_id
      this.is_ready = true
      this.course_name = localStorage.getItem("course_"+this.course_id)
      this.$store.commit('toggleLoader', true);
      ModuleService.getall(this.course_id).then(response => {
          var data = response.data;
          this.modules = data;
        })
        .catch(e => {
          this.$toast.error(e.message, {'position': 'top'});
        })
        .finally(() => {
          this.$store.commit('toggleLoader', false);
        });
    },
    methods: {
      showModule(index, is_edit) {
        if(is_edit) {
          this.edit_module = this.modules[index]
          this.module_index = index
        } else {
          try {
            this.last_module_order = this.modules[this.modules.length-1].order+1
          } catch {
            this.last_module_order = 0
          }
          this.edit_module = {'owner': this.user, "course": this.course_id, 'order': this.last_module_order}
        }
        this.$store.dispatch('setModule', this.edit_module)
        this.$store.dispatch('toggleModule', true)
        this.$store.dispatch('setCourseId', this.course_id)
      },
      showUnit(c_module, unit_index, is_edit, type) {
        this.edit_module = c_module
        if(is_edit) {
          this.edit_unit = c_module['units'][unit_index]
          this.unit_index = unit_index
        } else {
          try {
            var units = c_module["units"]
            this.last_unit_order = units[units.length-1].order+1
          } catch {
            this.last_unit_order = 1
          }
          this.edit_unit = {'owner': this.user, 'order': this.last_unit_order, 'type': type}
        }
        this.edit_unit['module_id'] = this.edit_module.id
        var isLesson = this.edit_unit["type"] == "Lesson"
        var isQuiz = this.edit_unit["type"] == "Quiz"
        this.$store.dispatch('setUnit', this.edit_unit)
        this.$store.dispatch('toggleUnit', {"isLesson": isLesson, "isQuiz": isQuiz})
        this.$store.dispatch('setCourseId', this.course_id)
      },
      updateModules(args) {
        if (args.existing) {
          this.modules[this.module_index] = args.data
        } else {
          this.modules.push(args.data)
        }
      },
      updateUnits(args) {
        if (args.existing) {
          this.edit_module['units'][this.unit_index] = args.data
        } else {
          this.edit_module["units"].push(args.data)
        }
        this.edit_module['has_units'] = true
      },
      updateOrder(units) {
        for(let i = 0; i < units.length; i++) {
          units[i].order = i
        }
      },
      submitUnits(module_id, units) {
        this.$store.commit('toggleLoader', true);
        let data = {"units": units}
        ModuleService.changeUnits(module_id, data).then(response => {
            let msg = response.data.message;
            let status = response.data.success
            if(status) {
              this.$toast.success(msg, {'position': 'top'});
            } else {
              this.$toast.error(msg, {'position': 'top'});
            }
          })
          .catch(e => {
            console.log(e)
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
</script>

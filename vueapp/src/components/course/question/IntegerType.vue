<template>
  <div>
    <button type="button" class="btn btn-primary btn-sm" @click="addTc">
      <i class="fa fa-plus-circle"></i>&nbsp;Add Options
    </button>
    <br><br>
    <table class="table table-responsive">
      <tr v-for="tc in test_cases" :key="tc.id">
        <td>
          <label>Correct:</label> <input type="number" required class="form-control" v-model="tc.correct_ans" />
        </td>
        <td>
          <label>Delete:</label> <input type="checkbox" v-model="tc.delete" name="active">
        </td>
      </tr>
    </table>
  </div>
</template>
<script>
  export default {
    name: "IntegerType",
    props: {
      que_tc: Array
    },
    data() {
      return {
        test_cases: [],
        tc_data: {
          type: "integertestcase",
          correct_ans: "",
          delete: false
        }
      }
    },
    mounted() {
      this.test_cases = this.que_tc
    },
    methods: {
      addTc() {
        this.test_cases.push(JSON.parse(JSON.stringify(this.tc_data)))
      }
    }
  }
</script>
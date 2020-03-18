const Error = Vue.component('Error', {
  template: `
    <div>
      <div v-if="result['message']">
        <div class="card">
          <div class="card-body">
            <strong>{{result["message"]}}</strong>
          </div>
        </div>
      </div>
      <div v-if="showSuccessMessage">
        <div class="card">
          <div class="card-body">
          {{showSuccessMessage}}
          </div>
        </div>
      </div>

      <div v-if="result.error">
        <div v-for='(error, index) in result.error' :key="index">
          <div class="card">
            <div class="card-header alert-danger">Error No. {{index+1}}</div>
            <div class="card-body">
              <div v-if="!error.type">
                <pre><code v-html="error"></code></pre>
              </div>
              <div v-else-if="error.type==='assertion'">
                <div v-if="error.test_case">
                  <strong>We tried your code with the following test case: </strong>
                  <br /><br />
                  <pre><code><strong class="text-danger">{{error.test_case}}</strong></code></pre>
                </div>
                <p><b>The following error took place: </b></p>
                <table class="table table-borderless border border-danger table-responsive-sm" width="100%" id='assertion'>
                  <col width="30%">
                  <tr class = "bg-light">
                    <td><b>Exception Name: </b></td>
                    <td><span class="text-danger">{{error.exception}}</span></td>
                  </tr>
                  <tr>
                    <td><b>Exception Message: </b></td><td>{{error.message}}</td>
                  </tr>
                  <tr v-if="error.traceback">
                    <input type="hidden" id="err_lineno" value="error.line_no">
                    <td><b>Full Traceback: </b></td>
                    <td><pre>{{error.traceback}}</pre></td>
                  </tr>
                </table>
              </div>
              <div v-else-if="error.type==='stdio'">
                <table class="table table-borderless table-responsive-sm" v-if="error.given_input">
                  <col width="30%">
                  <tr class="bg-light">
                    <td> For given Input value(s):</td>
                    <td>{{error.given_input}}</td>
                  </tr>
                </table>
                <table class="table table-borderless table-responsive-sm" width="100%" id="stdio">
                  <col width="10%">
                  <col width="40%">
                  <col width="40%">
                  <col width="10%">
                  <tr class="info">
                    <th><center>Line No.</center></th>
                    <th><center>Expected Output</center></th>
                    <th><center>User output</center></th>
                    <th><center>Status</center></th>
                  </tr>
                  <tr v-for="(output, index) in result.error" :key="index">
                    <td align="center">{{index + 1}}</td>
                    <td align="center" v-if="output['expected_output']" v-for="expOp in output['expected_output']">
                      {{expOp}}
                    </td>
                    <td align="center" v-if="output['user_output']" v-for="usOp in output['user_output']">
                      {{usOp}}
                    </td>
                    <td align="center" v-if="0 in error.error_line_numbers || !output['expected_output'] || !output['user_output']">
                      <span class="fa fa-times text-warning"></span>
                    </td>
                    <td align="center" v-else>
                      <span class ="fa fa-check text-success"></span>
                    </td>
                  </tr>
                </table>
                <table width="100%" class="table table-borderless table-responsive-sm">
                  <col width="10">
                  <tr class = "bg-light">
                    <td><b>Error:</b></td>
                    <td>{{error.error_msg}}</td>
                  </tr>
                 </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  props: ['result'],
  computed: {
    showSuccessMessage () {
      if (this.result.success) {
        const message = 'Submitted successfully'
        return message
      }
    },
  },
})
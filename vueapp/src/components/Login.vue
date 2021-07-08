<template>
  <div class="container mt--8 pb-5">
   <div class="row justify-content-center">
    <div class="col-lg-5 col-md-7">
      <div class="card bg-secondary border-0 mb-0">
        <div class="card-header bg-transparent pb-5">
          <div class="text-muted text-center mt-2 mb-3">Sign in with</div>
          <div class="btn-wrapper text-center">
            <a :href="google_url" class="btn btn-neutral btn-icon">
              <span class="btn-inner--icon">
                <span class="fa fa-google" style="color: red;"></span>
              </span>
              <span class="btn-inner--text" style="color: red;">Google</span>
            </a>
            <a :href="facebook_url" class="btn btn-neutral btn-icon">
              <span class="btn-inner--icon">
                  <span class="fa fa-facebook-square"></span>
              </span>
              <span class="btn-inner--text">Facebook</span>
            </a>
          </div>
        </div>
        <div class="card-body px-lg-5 py-lg-5">
          <div class="text-center text-muted mb-4">
            Or Sign in with credentials
          </div>
          <form action="#" @submit.prevent="onSubmit">
            <div class="form-group mb-3">
              <div class="input-group input-group-merge input-group-alternative">
                <div class="input-group-prepend">
                  <span class="input-group-text"><i class="fa fa-user"></i></span>
                </div>
                <input type="text" placeholder="Username" v-model="username" class="form-control">
              </div>
                <p>{{username}}</p>
            </div>
            <div class="form-group">
              <div class="input-group input-group-merge input-group-alternative">
                <div class="input-group-prepend">
                  <span class="input-group-text"><i class="fa fa-lock"></i></span>
                </div>
                <input type="password" placeholder="Password" v-model="password" class="form-control">
              </div>
                <p>{{password}}</p>
            </div>
            <div class="text-center">
              <button type="submit" class="btn btn-primary my-4">Sign in</button>
            </div>
          </form>
          <div class="row mt-3">
            <div class="col-6">
              <a :href="forgot_pwd_url" class="text-muted">Forgot password?</a>
            </div>
            <div class="col-6 text-right">
              <a :href="register_url" class="text-muted">Create new account</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script>
  // eslint-disable-next-line no-unused-vars
  import LoginService from "../services/LoginService";

  export default {
    name: "Login",
    data() {
      return {
        username: '',
        password: '',
        register_url: '',
        google_url: '',
        facebook_url: '',
        forgot_pwd_url: '',
      };
    },
    methods: {
      onSubmit() {
        var result = LoginService.validate(this.username, this.password);
        if(!result) {
          this.$toast.error('Please enter Username/Password', {'position': 'top'});
        } else {
          var headers = {"Content-type": "application/json"}
          // var data = {"username": this.username, "password": this.password}
          this.$store.commit('toggleLoader', true);
          LoginService.getCourses(headers).then(response => {
            this.$store.commit('toggleLoader', false);
            console.log(response.data)
          })
          .catch(e => {
            this.$store.commit('toggleLoader', false);
            this.$toast.error(e.response.data.message, {'position': 'top'});
          });
        }
      }
    }
  };
</script>

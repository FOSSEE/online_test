<template>
  <div>
    <div class="container">
      <router-link class="btn btn-primary" :to="{name: 'course_forum', params: {course_id: course.id}}">
        Back to Posts
      </router-link>
      <br>
      <br>
      <div>
        <!-- Toast messages -->
      </div>
      <div class="card mb-2">
        <div class="card-header py-2 px-3">
          {{post.title}}
          <br>
          <small>
            <strong v-if="post.anonymous">
              Anonymous
            </strong>
            <strong v-else-if="post.creator">
              {{post.creator.username}}
            </strong>
            {{post.created_at}}
          </small>
        </div>
        <div class="card-body">
          <p class="card-text description">
            <span v-html="post.description"></span>
          </p>
          <span v-if="post.image" class="thumbnail">
            <!-- if has image, show image -->
            <img :src="post.image" alt="" class="post_image">
          </span>
        </div>
      </div>
      <br>
      <b><u>Comments:</u></b>
      <div v-if="comments">
        <div v-for="comment in comments" :key="comment.id">
          <div class="card mb-2">
            <div class="card-body p-3">
              <div class="row mb-3">
                <div class="col-6">
                  <strong class="text-muted" v-if="comment.anonymous">
                    Anonymous
                  </strong>
                  <strong class="text-muted" v-else-if="comment.creator">
                    {{comment.creator.username}}
                  </strong>
                </div>
                <div class="col-6 text-right">
                  <small class="text-muted">
                    {{comment.created_at}}
                    <span v-if="checkPermission(comment)">
                      <!-- show trash icon to moderator or course creator/teacher -->
                      <i class="fa fa-trash" @click.prevent="deleteComment(course.id, post.id, comment.id)"></i>
                    </span>
                  </small>
                </div>
              </div>
              <p class="card-text description">
                <span v-html="comment.description"></span>
                <span v-if="comment.image" class="thumbnail">
                  <!-- if image exists show image -->
                  <img :src="comment.image" alt="" class="comment_image">
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>
      <br>
      <div>
        <b><u>Add Comment:</u></b>
        <form @submit.prevent="submitComment(post.id)" enctype="multipart/form-data">
          <div class="mb-3">
            <label for="description" class="form-label">Description:</label>
            <br>
            <small><strong class="text-danger">{{ fieldErrors.description }}</strong></small>
            <editor
              api-key="no-api-key"
              v-model="description"
            />
          </div>
          <div class="mb-3">
            <label for="image" class="form-label">Image</label>
            <input @change="onFileChange($event)" type="file" class="form-control" id="formFile" ref="inputFile">
          </div>
          <div class="form-check">
            <input type="checkbox" id="checkbox" v-model="anonymous">
            <label for="checkbox" class="form-check-label">Anonymous</label>
          </div>
          <button type="submit" class="btn btn-success">Submit</button>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
/* eslint-disable */
import ForumService from '../../services/ForumService';
import CourseService from '../../services/CourseService';
import Editor from '@tinymce/tinymce-vue'

export default {
  name: "PostComments",
  data () {
    return {
      course_id: '',
      post: '',
      user_id: '',
      course: '',
      comments: undefined,
      description: '',
      anonymous: false,
      file: '',
      fieldErrors: {
        description: undefined,
      },
    };
  },
  mounted () {
    this.getCourse();
    this.getUser();
    this.fetchPostDetails();
  },
  components: {
    'editor': Editor
  },
  computed: {
    isDisabled () {
      if(this.description.length > 0) {
        return false;
      }
      return true;
    }
  },
  methods: {
    onFileChange(event) {
      this.file = event.target.files[0];
    },

    fetchPostDetails () {
      this.course_id = parseInt(this.$route.params.course_id)
      this.post_id = parseInt(this.$route.params.post_id)
      this.$store.commit('toggleLoader', true);
      ForumService.getPost(this.course_id, this.post_id)
        .then((response) => {
          console.log(response)
          if(response.status == 200) {
            this.post = response.data,
            this.comments = this.post.comments
          }
        })
        .catch((e) => {
          console.log(e);
        })
      this.$store.commit('toggleLoader', false);
    },

    getUser () {
      this.user_id = document.getElementById("user_id").getAttribute("value");
    },

    getCourse () {
      this.course_id = parseInt(this.$route.params.course_id)
      this.$store.commit('toggleLoader', true);
      CourseService.get(this.course_id)
        .then((response) => {
          this.course = response.data;
        });
      this.$store.commit('toggleLoader', false);
    },

    resetFields () {
      this.description = '';
      this.anonymous = false;
      this.file = '';
      this.$refs.inputFile.value = null;
    },

    submitComment (post_id) {
      const data = new FormData();
      data.append('creator', this.user_id);
      data.append('description', this.description);
      data.append('anonymous', this.anonymous);
      data.append('file', this.file);
      this.$store.commit('toggleLoader', true);
      ForumService.createComment(this.course_id, this.post_id, data)
        .then((response) => {
          this.comments.push(response.data)
        })
        .catch((e) => {
          console.log(e.response.data.description[0])
          this.fieldErrors.description = e.response.data.description[0];
        })
        this.resetFields();
        this.$store.commit('toggleLoader', false);
    },

    removeComment(comment_id) {
      this.comments.forEach((comment, index) => {
        if(comment.id == comment_id) {
          this.comments.splice(index, 1);
        }
      });
    },

    deleteComment (course_id, post_id, comment_id) {
      if(confirm('Do you really want to delete?')){
        this.$store.commit('toggleLoader', true);
        ForumService.deleteComment(course_id, post_id, comment_id)
          .then((response) => {
            console.log('Successfully delete the comment')
          })
          .catch((e) => {
            console.log(e)
          })
        this.removeComment(comment_id)
        this.$store.commit('toggleLoader', false);
      }
    },

    checkPermission (object) {
      if (object.creator) return this.user_id == object.creator.id
    }
  },
}
</script>

<style scoped>
.post_image, .comment_image {
  border-radius: 8px;
  width: 50%;
  height: 50%;
}
</style>
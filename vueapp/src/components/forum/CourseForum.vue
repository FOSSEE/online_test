<template>
  <div>
    <div id="wrapper" class="d-flex">
      <div class="container" id="page-content-wrapper">
        <div>
            <h2><center>{{course.name}}</center></h2>
            <center>Discussion Forum</center>
        </div>
        <div class="d-flex p-2 bd-highlight">
          <div class="col-md-4">
            <a href="" class="btn btn-primary">
              <i class="fa fa-arrow-left"></i>&nbsp;Back
            </a>
          </div>
          <div class="col-md">
            <button type="button" class="btn btn-success pull-right" data-toggle="modal" data-target="#newPostModal">
                <i class="fa fa-plus-circle"></i>&nbsp;New Post
            </button>
          </div>
        </div>
        <!-- Modal -->
        <div id="newPostModal" class="modal fade" role="dialog">
          <div class="modal-dialog">
            <!-- Modal Content -->
            <div class="modal-content">
              <div class="modal-header">
                <h4 class="modal-title">Create a New Post</h4>
                <button type="button" ref="Close" class="close" data-dismiss="modal">&times;</button>
              </div>
              <div class="modal-body">
                <form @submit.prevent="submitPost" enctype="multipart/form-data">
                  <div class="mb-3">
                    <label for="title" class="form-label">Title</label>
                    <input v-model="title" type="text" class="form-control"/>
                  </div>
                  <div class="mb-3">
                    <label for="description" class="form-label">Description</label>
                    <!-- Editor component -->
                    <editor
                      api-key="no-api-key"
                      v-model="description"
                      />
                  </div>
                  <div class="mb-3">
                    <label for="image" class="form-label">Image</label>
                    <input @change="onFileChange($event)" type="file" class="form-control" id="formFile">
                  </div>
                  <div class="form-check">
                    <input type="checkbox" id="checkbox" v-model="anonymous" class="form-check-input">
                    <label for="checkbox" class="form-check-label">Anonymous</label>
                  </div>
                  <button type="submit" class="btn btn-success">
                    Submit
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
        <br>
        <br>
        <div v-if="posts">
          <div class="row justify-content-center">
            <div class="col-md-6">
              <form @submit.prevent="searchPosts" class="my-2 my-lg-0">
                <div class="input-group">
                  <input
                    type="search"
                    placeholder="Search Post"
                    name="search_post"
                    class="form-control"
                    v-model="search">
                  <span class="input-group-append">
                    <button class="btn btn-outline-info">
                      <i class="fa fa-search"></i>&nbsp;Search
                    </button>
                  </span>
                </div>
              </form>
            </div>
            <div class="col-md-4">
              <span @click="clearSearch" class="btn btn-outline-danger">
                <i class="fa fa-times"></i>&nbsp;Clear Search
              </span>
            </div>
          </div>
          <br>
          <!-- paginator -->
          <br>
          <div class="card">
            <div class="table-responsive" :style="getStyle">
              <table id="posts_table" class="table table-responsive-sm">
                <thead class="thread-inverse thead-light">
                  <tr>
                    <th width="700">Posts</th>
                    <th>Created by</th>
                    <th>Replies</th>
                    <th>Last reply</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody class="list">
                  <tr v-for="post in posts" :key="post.id">
                    <td>
                      <router-link :to="{name: 'post_comments', params: {course_id: course.id, post_id: post.id}}">
                        {{post.title}}
                      </router-link>
                      <small
                        class="text-muted d-block">
                        {{truncate(post.description, 10, '...')}}
                      </small>
                      <small
                        class="text-muted">
                        <strong>
                          Last updated: {{post.modified_at}}
                        </strong>
                      </small>
                    </td>
                    <td>
                      <div v-if="post.anonymous">Anonymous</div>
                      <div v-else>{{post.creator.username}}</div>
                    </td>
                    <td>
                      <!-- post comments count -->
                      {{post.comments_count}}
                    </td>
                    <td>
                      <!-- last comment by -->
                      <div v-if="post.last_comment_by">
                        {{post.last_comment_by}}
                      </div>
                      <div v-else>
                        None
                      </div>
                    </td>
                    <td v-if="checkPermission(post)">
                      <!-- show delete button to only course creator or course teacher -->
                        <i @click.prevent="deletePost(course.id, post.id)" class="pull-right fa fa-trash"></i>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <button class="btn btn-primary" @click="fetchMorePosts" v-show="hasPosts">
            Load More
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
/* eslint-disable */

import CourseService from "../../services/CourseService";
import Editor from '@tinymce/tinymce-vue';
import ForumService from '../../services/ForumService';

export default {
  name: "CourseForum",
  data () {
    return {
      course_id:'',
      course: '',
      user_id: '',
      title: '',
      description: '',
      file: '',
      anonymous: false,
      posts: [],
      search: '',
      nextPage: '',
      postsCount: '',
    };
  },
  mounted () {
    this.getCourse();
    this.getUser();
    this.fetchPosts();
  },
  components: {
    'editor': Editor
  },
  computed: {
    getStyle() {
      if(this.posts.length > 10) return 'height: 700px';
    },

    hasPosts() {
      return this.posts.length > 0
    }
  },
  methods: {
    checkPermission(post) {
      return this.user_id == post.creator.id;
    },

    truncate (text, length, clamp) {
      clamp = clamp || '...'
      var node = document.createElement('div')
      node.innerHTML = text
      var content = node.textContent
      return content.length > length ? content.slice(0, length) + clamp : content
    },

    appendData (data) {
      data.forEach((post) => {
        this.posts.push(post)
      })
    },

    fetchMorePosts () {
      if (this.nextPage != null) {
        const page = this.nextPage.split("?")[1];
        this.$store.commit('toggleLoader', true);
        ForumService.nextPosts(page, this.course_id)
          .then((response) => {
            const data = response.data
            this.appendData(data.results);
            this.postsCount = this.posts.length
            this.nextPage = data.next
          })
          .catch((e) => {
            console.log(e)
          })
        this.$store.commit('toggleLoader', false)
      } else {
        this.$toast.info("No more Posts", {'position': 'top'})
      }
    },

    fetchPosts () {
      this.$store.commit('toggleLoader', true);
      ForumService.getPosts(this.course_id)
        .then(response => {
          if (response.status == 200) {
            const data = response.data['results'];
            this.posts = data
            this.nextPage = response.data.next
          }
        });
      this.$store.commit('toggleLoader', false);
    },

    getCourse() {
      this.course_id = parseInt(this.$route.params.course_id)
      this.$store.commit('toggleLoader', true);
      CourseService.get(this.course_id)
        .then(response => {
            this.course = response.data;
        });
      this.$store.commit('toggleLoader', false);
    },
    getUser() {
      this.user_id = document.getElementById("user_id").getAttribute("value");
    },

    submitPost() {
      const data = {
        'title': this.title,
        'description': this.description,
        // 'image': this.file,
        'anonymous': this.anonymous,
        'target_id': this.course_id,
      }
      this.$store.commit('toggleLoader', true);
      ForumService.create_or_update(this.course_id, null, data)
        .then((response) => {
          this.posts.unshift(response.data)
        })
        .catch((e) => {
          console.log(e);
        })
      this.$refs.Close.click();
      this.$store.commit('toggleLoader', false);
    },

    removePost(post_id) {
      this.posts.forEach((post, index) => {
        if(post.id == post_id) {
          this.posts.splice(index, 1)
        }
      });
    },

    deletePost(course_id, post_id) {
      if(confirm('Do you really want to delete this post?')) {
        this.$store.commit('toggleLoader', true);
        ForumService.deletePost(course_id, post_id)
          .then((response) => {
            console.log('Post deleted successfully')
          })
          .catch((e) => {
            console.log(e)
          })
        this.removePost(post_id)
        this.$store.commit('toggleLoader', false);
      }
    },

    searchPosts() {
      this.$store.commit('toggleLoader', true);
      ForumService.searchPosts(this.course_id, this.search)
        .then((response) => {
          console.log(response)
          this.posts = response.data['results']
        })
        .catch((e) => {
          console.log(e.response)
        })
      this.$store.commit('toggleLoader', false);
    },

    clearSearch () {
      this.search = ''
    },

    onFileChange(event) {
      const file = event.target.files[0];
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = (e) => {
        this.file = e.target.result;
      }
    },
  },
}
</script>

<style scoped>
</style>
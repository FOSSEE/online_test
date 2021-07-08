import { createStore } from 'vuex';
import $ from 'jquery';
const store = createStore({
    state() {
        return {
            showLoading: false,
            user_id: ''
        }
    },
    mutations: {
        toggleLoader(state, payload) {
            state.showLoading = payload;
            if(state.showLoading)
            {$("#loader1").show()}
            else
            {$("#loader1").hide()}
        },
        setUserId(state, payload) {
            state.user_id = payload;
        }
    },
});

export default store;

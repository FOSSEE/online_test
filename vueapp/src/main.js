import {createApp} from 'vue'
import App from './App.vue'
import store from './store/store'
import Toaster from '@meforma/vue-toaster'
import VCalendar from 'v-calendar';
import Error from './components/Error.vue'
import router from './router'

const page_mapper = {
	"course": App,
	"module": "",
	"lesson": ""
}
var app;
try {
	var role = document.getElementById("role").getAttribute("value");
	app = createApp(page_mapper[role])
} catch (e) {
	app = createApp(Error)
}
app.use(router)
app.use(VCalendar)
app.use(Toaster)
app.use(store)
app.mount('#app')

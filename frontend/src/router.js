import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import SessionView from './views/SessionView.vue'
import CallbackView from './views/CallbackView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/session/:code', name: 'session', component: SessionView, props: true },
  { path: '/callback', name: 'callback', component: CallbackView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})

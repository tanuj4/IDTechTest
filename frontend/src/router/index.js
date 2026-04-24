import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AssetsView from '../views/AssetsView.vue'
import AssetCreateView from '../views/AssetCreateView.vue'
import AssetDetailView from '../views/AssetDetailView.vue'
import ClientsView from '../views/ClientsView.vue'
import ClientDetailView from '../views/ClientDetailView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/assets', component: AssetsView },
  { path: '/assets/new', component: AssetCreateView },
  { path: '/assets/:id', component: AssetDetailView },
  { path: '/clients', component: ClientsView },
  { path: '/clients/:id', component: ClientDetailView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})

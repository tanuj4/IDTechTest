<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAssets, toggleAsset, deleteAsset } from '../api/index.js'
import AssetTable from '../components/AssetTable.vue'
import ToastNotification from '../components/ToastNotification.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { useToast } from '../composables/useToast.js'
import { useConfirm } from '../composables/useConfirm.js'

const route = useRoute()
const router = useRouter()

const assets = ref([])
const total = ref(0)
const currentPage = ref(parseInt(route.query.page) || 1)
const totalPages = ref(1)
const search = ref(route.query.search || '')
const filterType = ref(route.query.type || '')
const filterStatus = ref(route.query.status || '')
const loading = ref(false)
const exporting = ref(false)
const error = ref(null)

const { toast, showToast, closeToast } = useToast()
const { confirmModal, showConfirm, handleConfirm, cancelConfirm } = useConfirm()

const assetTypes = ['workstation', 'server', 'network', 'peripheral']
const statuses = ['active', 'inactive', 'retired']

const activeFilterCount = computed(() => {
  return [search.value, filterType.value, filterStatus.value].filter(Boolean).length
})

const clearFilters = () => {
  search.value = ''
  filterType.value = ''
  filterStatus.value = ''
}

const formatDate = (dateStr) => dateStr ? dateStr.split('T')[0] : 'N/A'

const exportUrl = computed(() => {
  const params = new URLSearchParams()
  if (search.value) params.set('search', search.value)
  if (filterType.value) params.set('type', filterType.value)
  if (filterStatus.value) params.set('status', filterStatus.value)
  const qs = params.toString()
  return `/api/assets/export${qs ? '?' + qs : ''}`
})

const fetchAssets = async () => {
  loading.value = true
  error.value = null

  const query = {}
  if (search.value) query.search = search.value
  if (filterType.value) query.type = filterType.value
  if (filterStatus.value) query.status = filterStatus.value
  router.replace({ query: { ...query, ...(currentPage.value > 1 ? { page: currentPage.value } : {}) } })

  try {
    const data = await getAssets({ search: search.value, page: currentPage.value, type: filterType.value, status: filterStatus.value })
    assets.value = data.assets.map((a) => ({
      ...a,
      last_seen_formatted: formatDate(a.last_seen),
    }))
    total.value = data.total
    totalPages.value = data.pages
  } catch (err) {
    error.value = 'Failed to load assets. Is the backend running?'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const response = await fetch(exportUrl.value)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const today = new Date().toISOString().split('T')[0]
    a.download = `assets-${today}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export failed:', err)
  } finally {
    exporting.value = false
  }
}

const handleToggle = async (asset) => {
  await toggleAsset(asset.id)
  const newStatus = asset.status === 'active' ? 'inactive' : 'active'
  showToast(`${asset.name} marked as ${newStatus}`)
  fetchAssets()
}

const handleDelete = async (asset) => {
  showConfirm({
    title: 'Delete Asset',
    message: `Permanently delete "${asset.name}"? This cannot be undone.`,
    confirmText: 'Delete',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      await deleteAsset(asset.id)
      showToast(`${asset.name} deleted`, 'warning')
      fetchAssets()
    },
  })
}

const goToPage = (page) => {
  currentPage.value = page
  fetchAssets()
}

let searchTimeout = null

watch(search, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchAssets()
  }, 300)
})

watch([filterType, filterStatus], () => {
  currentPage.value = 1
  fetchAssets()
})

onMounted(fetchAssets)
</script>

<template>
  <div>
    <div class="d-flex align-items-center mb-4">
      <div>
        <h1 class="h3 mb-0">Assets</h1>
        <p class="text-muted mb-0">{{ total }} total asset{{ total !== 1 ? 's' : '' }}</p>
      </div>
      <router-link to="/assets/new" class="btn btn-primary ms-auto">
        <i class="bi bi-plus-lg me-1"></i>Add Asset
      </router-link>
      <button
        class="btn btn-success ms-2"
        :disabled="total === 0 || exporting"
        @click="handleExport"
      >
        <span v-if="exporting" class="spinner-border spinner-border-sm me-1"></span>
        <i v-else class="bi bi-download me-1"></i>
        {{ exporting ? 'Exporting…' : 'Export CSV' }}
      </button>
    </div>

    <!-- Search -->
    <div class="card mb-3">
      <div class="card-body py-2">
        <div class="row g-2 align-items-center">
          <div class="col">
            <div class="input-group">
              <span class="input-group-text bg-transparent border-end-0">
                <i class="bi bi-search text-muted"></i>
              </span>
              <input
                v-model="search"
                type="text"
                class="form-control border-start-0 ps-0"
                placeholder="Search assets…"
              />
            </div>
          </div>
          <div class="col-auto">
            <select v-model="filterType" class="form-select form-select-sm">
              <option value="">All Types</option>
              <option v-for="t in assetTypes" :key="t" :value="t">{{ t.charAt(0).toUpperCase() + t.slice(1) }}</option>
            </select>
          </div>
          <div class="col-auto">
            <select v-model="filterStatus" class="form-select form-select-sm">
              <option value="">All Statuses</option>
              <option v-for="s in statuses" :key="s" :value="s">{{ s.charAt(0).toUpperCase() + s.slice(1) }}</option>
            </select>
          </div>
          <div v-if="activeFilterCount > 0" class="col-auto">
            <button class="btn btn-sm btn-outline-danger" @click="clearFilters" title="Clear all filters">
              <i class="bi bi-funnel me-1"></i>Clear Filters
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div>
      Loading…
    </div>

    <!-- Table -->
    <div v-else class="card">
      <div class="card-body p-0">
        <AssetTable
          :assets="assets"
          @toggle="handleToggle"
          @delete="handleDelete"
        />
      </div>
    </div>

    <!-- Pagination -->
    <nav v-if="totalPages > 1" class="mt-3" aria-label="Asset pages">
      <ul class="pagination justify-content-center mb-0">
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <button class="page-link" @click="goToPage(currentPage - 1)">
            <i class="bi bi-chevron-left"></i>
          </button>
        </li>
        <li
          v-for="p in totalPages"
          :key="p"
          class="page-item"
          :class="{ active: p === currentPage }"
        >
          <button class="page-link" @click="goToPage(p)">{{ p }}</button>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <button class="page-link" @click="goToPage(currentPage + 1)">
            <i class="bi bi-chevron-right"></i>
          </button>
        </li>
      </ul>
    </nav>

    <ToastNotification
      :show="toast.show"
      :message="toast.message"
      :type="toast.type"
      @close="closeToast"
    />

    <ConfirmModal
      :show="confirmModal.show"
      :title="confirmModal.title"
      :message="confirmModal.message"
      :confirm-text="confirmModal.confirmText"
      :confirm-class="confirmModal.confirmClass"
      @confirm="handleConfirm"
      @cancel="cancelConfirm"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getClient, deleteClient } from '../api/index.js'
import StatusBadge from '../components/StatusBadge.vue'
import ToastNotification from '../components/ToastNotification.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { useToast } from '../composables/useToast.js'
import { useConfirm } from '../composables/useConfirm.js'

const route = useRoute()
const router = useRouter()
const client = ref(null)
const loading = ref(true)
const error = ref(null)

const { toast, showToast, closeToast } = useToast()
const { confirmModal, showConfirm, handleConfirm, cancelConfirm } = useConfirm()

const loadClient = async () => {
  loading.value = true
  try {
    client.value = await getClient(route.params.id)
  } catch (err) {
    error.value = err.response?.status === 404 ? 'Client not found.' : 'Failed to load client.'
  } finally {
    loading.value = false
  }
}

const handleDelete = () => {
  showConfirm({
    title: 'Delete Client',
    message: `Delete "${client.value.name}"? This cannot be undone.`,
    confirmText: 'Delete',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      try {
        await deleteClient(client.value.id)
        router.push('/clients')
      } catch (err) {
        showToast(err.response?.data?.error || 'Could not delete client.', 'danger')
      }
    },
  })
}

onMounted(loadClient)
</script>

<template>
  <div>
    <div class="mb-3">
      <router-link to="/clients" class="text-muted text-decoration-none small">
        <i class="bi bi-arrow-left me-1"></i>Back to Clients
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div>
      Loading…
    </div>

    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else-if="client">
      <div class="d-flex align-items-start mb-4">
        <div class="flex-grow-1">
          <h1 class="h3 mb-1">{{ client.name }}</h1>
          <p class="text-muted mb-0">{{ client.asset_count }} asset{{ client.asset_count !== 1 ? 's' : '' }}</p>
        </div>
        <button class="btn btn-outline-danger" @click="handleDelete">
          <i class="bi bi-trash me-1"></i>Delete Client
        </button>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-6">
          <div class="card h-100">
            <div class="card-header fw-semibold">Contact Info</div>
            <ul class="list-group list-group-flush">
              <li class="list-group-item d-flex justify-content-between">
                <span class="text-muted">Email</span>
                <span>{{ client.contact_email || '—' }}</span>
              </li>
              <li class="list-group-item d-flex justify-content-between">
                <span class="text-muted">Phone</span>
                <span>{{ client.phone || '—' }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header fw-semibold">
          Assets
          <span class="badge bg-secondary ms-1">{{ client.assets.length }}</span>
        </div>
        <div v-if="client.assets.length === 0" class="card-body text-muted">
          No assets assigned to this client.
        </div>
        <div v-else class="table-responsive">
          <table class="table table-sm mb-0">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Status</th>
                <th>Serial Number</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="asset in client.assets" :key="asset.id">
                <td>
                  <router-link :to="`/assets/${asset.id}`">{{ asset.name }}</router-link>
                </td>
                <td class="text-capitalize">{{ asset.asset_type }}</td>
                <td><StatusBadge :status="asset.status" /></td>
                <td><code>{{ asset.serial_number || '—' }}</code></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <ToastNotification :show="toast.show" :message="toast.message" :type="toast.type" @close="closeToast" />
    <ConfirmModal :show="confirmModal.show" :title="confirmModal.title" :message="confirmModal.message"
      :confirm-text="confirmModal.confirmText" :confirm-class="confirmModal.confirmClass"
      @confirm="handleConfirm" @cancel="cancelConfirm" />
  </div>
</template>

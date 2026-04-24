import { ref } from 'vue'

export function useToast() {
    const toast = ref({ show: false, message: '', type: 'success' })

    const showToast = (message, type = 'success') => {
        toast.value = { show: true, message, type }
    }

    const closeToast = () => {
        toast.value.show = false
    }

    return { toast, showToast, closeToast }
}

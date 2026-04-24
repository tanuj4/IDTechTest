import { ref } from 'vue'

export function useConfirm() {
    const confirmModal = ref({ show: false, title: '', message: '', confirmText: '', confirmClass: '', onConfirm: null })

    const showConfirm = ({ title, message, confirmText, confirmClass, onConfirm }) => {
        confirmModal.value = { show: true, title, message, confirmText, confirmClass: confirmClass || 'btn-danger', onConfirm }
    }

    const handleConfirm = () => {
        confirmModal.value.show = false
        if (confirmModal.value.onConfirm) confirmModal.value.onConfirm()
    }

    const cancelConfirm = () => {
        confirmModal.value.show = false
    }

    return { confirmModal, showConfirm, handleConfirm, cancelConfirm }
}

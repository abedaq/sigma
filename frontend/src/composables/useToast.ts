import { ref } from 'vue';

export interface ToastItem {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration: number; // ms
}

const toasts = ref<ToastItem[]>([]);

export function useToast() {
  function show(message: string, type: ToastItem['type'] = 'info', title?: string, duration: number = 4000) {
    const id = 'toast_' + Math.random().toString(36).substring(2, 9);
    const item: ToastItem = {
      id,
      type,
      title,
      message,
      duration
    };

    toasts.value.push(item);

    if (duration > 0) {
      setTimeout(() => {
        remove(id);
      }, duration);
    }

    return id;
  }

  function success(message: string, title: string = 'نجاح') {
    return show(message, 'success', title, 3500);
  }

  function error(message: string, title: string = 'خطأ') {
    return show(message, 'error', title, 5000);
  }

  function warning(message: string, title: string = 'تنبيه') {
    return show(message, 'warning', title, 4000);
  }

  function info(message: string, title: string = 'معلومة') {
    return show(message, 'info', title, 3500);
  }

  function remove(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }

  return {
    toasts,
    show,
    success,
    error,
    warning,
    info,
    remove
  };
}

"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { CheckIcon, ErrorIcon, InfoIcon, WarningIcon, CloseIcon } from "./Icon";

/**
 * Toast Component
 * 세련된 알림 메시지 시스템
 */

export type ToastVariant = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
}

interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const ToastItem = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ toast, onClose }, ref) => {
    const variantStyles = {
      success: "bg-success/10 border-success/20 text-success",
      error: "bg-error/10 border-error/20 text-error",
      warning: "bg-warning/10 border-warning/20 text-warning",
      info: "bg-info/10 border-info/20 text-info",
    };

    const icons = {
      success: CheckIcon,
      error: ErrorIcon,
      warning: WarningIcon,
      info: InfoIcon,
    };

    const Icon = icons[toast.variant];

    React.useEffect(() => {
      const timer = setTimeout(() => {
        onClose(toast.id);
      }, toast.duration || 3000);

      return () => clearTimeout(timer);
    }, [toast.id, toast.duration, onClose]);

    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center gap-3 p-4 rounded-lg border shadow-lg",
          "animate-in slide-in-from-right duration-300",
          "min-w-[320px] max-w-md",
          variantStyles[toast.variant]
        )}
        role="alert"
      >
        <Icon className="flex-shrink-0" fontSize="small" />
        <p className="flex-1 text-sm font-medium">{toast.message}</p>
        <button
          onClick={() => onClose(toast.id)}
          className="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
          aria-label="닫기"
        >
          <CloseIcon fontSize="small" />
        </button>
      </div>
    );
  }
);

ToastItem.displayName = "ToastItem";

/**
 * Toast Container
 */
interface ToastContainerProps {
  toasts: Toast[];
  onClose: (id: string) => void;
}

export const ToastContainer = React.forwardRef<
  HTMLDivElement,
  ToastContainerProps
>(({ toasts, onClose }, ref) => {
  if (toasts.length === 0) return null;

  return (
    <div
      ref={ref}
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
});

ToastContainer.displayName = "ToastContainer";

/**
 * Toast Hook
 */
interface ToastContextValue {
  toasts: Toast[];
  showToast: (
    message: string,
    variant?: ToastVariant,
    duration?: number
  ) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
}

const ToastContext = React.createContext<ToastContextValue | undefined>(
  undefined
);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = React.useCallback(
    (message: string, variant: ToastVariant = "info", duration = 3000) => {
      const id = Math.random().toString(36).substring(2, 9);
      const toast: Toast = { id, message, variant, duration };
      setToasts((prev) => [...prev, toast]);
    },
    []
  );

  const success = React.useCallback(
    (message: string, duration?: number) => {
      showToast(message, "success", duration);
    },
    [showToast]
  );

  const error = React.useCallback(
    (message: string, duration?: number) => {
      showToast(message, "error", duration);
    },
    [showToast]
  );

  const warning = React.useCallback(
    (message: string, duration?: number) => {
      showToast(message, "warning", duration);
    },
    [showToast]
  );

  const info = React.useCallback(
    (message: string, duration?: number) => {
      showToast(message, "info", duration);
    },
    [showToast]
  );

  const value = React.useMemo(
    () => ({
      toasts,
      showToast,
      success,
      error,
      warning,
      info,
    }),
    [toasts, showToast, success, error, warning, info]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};
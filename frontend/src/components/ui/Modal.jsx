/**
 * Modal - Accessible modal dialog with animations
 * Usage: <Modal isOpen={true} onClose={() => {}} title="Modal Title">Content</Modal>
 */
import { useEffect, useRef, useCallback } from "react";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";

const Modal = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = "md",
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  footer,
  className = "",
  headerClassName = "",
  bodyClassName = "",
  footerClassName = "",
}) => {
  const modalRef = useRef(null);
  const previousActiveElement = useRef(null);

  const sizes = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
    xl: "max-w-4xl",
    full: "max-w-[90vw] h-[90vh]",
  };

  // Handle escape key
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape" && closeOnEscape) {
        onClose();
      }
    },
    [closeOnEscape, onClose]
  );

  // Handle overlay click
  const handleOverlayClick = (e) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  // Focus management
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement;
      modalRef.current?.focus();
      document.body.style.overflow = "hidden";
      document.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", handleKeyDown);
      if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, handleKeyDown]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={handleOverlayClick}
          aria-modal="true"
          role="dialog"
          aria-labelledby="modal-title"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />

          {/* Modal Content */}
          <motion.div
            ref={modalRef}
            tabIndex={-1}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", duration: 0.3 }}
            className={`
              relative w-full ${sizes[size]}
              bg-gray-900 border border-gray-700/50
              rounded-2xl shadow-2xl
              overflow-hidden
              ${className}
            `}
          >
            {/* Header */}
            {(title || showCloseButton) && (
              <div
                className={`
                flex items-center justify-between
                px-6 py-4 border-b border-gray-700/50
                ${headerClassName}
              `}
              >
                <div>
                  {title && (
                    <h2
                      id="modal-title"
                      className="text-xl font-semibold text-white"
                    >
                      {title}
                    </h2>
                  )}
                  {description && (
                    <p className="mt-1 text-sm text-gray-400">{description}</p>
                  )}
                </div>
                {showCloseButton && (
                  <button
                    onClick={onClose}
                    className="
                      p-2 rounded-xl text-gray-400
                      hover:text-white hover:bg-gray-800
                      transition-all duration-200
                      focus:outline-none focus:ring-2 focus:ring-blue-500
                    "
                    aria-label="Close modal"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                )}
              </div>
            )}

            {/* Body */}
            <div
              className={`
              px-6 py-6 max-h-[60vh] overflow-y-auto
              ${bodyClassName}
            `}
            >
              {children}
            </div>

            {/* Footer */}
            {footer && (
              <div
                className={`
                px-6 py-4 border-t border-gray-700/50
                bg-gray-800/30
                ${footerClassName}
              `}
              >
                {footer}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Confirmation Modal Preset
export const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "danger",
  isLoading = false,
}) => {
  const variants = {
    danger: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
    warning: "bg-amber-600 hover:bg-amber-700 focus:ring-amber-500",
    success: "bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500",
    primary: "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500",
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="
              px-4 py-2 rounded-xl
              text-gray-300 bg-gray-800 border border-gray-700
              hover:bg-gray-700 hover:text-white
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-gray-500
              disabled:opacity-50
            "
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`
              px-4 py-2 rounded-xl text-white
              ${variants[variant]}
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900
              disabled:opacity-50
              flex items-center space-x-2
            `}
          >
            {isLoading && (
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            )}
            <span>{confirmText}</span>
          </button>
        </div>
      }
    >
      <p className="text-gray-300">{message}</p>
    </Modal>
  );
};

export default Modal;

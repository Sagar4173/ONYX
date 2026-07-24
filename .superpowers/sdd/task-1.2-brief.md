# Task 1.2: Add ConfirmDialog component

**Files:**
- Modify: `frontend/src/styles/components.jsx`

**Task:** Add a reusable ConfirmDialog component to `frontend/src/styles/components.jsx` and export it.

## Requirements

Add a `ConfirmDialog` component with these props:
- `isOpen` — boolean, controls visibility (component returns null when false)
- `onClose` — callback when dialog is dismissed
- `onConfirm` — callback when confirm button is clicked
- `title = "Confirm"` — dialog title
- `message = "Are you sure?"` — dialog body text
- `confirmLabel = "Confirm"` — confirm button text
- `cancelLabel = "Cancel"` — cancel button text
- `variant = "danger"` — one of "danger", "warning", "primary" — controls button color
- `requireTypeToConfirm = false` — if true, user must type `confirmText` to enable the confirm button
- `confirmText = ""` — the text the user must type when `requireTypeToConfirm` is true

Uses `useState` and `useId` from React. Renders as a fixed overlay with backdrop blur, a centered card with `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` pointing to the title.

Implements `e.stopPropagation()` on the inner card so clicking the overlay (backdrop) closes the dialog but clicking the card does not.

The confirm button calls `onConfirm()` then `onClose()`.

## Code

Paste this into `styles/components.jsx` before the `export default {` line:

```jsx
// =============================================================================
// CONFIRM DIALOG COMPONENT
// =============================================================================

export const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm",
  message = "Are you sure?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  requireTypeToConfirm = false,
  confirmText = "",
}) => {
  const [typedText, setTypedText] = useState("");
  const titleId = useId();

  if (!isOpen) return null;

  const buttonColors = {
    danger: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
    warning: "bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500",
    primary: "bg-blue-600 hover:bg-blue-700 focus:ring-blue-500",
  };

  const canConfirm = requireTypeToConfirm
    ? typedText === confirmText
    : true;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700/50 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id={titleId} className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-gray-400 text-sm mb-4">{message}</p>

        {requireTypeToConfirm && (
          <div className="mb-4">
            <p className="text-sm text-gray-400 mb-2">
              Type <span className="font-mono text-red-400 bg-red-900/30 px-1.5 py-0.5 rounded">{confirmText}</span> to confirm:
            </p>
            <input
              type="text"
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700/50 rounded-lg text-white text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              autoFocus
            />
          </div>
        )}

        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={() => { onConfirm(); onClose(); }}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-all disabled:opacity-50 ${buttonColors[variant]}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
```

Then add `ConfirmDialog` to the `export default {` block at the bottom of `styles/components.jsx`.

## Verification

1. Run `npm run build` — must complete without errors
2. Verify the component is importable: `import { ConfirmDialog } from "../../styles/components"` should work

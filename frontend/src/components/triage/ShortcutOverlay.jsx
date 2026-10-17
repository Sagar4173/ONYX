import { Modal } from "../ui/StyleComponents";

const SHORTCUT_ROWS = [
  ["J / K", "Next / previous finding"],
  ["A", "Accept (mark true positive)"],
  ["F", "False positive"],
  ["D", "Dismissed"],
  ["U", "Untriage (clear your label)"],
  ["?", "Show / hide this overlay"],
  ["Esc", "Close"],
];

export function ShortcutOverlay({ isOpen, onClose }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Triage shortcuts" size="sm">
      <dl className="space-y-2">
        {SHORTCUT_ROWS.map(([keys, description]) => (
          <div key={keys} className="flex items-center justify-between gap-4 text-sm">
            <dt>
              <kbd className="px-2 py-0.5 bg-gray-700/60 border border-gray-600 rounded text-xs font-mono text-gray-200">
                {keys}
              </kbd>
            </dt>
            <dd className="text-gray-300 text-right">{description}</dd>
          </div>
        ))}
      </dl>
    </Modal>
  );
}

export function KeyboardHintStrip() {
  return (
    <p className="text-[11px] text-gray-500 text-center pt-2">
      J/K move · A accept · F false positive · D dismiss · U untriage · ? shortcuts
    </p>
  );
}

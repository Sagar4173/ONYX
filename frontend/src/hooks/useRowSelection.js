import { useCallback, useRef, useState } from "react";

export function useRowSelection() {
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const anchorIdRef = useRef(null);

  const toggle = useCallback((id, { shift = false, orderedIds = [] } = {}) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      const anchor = anchorIdRef.current;
      const hasRange =
        shift && anchor && orderedIds.includes(anchor) && orderedIds.includes(id) && anchor !== id;

      if (hasRange) {
        const a = orderedIds.indexOf(anchor);
        const b = orderedIds.indexOf(id);
        const [lo, hi] = a <= b ? [a, b] : [b, a];
        for (const rowId of orderedIds.slice(lo, hi + 1)) next.add(rowId);
      } else if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      anchorIdRef.current = id;
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    anchorIdRef.current = null;
    setSelectedIds(new Set());
  }, []);

  return {
    selectedIds,
    count: selectedIds.size,
    isSelected: (id) => selectedIds.has(id),
    toggle,
    clear,
  };
}

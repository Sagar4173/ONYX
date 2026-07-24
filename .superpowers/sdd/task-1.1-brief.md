# Task 1.1: Add DataTable component

**Files:**
- Modify: `frontend/src/styles/components.jsx`

**Task:** Add a reusable DataTable component to `frontend/src/styles/components.jsx` and export it.

## Requirements

Add a `DataTable` component with these props:
- `columns = []` — array of `{ key, label, sortable, render, width }`
- `data = []` — array of row objects
- `onSort` — callback when a sortable column header is clicked
- `sortKey` — currently sorted column key
- `sortDirection` — "asc" or "desc"
- `onPageChange` — callback with new page number
- `currentPage = 1` — current page
- `pageSize = 20` — rows per page
- `totalItems` — total rows (for external pagination)
- `loading = false` — show skeleton rows when true
- `emptyMessage = "No data available"` — shown when data is empty and not loading
- `onRowClick` — callback with the row object
- `className = ""` — additional classes

Also add a helper `TableSkeleton` component (internal, not exported) that renders 5 rows × N columns of shimmer placeholders.

## Code

Paste this into `styles/components.jsx` before the `export default {` line:

```jsx
// =============================================================================
// DATA TABLE COMPONENT
// =============================================================================

const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <>
    {Array.from({ length: rows }).map((_, i) => (
      <tr key={i} className="border-b border-gray-700/50">
        {Array.from({ length: columns }).map((_, j) => (
          <td key={j} className="px-4 py-3">
            <div className="h-4 bg-gray-700/50 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
          </td>
        ))}
      </tr>
    ))}
  </>
);

export const DataTable = ({
  columns = [],
  data = [],
  onSort,
  sortKey,
  sortDirection,
  onPageChange,
  currentPage = 1,
  pageSize = 20,
  totalItems,
  loading = false,
  emptyMessage = "No data available",
  onRowClick,
  className = "",
}) => {
  const totalPages = Math.ceil((totalItems || data.length) / pageSize);

  return (
    <div className={`overflow-x-auto rounded-xl border border-gray-700/50 ${className}`}>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-800/50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${
                  col.sortable ? "cursor-pointer hover:text-white select-none" : ""
                }`}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => {
                  if (col.sortable && onSort) {
                    onSort(col.key);
                  }
                }}
              >
                <span className="flex items-center gap-1">
                  {col.label}
                  {col.sortable && sortKey === col.key && (
                    <span className="text-blue-400">
                      {sortDirection === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700/50">
          {loading ? (
            <TableSkeleton rows={5} columns={columns.length} />
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-gray-400"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr
                key={row.id || row._id || i}
                className={`transition-colors duration-150 ${
                  onRowClick ? "cursor-pointer hover:bg-gray-800/30" : "hover:bg-gray-800/10"
                }`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-gray-300">
                    {col.render ? col.render(row[col.key], row) : row[col.key] ?? "-"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-700/50 bg-gray-800/30">
          <span className="text-sm text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-1 text-sm rounded-lg bg-gray-700/50 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

Then add `DataTable` to the `export default {` block at the bottom of `styles/components.jsx`.

## Verification

1. Run `npm run dev` — app must start without errors
2. Verify the component is importable: `import { DataTable } from "../../styles/components"` should work

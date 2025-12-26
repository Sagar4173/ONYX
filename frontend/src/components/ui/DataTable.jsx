/**
 * DataTable - Advanced data table with sorting, filtering, pagination, and row actions
 */
import React, { useState, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EllipsisVerticalIcon,
  ArrowsUpDownIcon,
} from "@heroicons/react/24/outline";

const DataTable = ({
  columns = [],
  data = [],
  sortable = true,
  filterable = true,
  paginated = true,
  pageSize: initialPageSize = 10,
  selectable = false,
  onRowClick,
  onSelectionChange,
  rowActions,
  emptyMessage = "No data available",
  loading = false,
  stickyHeader = false,
  striped = false,
  className = "",
}) => {
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [columnFilters, setColumnFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);

  // Filtering
  const filteredData = useMemo(() => {
    let result = [...data];

    // Global search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => {
          const value = row[col.key];
          return value?.toString().toLowerCase().includes(query);
        })
      );
    }

    // Column filters
    Object.entries(columnFilters).forEach(([key, filterValue]) => {
      if (filterValue) {
        result = result.filter((row) =>
          row[key]?.toString().toLowerCase().includes(filterValue.toLowerCase())
        );
      }
    });

    return result;
  }, [data, searchQuery, columnFilters, columns]);

  // Sorting
  const sortedData = useMemo(() => {
    if (!sortColumn) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredData, sortColumn, sortDirection]);

  // Pagination
  const paginatedData = useMemo(() => {
    if (!paginated) return sortedData;
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize, paginated]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = useCallback(
    (columnKey) => {
      if (!sortable) return;
      if (sortColumn === columnKey) {
        setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        setSortColumn(columnKey);
        setSortDirection("asc");
      }
    },
    [sortColumn, sortable]
  );

  const handleSelectAll = useCallback(
    (checked) => {
      if (checked) {
        const allIds = paginatedData.map((row) => row.id);
        setSelectedRows(new Set(allIds));
      } else {
        setSelectedRows(new Set());
      }
    },
    [paginatedData]
  );

  const handleSelectRow = useCallback((id, checked) => {
    setSelectedRows((prev) => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  }, []);

  React.useEffect(() => {
    onSelectionChange?.(Array.from(selectedRows));
  }, [selectedRows, onSelectionChange]);

  // Reset page when filters change
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, columnFilters]);

  const SortIcon = ({ column }) => {
    if (sortColumn !== column) {
      return <ArrowsUpDownIcon className="h-4 w-4 text-gray-500" />;
    }
    return sortDirection === "asc" ? (
      <ChevronUpIcon className="h-4 w-4 text-blue-400" />
    ) : (
      <ChevronDownIcon className="h-4 w-4 text-blue-400" />
    );
  };

  return (
    <div
      className={`bg-gray-800/30 rounded-xl border border-gray-700/50 overflow-hidden ${className}`}
    >
      {/* Toolbar */}
      {(filterable || selectable) && (
        <div className="p-4 border-b border-gray-700/50 flex items-center justify-between gap-4">
          {filterable && (
            <div className="relative flex-1 max-w-md">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="w-full h-10 pl-10 pr-4 bg-gray-800/50 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div className="flex items-center gap-2">
            {filterable && (
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`p-2 rounded-lg transition-colors ${
                  showFilters
                    ? "bg-blue-500/20 text-blue-400"
                    : "text-gray-400 hover:bg-gray-700"
                }`}
              >
                <FunnelIcon className="h-5 w-5" />
              </button>
            )}

            {selectedRows.size > 0 && (
              <span className="text-sm text-gray-400">
                {selectedRows.size} selected
              </span>
            )}
          </div>
        </div>
      )}

      {/* Column Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-b border-gray-700/50"
          >
            <div className="p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {columns
                .filter((col) => col.filterable !== false)
                .map((column) => (
                  <div key={column.key}>
                    <label className="block text-xs text-gray-400 mb-1">
                      {column.label}
                    </label>
                    <input
                      type="text"
                      value={columnFilters[column.key] || ""}
                      onChange={(e) =>
                        setColumnFilters((prev) => ({
                          ...prev,
                          [column.key]: e.target.value,
                        }))
                      }
                      placeholder={`Filter ${column.label}`}
                      className="w-full h-8 px-3 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className={stickyHeader ? "sticky top-0 z-10" : ""}>
            <tr className="bg-gray-800/50 border-b border-gray-700/50">
              {selectable && (
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={
                      paginatedData.length > 0 &&
                      paginatedData.every((row) => selectedRows.has(row.id))
                    }
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-600 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-800"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() =>
                    column.sortable !== false && handleSort(column.key)
                  }
                  className={`
                    px-4 py-3 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider
                    ${
                      sortable && column.sortable !== false
                        ? "cursor-pointer hover:text-white"
                        : ""
                    }
                    ${column.width ? `w-[${column.width}]` : ""}
                  `}
                  style={{ width: column.width }}
                >
                  <div className="flex items-center gap-2">
                    {column.label}
                    {sortable && column.sortable !== false && (
                      <SortIcon column={column.key} />
                    )}
                  </div>
                </th>
              ))}
              {rowActions && <th className="w-16 px-4 py-3" />}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-700/30">
                  {selectable && (
                    <td className="px-4 py-4">
                      <div className="w-4 h-4 bg-gray-700 rounded animate-pulse" />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-4">
                      <div
                        className="h-4 bg-gray-700 rounded animate-pulse"
                        style={{ width: `${Math.random() * 40 + 40}%` }}
                      />
                    </td>
                  ))}
                  {rowActions && (
                    <td className="px-4 py-4">
                      <div className="w-6 h-6 bg-gray-700 rounded animate-pulse" />
                    </td>
                  )}
                </tr>
              ))
            ) : paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={
                    columns.length + (selectable ? 1 : 0) + (rowActions ? 1 : 0)
                  }
                  className="px-4 py-12 text-center text-gray-400"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => (
                <motion.tr
                  key={row.id || rowIndex}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: rowIndex * 0.02 }}
                  onClick={() => onRowClick?.(row)}
                  className={`
                    border-b border-gray-700/30 transition-colors
                    ${onRowClick ? "cursor-pointer" : ""}
                    ${striped && rowIndex % 2 === 1 ? "bg-gray-800/20" : ""}
                    ${
                      selectedRows.has(row.id)
                        ? "bg-blue-500/10"
                        : "hover:bg-gray-700/30"
                    }
                  `}
                >
                  {selectable && (
                    <td
                      className="px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={selectedRows.has(row.id)}
                        onChange={(e) =>
                          handleSelectRow(row.id, e.target.checked)
                        }
                        className="w-4 h-4 rounded border-gray-600 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-800"
                      />
                    </td>
                  )}
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className="px-4 py-4 text-sm text-gray-300"
                    >
                      {column.render
                        ? column.render(row[column.key], row)
                        : row[column.key]}
                    </td>
                  ))}
                  {rowActions && (
                    <td
                      className="px-4 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <RowActionsMenu actions={rowActions} row={row} />
                    </td>
                  )}
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {paginated && totalPages > 1 && (
        <div className="p-4 border-t border-gray-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="h-8 px-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {[10, 25, 50, 100].map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">
              {(currentPage - 1) * pageSize + 1} -{" "}
              {Math.min(currentPage * pageSize, sortedData.length)} of{" "}
              {sortedData.length}
            </span>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeftIcon className="h-4 w-4" />
                <ChevronLeftIcon className="h-4 w-4 -ml-3" />
              </button>
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </button>

              {/* Page numbers */}
              <div className="flex items-center gap-1 mx-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let page;
                  if (totalPages <= 5) {
                    page = i + 1;
                  } else if (currentPage <= 3) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    page = totalPages - 4 + i;
                  } else {
                    page = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`
                        w-8 h-8 rounded-lg text-sm font-medium transition-colors
                        ${
                          currentPage === page
                            ? "bg-blue-500 text-white"
                            : "text-gray-400 hover:text-white hover:bg-gray-700"
                        }
                      `}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() =>
                  setCurrentPage((p) => Math.min(totalPages, p + 1))
                }
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRightIcon className="h-4 w-4" />
                <ChevronRightIcon className="h-4 w-4 -ml-3" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Row Actions Menu
const RowActionsMenu = ({ actions, row }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700"
      >
        <EllipsisVerticalIcon className="h-5 w-5" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="absolute right-0 top-full mt-1 w-48 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden"
            >
              {actions.map((action, index) => {
                const Icon = action.icon;
                return (
                  <button
                    key={index}
                    onClick={() => {
                      action.onClick?.(row);
                      setIsOpen(false);
                    }}
                    className={`
                      w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left
                      transition-colors hover:bg-gray-700/50
                      ${
                        action.danger
                          ? "text-red-400 hover:text-red-300"
                          : "text-gray-300 hover:text-white"
                      }
                    `}
                  >
                    {Icon && <Icon className="h-4 w-4" />}
                    {action.label}
                  </button>
                );
              })}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DataTable;

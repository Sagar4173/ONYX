/**
 * Production-safe Logger Utility
 * Silences all console output in production to prevent information leakage
 */

const isDevelopment = import.meta.env.DEV;

// No-op function for production
const noop = () => {};

/**
 * Logger object that only outputs in development mode
 * In production, all methods are no-ops
 */
const logger = {
  log: isDevelopment ? console.log.bind(console) : noop,
  info: isDevelopment ? console.info.bind(console) : noop,
  warn: isDevelopment ? console.warn.bind(console) : noop,
  error: isDevelopment ? console.error.bind(console) : noop,
  debug: isDevelopment ? console.debug.bind(console) : noop,
  table: isDevelopment ? console.table.bind(console) : noop,
  group: isDevelopment ? console.group.bind(console) : noop,
  groupEnd: isDevelopment ? console.groupEnd.bind(console) : noop,
  time: isDevelopment ? console.time.bind(console) : noop,
  timeEnd: isDevelopment ? console.timeEnd.bind(console) : noop,
};

export default logger;

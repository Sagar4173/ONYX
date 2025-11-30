import { useState, useEffect, useRef } from "react";
import api from "../services/api";
import toast from "react-hot-toast";

/**
 * Custom hook to track scan progress and status
 */
export const useScanTracker = (scanId, onStatusChange) => {
  const [scanStatus, setScanStatus] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const intervalRef = useRef(null);
  const toastRef = useRef(null);

  const startTracking = () => {
    if (!scanId || isTracking) return;

    setIsTracking(true);
    // Show initial tracking toast
    toastRef.current = toast.loading(
      `🔄 Tracking scan progress... (ID: ${scanId.slice(-8)})`,
      { duration: Infinity }
    );

    // Poll every 5 seconds
    intervalRef.current = setInterval(async () => {
      try {
        const status = await api.getScanStatus(scanId);

        if (status) {
          setScanStatus(status);

          // Call callback if provided
          if (onStatusChange) {
            onStatusChange(status);
          }

          // Handle status changes
          if (status.status === "completed") {
            // Scan completed successfully
            toast.dismiss(toastRef.current);
            toast.success(
              `✅ Scan completed! Found ${status.total_findings} issues.`,
              { duration: 6000 }
            );
            stopTracking();
          } else if (status.status === "failed") {
            // Scan failed
            toast.dismiss(toastRef.current);
            toast.error(
              `❌ Scan failed: ${status.error_message || "Unknown error"}`,
              { duration: 8000 }
            );
            stopTracking();
          } else if (status.status === "running") {
            // Update progress toast
            toast.dismiss(toastRef.current);
            toastRef.current = toast.loading(
              `🔄 Scan in progress... (ID: ${scanId.slice(-8)})`,
              { duration: Infinity }
            );
          }
        }
      } catch (error) {
        console.error("Error checking scan status:", error);
        // Don't stop tracking on error, just log it
      }
    }, 5000); // Poll every 5 seconds
  };

  const stopTracking = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (toastRef.current) {
      toast.dismiss(toastRef.current);
      toastRef.current = null;
    }

    setIsTracking(false);  };

  // Auto-start tracking when scanId is provided
  useEffect(() => {
    if (scanId) {
      startTracking();
    }

    // Cleanup on unmount
    return () => {
      stopTracking();
    };
  }, [scanId]);

  // Cleanup interval on component unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (toastRef.current) {
        toast.dismiss(toastRef.current);
      }
    };
  }, []);

  return {
    scanStatus,
    isTracking,
    startTracking,
    stopTracking,
  };
};

export default useScanTracker;

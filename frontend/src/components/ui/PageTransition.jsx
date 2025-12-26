/**
 * PageTransition - Smooth page transitions with Framer Motion
 */
import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLocation } from "react-router-dom";

const pageVariants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  enter: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.25, 0.46, 0.45, 0.94],
      when: "beforeChildren",
      staggerChildren: 0.05,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: {
      duration: 0.2,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
};

const childVariants = {
  initial: { opacity: 0, y: 20 },
  enter: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

/**
 * PageTransition - Wraps pages with entry/exit animations
 */
export const PageTransition = ({ children, className = "" }) => {
  return (
    <motion.div
      initial="initial"
      animate="enter"
      exit="exit"
      variants={pageVariants}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * AnimatedSection - For staggered section animations
 */
export const AnimatedSection = ({ children, delay = 0, className = "" }) => {
  return (
    <motion.div
      variants={childVariants}
      initial="initial"
      animate="enter"
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * StaggeredList - Animates list items with stagger effect
 */
export const StaggeredList = ({
  children,
  staggerDelay = 0.05,
  className = "",
  itemClassName = "",
}) => {
  return (
    <motion.div
      initial="initial"
      animate="enter"
      variants={{
        initial: {},
        enter: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
    >
      {React.Children.map(children, (child, i) => (
        <motion.div
          key={i}
          variants={{
            initial: { opacity: 0, y: 20 },
            enter: {
              opacity: 1,
              y: 0,
              transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
            },
          }}
          className={itemClassName}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

/**
 * FadeIn - Simple fade in animation
 */
export const FadeIn = ({
  children,
  delay = 0,
  duration = 0.5,
  direction = "up",
  className = "",
}) => {
  const directionOffset = {
    up: { y: 20 },
    down: { y: -20 },
    left: { x: 20 },
    right: { x: -20 },
    none: {},
  };

  return (
    <motion.div
      initial={{ opacity: 0, ...directionOffset[direction] }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * ScaleIn - Scale up animation
 */
export const ScaleIn = ({
  children,
  delay = 0,
  duration = 0.4,
  className = "",
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * SlideIn - Slide animation from direction
 */
export const SlideIn = ({
  children,
  direction = "left",
  delay = 0,
  className = "",
}) => {
  const variants = {
    left: { initial: { x: -50, opacity: 0 }, animate: { x: 0, opacity: 1 } },
    right: { initial: { x: 50, opacity: 0 }, animate: { x: 0, opacity: 1 } },
    up: { initial: { y: 50, opacity: 0 }, animate: { y: 0, opacity: 1 } },
    down: { initial: { y: -50, opacity: 0 }, animate: { y: 0, opacity: 1 } },
  };

  return (
    <motion.div
      initial={variants[direction].initial}
      animate={variants[direction].animate}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * AnimatedPresence wrapper for conditional rendering
 */
export const ConditionalAnimation = ({
  show,
  children,
  type = "fade",
  className = "",
}) => {
  const animations = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
    },
    scale: {
      initial: { opacity: 0, scale: 0.9 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.9 },
    },
    slideUp: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 },
    },
    slideDown: {
      initial: { opacity: 0, y: -20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: 20 },
    },
  };

  return (
    <AnimatePresence mode="wait">
      {show && (
        <motion.div
          key="content"
          {...animations[type]}
          transition={{ duration: 0.2 }}
          className={className}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/**
 * Hover Animation Wrapper
 */
export const HoverScale = ({
  children,
  scale = 1.02,
  className = "",
  whileTap = 0.98,
}) => {
  return (
    <motion.div
      whileHover={{ scale }}
      whileTap={{ scale: whileTap }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * Pulse Animation
 */
export const PulseAnimation = ({ children, className = "" }) => {
  return (
    <motion.div
      animate={{
        scale: [1, 1.05, 1],
        opacity: [1, 0.8, 1],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;

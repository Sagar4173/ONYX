/**
 * SearchInput - Advanced search input with debounce, suggestions, and keyboard navigation
 */
import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
} from "@heroicons/react/24/outline";

const SearchInput = ({
  value = "",
  onChange,
  onSearch,
  placeholder = "Search...",
  suggestions = [],
  recentSearches = [],
  trendingSearches = [],
  debounceMs = 300,
  showClearButton = true,
  autoFocus = false,
  size = "md",
  variant = "default",
  className = "",
  isLoading = false,
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const debounceTimer = useRef(null);

  const sizes = {
    sm: "h-9 text-sm px-3",
    md: "h-11 text-base px-4",
    lg: "h-13 text-lg px-5",
  };

  const variants = {
    default:
      "bg-gray-800/50 border border-gray-700 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20",
    glass: "glass-card border-white/10 focus-within:border-white/20",
    minimal:
      "bg-transparent border-b-2 border-gray-700 focus-within:border-blue-500 rounded-none",
  };

  const allSuggestions = [
    ...recentSearches.map((s) => ({ type: "recent", text: s })),
    ...trendingSearches.map((s) => ({ type: "trending", text: s })),
    ...suggestions.map((s) => ({
      type: "suggestion",
      text: typeof s === "string" ? s : s.text,
      ...s,
    })),
  ];

  const filteredSuggestions = inputValue
    ? allSuggestions.filter((s) =>
        s.text.toLowerCase().includes(inputValue.toLowerCase())
      )
    : allSuggestions;

  const handleInputChange = useCallback(
    (e) => {
      const newValue = e.target.value;
      setInputValue(newValue);
      setSelectedIndex(-1);

      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      debounceTimer.current = setTimeout(() => {
        onChange?.(newValue);
      }, debounceMs);
    },
    [onChange, debounceMs]
  );

  const handleSubmit = useCallback(
    (searchValue = inputValue) => {
      onSearch?.(searchValue);
      setIsFocused(false);
    },
    [inputValue, onSearch]
  );

  const handleKeyDown = (e) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        e.preventDefault();
        if (selectedIndex >= 0 && filteredSuggestions[selectedIndex]) {
          setInputValue(filteredSuggestions[selectedIndex].text);
          handleSubmit(filteredSuggestions[selectedIndex].text);
        } else {
          handleSubmit();
        }
        break;
      case "Escape":
        setIsFocused(false);
        inputRef.current?.blur();
        break;
      default:
        break;
    }
  };

  const handleClear = () => {
    setInputValue("");
    onChange?.("");
    inputRef.current?.focus();
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion.text);
    handleSubmit(suggestion.text);
  };

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  const showDropdown = isFocused && filteredSuggestions.length > 0;

  return (
    <div className={`relative ${className}`}>
      <div
        className={`
          flex items-center rounded-xl
          ${sizes[size]}
          ${variants[variant]}
          transition-all duration-200
        `}
      >
        <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />

        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 150)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className={`
            flex-1 bg-transparent border-none outline-none
            text-white placeholder-gray-400
            ml-3
          `}
        />

        {isLoading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"
          />
        )}

        {showClearButton && inputValue && !isLoading && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={handleClear}
            className="p-1 rounded-full hover:bg-gray-700/50 transition-colors"
          >
            <XMarkIcon className="h-4 w-4 text-gray-400" />
          </motion.button>
        )}
      </div>

      {/* Suggestions dropdown */}
      <AnimatePresence>
        {showDropdown && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`
              absolute top-full left-0 right-0 mt-2
              bg-gray-800 border border-gray-700 rounded-xl
              shadow-xl overflow-hidden z-50
              max-h-80 overflow-y-auto
            `}
          >
            {filteredSuggestions.map((suggestion, index) => (
              <button
                key={`${suggestion.type}-${index}`}
                onClick={() => handleSuggestionClick(suggestion)}
                className={`
                  w-full flex items-center space-x-3 px-4 py-3
                  text-left transition-colors
                  ${
                    selectedIndex === index
                      ? "bg-blue-500/20 text-blue-400"
                      : "text-gray-300 hover:bg-gray-700/50"
                  }
                `}
              >
                {suggestion.type === "recent" && (
                  <ClockIcon className="h-4 w-4 text-gray-500 flex-shrink-0" />
                )}
                {suggestion.type === "trending" && (
                  <ArrowTrendingUpIcon className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                )}
                {suggestion.type === "suggestion" && (
                  <MagnifyingGlassIcon className="h-4 w-4 text-gray-500 flex-shrink-0" />
                )}
                <span className="flex-1 truncate">{suggestion.text}</span>
                {suggestion.count && (
                  <span className="text-xs text-gray-500">
                    {suggestion.count}
                  </span>
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Command Palette - Spotlight-style search
export const CommandPalette = ({
  isOpen,
  onClose,
  commands = [],
  placeholder = "Type a command or search...",
}) => {
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.keywords?.some((k) => k.toLowerCase().includes(search.toLowerCase()))
  );

  const handleKeyDown = (e) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        );
        break;
      case "Enter":
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].onSelect?.();
          onClose();
        }
        break;
      case "Escape":
        onClose();
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setSearch("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: -20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -20 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* Search input */}
        <div className="flex items-center px-4 py-3 border-b border-gray-700">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-400 ml-3"
          />
          <kbd className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
            ESC
          </kbd>
        </div>

        {/* Commands list */}
        <div className="max-h-80 overflow-y-auto py-2">
          {filteredCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-400">
              No commands found
            </div>
          ) : (
            filteredCommands.map((command, index) => {
              const Icon = command.icon;
              return (
                <button
                  key={command.id || index}
                  onClick={() => {
                    command.onSelect?.();
                    onClose();
                  }}
                  className={`
                    w-full flex items-center space-x-3 px-4 py-3
                    transition-colors
                    ${
                      selectedIndex === index
                        ? "bg-blue-500/20 text-white"
                        : "text-gray-300 hover:bg-gray-800"
                    }
                  `}
                >
                  {Icon && (
                    <Icon
                      className={`h-5 w-5 ${
                        command.iconColor || "text-gray-400"
                      }`}
                    />
                  )}
                  <div className="flex-1 text-left">
                    <div className="font-medium">{command.label}</div>
                    {command.description && (
                      <div className="text-sm text-gray-400">
                        {command.description}
                      </div>
                    )}
                  </div>
                  {command.shortcut && (
                    <kbd className="px-2 py-1 bg-gray-800 rounded text-xs text-gray-400">
                      {command.shortcut}
                    </kbd>
                  )}
                </button>
              );
            })
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SearchInput;

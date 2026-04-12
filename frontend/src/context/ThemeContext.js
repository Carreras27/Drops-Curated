import React, { createContext, useContext, useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

// Theme Context
const ThemeContext = createContext(null);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('drops-curated-theme');
      if (stored) return stored;
    }
    // Default to dark mode (the hype streetwear vibe)
    return 'dark';
  });

  useEffect(() => {
    // Apply theme to document
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    
    // Persist preference
    localStorage.setItem('drops-curated-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isDark: theme === 'dark' }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Theme Toggle Button Component
export const ThemeToggle = ({ className = '' }) => {
  const { theme, toggleTheme, isDark } = useTheme();
  
  return (
    <button
      onClick={toggleTheme}
      className={`
        relative w-10 h-10 flex items-center justify-center
        rounded-full transition-all duration-300 ease-out
        bg-surface/50 backdrop-blur-sm border border-primary/10
        hover:border-accent hover:shadow-[0_0_20px_rgba(184,255,28,0.15)]
        active:scale-95
        ${className}
      `}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      data-testid="theme-toggle"
    >
      {/* Sun Icon (shown in dark mode) */}
      <Sun 
        className={`
          w-4 h-4 absolute transition-all duration-300
          ${isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-90 scale-50'}
          text-accent
        `}
        strokeWidth={2}
      />
      
      {/* Moon Icon (shown in light mode) */}
      <Moon 
        className={`
          w-4 h-4 absolute transition-all duration-300
          ${!isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-50'}
          text-primary
        `}
        strokeWidth={2}
      />
    </button>
  );
};

export default ThemeProvider;

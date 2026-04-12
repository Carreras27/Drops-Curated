/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./app/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Theme-aware colors using CSS variables
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-elevated': 'var(--color-surface-elevated)',
        primary: {
          DEFAULT: 'var(--color-primary)',
          muted: 'var(--color-primary-muted)',
          dim: 'var(--color-primary-dim)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          muted: 'var(--color-accent-muted)',
          dim: 'var(--color-accent-dim)',
        },
        foreground: 'var(--color-primary)',
        muted: 'var(--color-primary-muted)',
        border: 'var(--color-border)',
        'border-strong': 'var(--color-border-strong)',
        card: 'var(--color-card-bg)',
        stat: 'var(--color-stat-bg)',
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
      fontFamily: {
        serif: ['Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        'subtle': '0 1px 2px var(--color-shadow)',
        'soft': '0 4px 20px var(--color-shadow)',
        'lift': '0 8px 30px var(--color-shadow)',
        'glow': '0 0 20px var(--color-glow)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

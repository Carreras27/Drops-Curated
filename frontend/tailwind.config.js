/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./app/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Light mode (default)
        background: '#FFFFFF',
        foreground: '#0A0A0A',
        
        // Dark mode
        'dark-background': '#0A0A0A',
        'dark-foreground': '#FFFFFF',
        
        // Pop colors (work in both modes)
        primary: {
          DEFAULT: '#0066FF',
          hover: '#0052CC',
          light: '#3385FF',
        },
        secondary: {
          DEFAULT: '#FF0080',
          hover: '#CC0066',
          light: '#FF339D',
        },
        success: {
          DEFAULT: '#00FF85',
          hover: '#00CC6A',
          light: '#33FF9F',
        },
        warning: {
          DEFAULT: '#FF6B00',
          hover: '#CC5500',
          light: '#FF8833',
        },
        
        // Neutrals
        gray: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E5E5E5',
          300: '#D4D4D4',
          400: '#A3A3A3',
          500: '#737373',
          600: '#525252',
          700: '#404040',
          800: '#262626',
          900: '#171717',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'soft': '0 4px 12px 0 rgba(0, 0, 0, 0.08)',
        'strong': '0 8px 24px 0 rgba(0, 0, 0, 0.12)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./app/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: '#FDFBF7',
        surface: '#FFFFFF',
        primary: {
          DEFAULT: '#001F3F',
          hover: '#00152b',
        },
        accent: {
          DEFAULT: '#D4AF37',
          hover: '#b8972e',
        },
        foreground: '#001F3F',
        muted: 'rgba(0, 31, 63, 0.6)',
        border: 'rgba(0, 31, 63, 0.1)',
        success: '#16a34a',
        warning: '#ea580c',
        danger: '#dc2626',
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
        'subtle': '0 1px 2px rgba(0, 31, 63, 0.04)',
        'soft': '0 4px 20px rgba(0, 31, 63, 0.06)',
        'lift': '0 8px 30px rgba(0, 31, 63, 0.12)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        fredoka: ['Fredoka', 'sans-serif'],
        dmsans: ['DM Sans', 'sans-serif'],
      },
      colors: {
        primary: '#FF6B35',
        'primary-hover': '#E85D2A',
        secondary: '#2EC4B6',
        accent: '#FF9F1C',
        'bg-main': '#FDFFFC',
        'text-main': '#011627',
        'text-muted': '#70798C',
        'border-light': '#E6E8E6',
        'status-online': '#2EC4B6',
        'status-offline': '#E71D36',
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

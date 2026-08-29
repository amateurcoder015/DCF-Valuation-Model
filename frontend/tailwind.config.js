/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0265d6',
          700: '#034aa6',
          900: '#0c2240',
        },
        slate: {
          850: '#151e2e',
          900: '#0f172a',
          950: '#080d19',
        }
      }
    },
  },
  plugins: [],
}

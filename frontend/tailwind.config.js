/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        amber: {
          primary: '#FF6A1A',
          deep: '#C94E0A',
          subtle: '#FFF0E6',
        },
        surface: {
          black: '#050505',
          light: '#F7F7F5',
          muted: '#8A8A8A',
        },
        swiss: {
          bg: '#FFFFFF',
          fg: '#000000',
          muted: '#F7F7F5',
          accent: '#FF6A1A', // Signal Amber
          border: '#000000',
        }
      },
      fontFamily: {
        sans: ['"Helvetica Now Var"', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        blink: 'blink 1s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        }
      }
    },
  },
  plugins: [],
}

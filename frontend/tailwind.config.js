/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: '#F8F3EC',
          alt: '#F1EBE1',
        },
        ink: {
          DEFAULT: '#111010',
          pure: '#000000',
        },
        red: {
          swiss: '#DC201E',
        },
        grey: {
          furniture: '#8C8880',
        },
        hairline: {
          DEFAULT: 'rgba(17,16,16,0.16)',
          faint: 'rgba(17,16,16,0.08)',
        },
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
          bg: '#F8F3EC',
          fg: '#111010',
          muted: '#F1EBE1',
          accent: '#DC201E',
          border: '#111010',
        }
      },
      fontFamily: {
        anton: ['Anton', 'sans-serif'],
        archivo: ['Archivo', 'sans-serif'],
        sans: ['Archivo', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      letterSpacing: {
        'tight-anton': '-0.012em',
        'wide-mono': '0.26em',
      },
      lineHeight: {
        'tight-anton': '0.88',
      },
      animation: {
        blink: 'blink 1s step-end infinite',
        'ambient-hairline': 'ambientHairline 38s linear infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        ambientHairline: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100vw)' },
        }
      }
    },
  },
  plugins: [],
}

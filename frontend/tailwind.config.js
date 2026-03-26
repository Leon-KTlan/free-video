/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#fff8f0',
          100: '#ffecd0',
          200: '#ffd49a',
          300: '#ffb85a',
          400: '#ff9a20',
          500: '#ff7f00',
          600: '#e06500',
          700: '#b84d00',
          800: '#8c3a00',
          900: '#5c2500',
        },
        dark: {
          900: '#0a0e1a',
          800: '#0f1629',
          700: '#151e38',
          600: '#1c2847',
          500: '#243058',
        }
      },
      fontFamily: {
        sans: ['"Sora"', '"Noto Sans SC"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0a0e1a 0%, #0f1a35 40%, #1a0a2e 100%)',
        'card-glass': 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%)',
        'brand-gradient': 'linear-gradient(135deg, #ff7f00 0%, #ff4500 100%)',
        'gold-gradient': 'linear-gradient(135deg, #f7c948 0%, #ff8c00 50%, #ff4500 100%)',
      },
      boxShadow: {
        'glow-brand': '0 0 30px rgba(255, 127, 0, 0.3)',
        'glow-gold': '0 0 40px rgba(247, 201, 72, 0.25)',
        'card': '0 8px 32px rgba(0,0,0,0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        }
      }
    },
  },
  plugins: [],
}

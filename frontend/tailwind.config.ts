import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#102a43',
        navy: '#0b2545',
        teal: '#0f766e',
        mist: '#f5f8fb',
        line: '#d9e2ec',
      },
      boxShadow: {
        soft: '0 12px 30px rgba(16, 42, 67, 0.07)',
      },
    },
  },
  plugins: [],
} satisfies Config

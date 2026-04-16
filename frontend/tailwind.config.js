export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        contraindicated: { bg: '#fff0f0', text: '#c0392b', border: '#f5c6c6' },
        major: { bg: '#fff8f0', text: '#d35400', border: '#fad7b0' },
        moderate: { bg: '#fffbf0', text: '#b7860b', border: '#faeab0' },
        minor: { bg: '#f0f7ff', text: '#2471a3', border: '#b0d4f5' },
      },
    },
  },
  plugins: [],
}

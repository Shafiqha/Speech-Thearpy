/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom color palette
        'sky-blue': '#ADD4EB',
        'lilac': '#C4C4DE',
        'sage': '#A6BAA3',
        'forest': '#52604A',
        'slate-blue': '#59738C',
        // Additional shades
        'sky-blue-light': '#C5E3F5',
        'sky-blue-dark': '#8BB8D8',
        'lilac-light': '#D8D8E9',
        'lilac-dark': '#A9A9CE',
        'sage-light': '#BFD0BD',
        'sage-dark': '#8CA489',
        'forest-light': '#6B7D61',
        'forest-dark': '#3A4434',
        'slate-blue-light': '#7A92A9',
        'slate-blue-dark': '#405468',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'display': ['Poppins', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      animation: {
        'gradient': 'gradient 8s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' }
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-soft': 'linear-gradient(135deg, #ADD4EB 0%, #C4C4DE 100%)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

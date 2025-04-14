const { join } = require('path');

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    join(
      __dirname,
      '{src,pages,components,app}/**/*!(*.stories|*.spec).{ts,tsx,html}'
    ),
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {},
    },
  },
  plugins: [require('@tailwindcss/typography')],
};

module.exports = {
  content: [
    "../templates/**/*.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../appartment/templates/**/*.html",
  ],
  theme: {
    extend: {},
  },
  plugins: [require('daisyui')],
};

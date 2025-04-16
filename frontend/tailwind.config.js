// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class", // <== THIS LINE is required
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

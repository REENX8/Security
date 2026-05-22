/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        safe: "#22c55e",
        suspicious: "#eab308",
        phishing: "#ef4444",
      },
      fontFamily: {
        sans: ["Segoe UI", "Sarabun", "Tahoma", "sans-serif"],
      },
    },
  },
  plugins: [],
};

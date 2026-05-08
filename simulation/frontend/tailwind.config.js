/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        antimatter: {
          50: "#f0f9ff",
          400: "#00f5ff",
          500: "#00d4e8",
          900: "#020408",
        },
      },
    },
  },
  plugins: [],
};

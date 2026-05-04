/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        darkN0: "#242424",
        y50: "#FAF3EA",
        darkY50: "#090909",
        y75: "#ECCFA9",
        darkY75: "#242424",
        y100: "#E4BB85",
        y200: "#FFB323",
        y300: "#D0892D",

        b300: "#5A3301",
        darkB300: "#D0892D",
        n40: "#DFDFDF",
        darkN40: "#353535",
        n70: "#A6A6A6",
        n90: "#898989",
        n500: "#424242",
        darkN500: "#B3B3B3",
        n900: "#090909",
      },
    },
  },
  plugins: [],
};

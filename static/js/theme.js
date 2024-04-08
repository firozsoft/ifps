'use strict';

// Function to detect system theme preference
const detectSystemTheme = () => {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

// Function to apply the theme based on system preference or saved preference
(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.documentElement.dataset.mdbTheme = savedTheme;
  } else {
    // Detect system-wide theme for the first time
    const systemTheme = detectSystemTheme();
    document.documentElement.dataset.mdbTheme = systemTheme;
    // Save system-wide theme preference
    localStorage.setItem('theme', systemTheme);
  }
})();

// Function to toggle theme
const toggleTheme = (isChecked) => {
  const theme = isChecked ? "dark" : "light";
  document.documentElement.dataset.mdbTheme = theme;
  // Save selected theme to local storage
  localStorage.setItem('theme', theme);
};

document.addEventListener("DOMContentLoaded", function () {
  const themeSwitcher = document.getElementById("themingSwitcher");

  // set toggler position based on system theme
  themeSwitcher.checked = document.documentElement.dataset.mdbTheme === "dark";

  // add listener to theme toggler
  themeSwitcher.addEventListener("change", (e) => {
    toggleTheme(e.target.checked);
  });
});
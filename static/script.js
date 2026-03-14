document.addEventListener("DOMContentLoaded", function () {
    initializeTheme();
    initializeTextareaCounter();
});

function initializeTheme() {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);

    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
        updateThemeButton(themeToggle, savedTheme);

        themeToggle.addEventListener("click", function () {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";

            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            updateThemeButton(themeToggle, newTheme);
        });
    }
}

function updateThemeButton(button, theme) {
    if (theme === "dark") {
        button.textContent = "Light Mode";
    } else {
        button.textContent = "Dark Mode";
    }
}

function initializeTextareaCounter() {
    const textarea = document.getElementById("newsInput");
    const counter = document.getElementById("charCount");

    if (textarea && counter) {
        const updateCount = () => {
            counter.textContent = textarea.value.length + " chars";
        };

        textarea.addEventListener("input", updateCount);
        updateCount();
    }
}
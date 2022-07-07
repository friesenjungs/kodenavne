const toggleTheme = () => {
	const body = document.getElementById("idBody");
	body.classList.toggle('bg-dark');
	body.classList.toggle('text-light');
	document.getElementById("idTheme").classList.toggle('bi-sun');
	localStorage.setItem("theme", body.classList.contains("bg-dark") ? "dark" : "light");
}

const saveSettings = () => {
	localStorage.setItem("username", document.getElementById("idUsernameInput").value);
	localStorage.setItem("language", document.getElementById("idLanguageSelect").value);
	sendUsername();
}

document.addEventListener("DOMContentLoaded", () => {
	document.getElementById("idToggleThemeBtn").addEventListener("click", toggleTheme);
	document.getElementById("idSettingsForm").addEventListener("submit", saveSettings);
	if (localStorage.getItem("theme") === "light") toggleTheme();
	const username = localStorage.getItem("username");
	const language = localStorage.getItem("language");
	if (username) document.getElementById("idUsernameInput").value = username;
	if (language) document.getElementById("idLanguageSelect").value = language;
});

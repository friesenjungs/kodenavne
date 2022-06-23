const joinRoom = () => {
    const code = document.getElementById("idCodeInput").value;
    if(code) window.open(`/room/${code}`, "_self");
}

const toggleTheme = () => {
    const body = document.getElementById("idBody");
    body.classList.toggle('bg-dark');
    body.classList.toggle('text-light');
    document.getElementById("idTheme").classList.toggle('bi-sun');
    localStorage.setItem("theme", body.classList.contains("bg-dark") ? "dark" : "light");  
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("idJoinRoomBtn").addEventListener("click", joinRoom);
    document.getElementById("idToggleThemeBtn").addEventListener("click", toggleTheme);
    if(localStorage.getItem("theme") == "light") toggleTheme();
});

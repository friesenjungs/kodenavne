joinRoom = () => {
    const code = document.getElementById("idCodeInput").value;
    if(code) window.open(`/room/${code}`, "_self");
}

toggleTheme = () => {
    document.getElementById("idBody").classList.toggle('bg-dark');
    document.getElementById("idBody").classList.toggle('text-light');
    document.getElementById("idTheme").classList.toggle('bi-sun')
}

document.addEventListener("DOMContentLoaded", function(){
    document.getElementById("idJoinRoomBtn").addEventListener("click", joinRoom)
    document.getElementById("idToggleThemeBtn").addEventListener("click", toggleTheme)
});

const createRoom = () => {
    localStorage.setItem("username", document.getElementById("idUsernameInput").value);
    localStorage.setItem("language", document.getElementById("idLanguageSelect").value);
}

document.addEventListener("DOMContentLoaded", () => {
    const usernameInput = document.getElementById("idUsernameInput");
    const languageSelect = document.getElementById("idLanguageSelect");    
    const username = localStorage.getItem("username");
    const language = localStorage.getItem("language");
    if(username) usernameInput.value = username;
    if(language) languageSelect.value = language;

    document.getElementById("idCreateRoomBtn").addEventListener("click", createRoom);
});
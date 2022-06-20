document.addEventListener("DOMContentLoaded", function(){
    this.usernameInput = document.getElementById("idUsernameInput");
    this.languageSelect = document.getElementById("idLanguageSelect");
    var username = localStorage.getItem("username");
    var language = localStorage.getItem("language");
    username ? this.usernameInput.value = username : console.log("no local username");
    language ? this.languageSelect.value = language : console.log("no local language");
});

function createRoom(){
    localStorage.setItem("username", this.usernameInput.value);
    localStorage.setItem("language", this.languageSelect.value);
}

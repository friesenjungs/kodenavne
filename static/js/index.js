document.addEventListener("DOMContentLoaded", function(){
    this.floatingUsername = document.getElementById("floatingUsername");
    this.floatingLanguage = document.getElementById("floatingLanguage");
    var username = localStorage.getItem("username");
    var language = localStorage.getItem("language");
    username ? floatingUsername.value = username : console.log("no local username");
    language ? floatingLanguage.value = language : console.log("no local language");
});

function createRoom(){
    localStorage.setItem("username", this.floatingUsername.value);
    localStorage.setItem("language", this.floatingLanguage.value);
}
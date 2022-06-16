function joinRoom(){
    let code = document.getElementById("idCodeInput").value;
    code ? window.open("/room/" + code, "_self") : console.log("no code entered");
}
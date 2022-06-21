function joinRoom(){
    let code = document.getElementById("idCodeInput").value;
    code ? window.open("/room/" + code, "_self") : console.log("no code entered");
}

function toggleTheme(){
    console.log("Toggle");
    document.getElementById("idBody").classList.toggle('bg-dark');
    document.getElementById("idBody").classList.toggle('text-light');
    document.getElementById("idTheme").classList.toggle('bi-sun')
}
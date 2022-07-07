window.onload = () => {
    const namespace = '/';
    const socket = io(namespace);

    socket.on('connect', () => {
        const room_code = window.location.href.split("/").pop()
        socket.emit('join', {'room_code': room_code});
    });

    socket.on('server message', data => {
        //example: console.log(data);
    })

    const div = document.createElement("div");
    div.setAttribute("class", "col");

    const input = document.createElement("input");
    input.setAttribute("size", "20");

    const button = document.createElement("a");
    button.setAttribute("class", "btn btn-outline-primary");
    const text = document.createTextNode("Send text to server!");
    button.appendChild(text);

    div.appendChild(input);
    div.appendChild(button);

    document.body.appendChild(div);

    button.onclick = () => {
        socket.emit('client message', {'message': 'Button was clicked'});
        socket.emit('set username', {'username': input.value});
    }
}
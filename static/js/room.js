const namespace = '/';
let socket;

const wordPressed = (e) => {
	//e.srcElement.classList.toggle('border')
}

const startGame = () => {
	const size = document.getElementById("idSizeSelect").value;
	document.getElementById("idGameSettings").remove();
	createBoard(size, size);
}

const createBoard = (columns, rows) => {
	const gameBoard = document.getElementById("idGameBoard");
	for (let i = 0; i < rows; i++) {
		const div = document.createElement("div");
		div.setAttribute("class", "d-flex flex-row h-100 justify-content-between flex-grow-1 text-align-center");
		for (let j = 0; j < columns; j++) {
			const a = document.createElement("a");
			a.setAttribute("class", "d-flex btn border w-100 fw-bold m-1 align-items-center justify-content-center flex-grow-1");
			a.setAttribute("style", "color: inherit");
			a.addEventListener("click", wordPressed)
			a.appendChild(document.createTextNode("Word " + (i * rows + j + 1)));
			div.appendChild(a);
		}
		gameBoard.appendChild(div);
	}
}

const sendUsername = () => {
	if (localStorage.getItem("username")) {
		if (socket.connected) {
			socket.emit('set username', { 'username': localStorage.getItem("username") });
		}
	}
}

document.addEventListener("DOMContentLoaded", () => {
	document.getElementById("idStartGameBtn").addEventListener("click", startGame);
});

window.onload = () => {

	socket = io(namespace);

	socket.on('connect', () => {
		const room_code = window.location.href.split("/").pop();
		socket.emit('join', { 'room_code': room_code });
		sendUsername();
	});

	socket.on('server message', data => {
		//example: console.log(data);
	})

	// const div = document.createElement("div");
	// div.setAttribute("class", "col");

	// const input = document.createElement("input");
	// input.setAttribute("size", "20");

	// const button = document.createElement("a");
	// button.setAttribute("class", "btn btn-outline-primary");
	// const text = document.createTextNode("Send text to server!");
	// button.appendChild(text);

	// div.appendChild(input);
	// div.appendChild(button);

	// document.body.appendChild(div);

	// button.onclick = () => {
	//     socket.emit('client message', {'message': 'Button was clicked'});
	//     socket.emit('set username', {'username': input.value});
	// }
}
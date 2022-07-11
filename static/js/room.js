const namespace = '/';
let socket;

// styling for word cards
const getStyle = {
	0: 'background-color: inherit; border-color: inherit !important; border-width: medium !important; color: inherit !important', // unknown
	1: 'background-color: #0d6efd !important; border-color: black !important; border-width: medium !important; color: white',	// team 1
	2: 'background-color: #dc3545; border-color: inherit !important; border-width: medium !important; color: white', // team 2
	3: 'background-color: #198754; border-color: inherit !important; border-width: medium !important; color: white', // team 3
	4: 'background-color: #ffc107; border-color: inherit !important; border-width: medium !important; color: white', // team 4
	5: 'background-color: white; border-color: inherit !important; border-width: medium !important; color: black', // neutral card
	6: 'background-color: black; border-color: white !important; border-width: medium !important; color: white' // balck card
}

// show Bootstrap Toast to communicate with user
const showToast = (title, message, icon, time) => {
	console.log(`${title}: ${message} ${time}`);
	const toast = document.getElementById('idToast');
	if (title) document.getElementById("idToastHeader").childNodes[0].nodeValue = title;
	if (message) document.getElementById("idToastMessage").childNodes[0].nodeValue = message;
	if (time) document.getElementById("idToastTime").childNodes[0].nodeValue = time;
	if (icon) document.getElementById("idToastIcon").classList.add(icon);
	const newToast = new bootstrap.Toast(toast);
	newToast.show();
}

// send settings to server
const sendSettings = (size, lang) => {
	// send 'set setting' event with board_size and game language to server
	socket.emit('set setting', { 'board_size': { 'x': parseInt(size[0], 10), 'y': parseInt(size[1], 10) }, lang });
}

// called when settings change
const changedSettings = () => {

	// get game size and game language
	const size = document.getElementById("idSizeSelect").value.split('x');
	const lang = document.getElementById("idGameLanguageSelect").value;

	// send changes to server
	sendSettings(size, lang);
}

// called when a user wants to join a team with role
const joinTeam = (e) => {

	const btn = e.srcElement;
	const data = btn.previousElementSibling.id; // z.B. idSpymaster2
	const team = parseInt(data.slice(-1), 10);
	const role = data.slice(2, -1);

	// send 'set team' event with team and role to server
	socket.emit('set team', { team, role });
}

// called when admin starts the game
const startGame = () => {

	// send 'start game' event so server
	socket.emit('start game');

	// to be deleted
	//const size = document.getElementById("idSizeSelect").value.split('x');
	//document.getElementById("idGameSettings").remove();
	//createBoard(size[0], size[1]);
	//
}

// called when user clicks a word
const wordPressed = (e) => {
	e.srcElement.classList.toggle('border');// border-style toogles between solid and dashed
}

// called when Spymaster sends clue
const performSpymasterAction = () => {

	// get clue and cluenumber
	const clue = document.getElementById("idClueInput").value;
	const cluenumber = document.getElementById("idClueNumberInput").value;

	// send 'performed spymaster action' event with clue and cluenumber to server
	socket.emit('performed spymaster action', { 'hint': clue, 'amount': cluenumber }, (response) => {
		if (response) {
			document.getElementById("idClueBtn").classList.add('visually-hidden');
		}
	});

	// to be deleted
	document.getElementById("idClueBtn").classList.add('visually-hidden');
	//
}

const performOperativeAction = (e) => {
	e.preventDefault();
	socket.emit('performed operative action', { 'id': e.srcElement.id });
}

// add EventListener when DOM ist loaded
document.addEventListener('DOMContentLoaded', () => {

	document.getElementById("idSizeSelect").addEventListener('change', changedSettings);
	document.getElementById("idGameLanguageSelect").addEventListener('change', changedSettings);
	document.querySelectorAll("#idButtonTeam").forEach(btn => {
		btn.addEventListener('click', joinTeam);
	});
	document.getElementById("idStartGameBtn").addEventListener('click', startGame);
	document.getElementById("idClueForm").addEventListener('submit', performSpymasterAction);
});

// send Username to Server
const setUsername = () => {

	// only if there is a username in local storage
	if (localStorage.getItem('username')) {

		// only if user ist connected to server
		if (socket.connected) {

			// send 'set username' event with username to server
			socket.emit('set username', { 'username': localStorage.getItem('username') });
		}
	}
}

const showPlayers = (players) => {

	// for each button to join a team
	document.querySelectorAll("#idButtonTeam").forEach(btn => {

		const data = btn.previousElementSibling.id; // z.B. idSpymaster2
		const team = parseInt(data.slice(-1), 10);
		const role = data.slice(2, -1);

		// find entry for this player in players
		const player = players.filter(element => (element.role === role && element.team === team));

		// if entry exists show player else show button
		if (player.length === 1) {
			btn.previousSibling.nodeValue = player[0].name;
			btn.classList.add('visually-hidden');
		} else {
			btn.previousSibling.nodeValue = '';
			btn.classList.remove('visually-hidden');
		}
	});
}

// update game board
const updateBoard = (words) => {

	words.forEach(word => {
		const btn = document.getElementById(word.id);
		// set style for word card
		if (word.team != undefined) btn.setAttribute('style', `${getStyle[word.team]}`);
		// set text
		if (word.text) btn.childNodes[0].nodeValue = word.text;
	});
}

// create game board
const createBoard = (columns, rows) => {
	const gameBoard = document.getElementById('idGameBoard');
	for (let i = 0; i < rows; i++) {
		const div = document.createElement('div');
		div.setAttribute('class', 'd-flex flex-row h-100 justify-content-between flex-grow-1 text-align-center');
		for (let j = 0; j < columns; j++) {
			const newWord = document.createElement("a");
			newWord.setAttribute('id', `${i * rows + j}`)
			newWord.setAttribute('class', 'd-flex btn border myborder w-100 fw-bold m-1 align-items-center justify-content-center text-break');
			newWord.setAttribute('style', 'color: inherit;');
			newWord.appendChild(document.createTextNode(''));
			newWord.addEventListener('click', wordPressed);
			newWord.addEventListener('contextmenu', performOperativeAction);
			div.appendChild(newWord);
		}
		gameBoard.appendChild(div);
	}
}

window.onload = () => {

	socket = io(namespace);

	// set client language as game language default
	if (localStorage.getItem('language')) {
		document.getElementById("idGameLanguageSelect").value = localStorage.getItem('language');
		document.getElementById("idGameLanguageSelect").dispatchEvent(new Event('change'));
	}

	socket.on('connect', () => {
		const room_code = window.location.href.split('/').pop();
		socket.emit('join', { room_code });
		setUsername();
	});

	socket.on('disconnect', () => {
		//console.log('disconnected');
	});

	socket.on('show toast', (data) => {
		showToast(data.title, data.message, data.icon, data.time);
	});

	socket.on('show settings', settings => {
		document.getElementById("idSizeSelect").value = `${settings.board_size.x}x${settings.board_size.y}`;
		document.getElementById("idGameLanguageSelect").value = settings.lang;
	});

	socket.on('show players', players => {
		showPlayers(players);
	});

	socket.on('start game', (data) => {
		document.getElementById("idGameSettings").remove();
		createBoard(data.board_size.x, data.board_size.y);
	});

	socket.on('show cards', data => {
		updateBoard(data);
	});

	socket.on('show spymaster hint', data => {
		console.log(data); //tbd
	});

	socket.on('perform operative action', data => {
		console.log(data); //tbd
	});

	socket.on('perform spymaster action', () => {
		document.getElementById("idClueBtn").classList.remove('visually-hidden');
	});

	socket.on('end game', data => {
		console.log(data); //tbd
	});
}
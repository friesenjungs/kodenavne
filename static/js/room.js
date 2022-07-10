const namespace = '/';
let socket;

// styling for word cards
const getStyle = {
	0: 'border-color: inherit !important', // unknown
	1: 'border-color: blue !important',	// team 1
	2: 'border-color: red !important', // team 2
	3: 'border-color: green !important', // team 3
	4: 'border-color: yellow !important', // team 4
	5: 'border-color: inherit !important', // neutral card
	6: 'border-color: white !important; background-color: black; color: white' // balck card
}

// dummy data
const words = [
	{ "id": 0, "text": "ROULETTE", "team": 0 },
	{ "id": 1, "text": "DRACHE", "team": 1 },
	{ "id": 2, "text": "KRIEG", "team": 2 },
	{ "id": 3, "text": "HONIG", "team": 3 },
	{ "id": 4, "text": "BOMBE", "team": 4 },
	{ "id": 5, "text": "KASINO", "team": 6 },
	{ "id": 6, "text": "WOLKENKRATZER", "team": 0 },
	{ "id": 7, "text": "SATURN", "team": 1 },
	{ "id": 8, "text": "ALIEN", "team": 2 },
	{ "id": 9, "text": "PEITSCHE", "team": 3 },
	{ "id": 10, "text": "ANTARKTIS", "team": 0 },
	{ "id": 11, "text": "SCHNEEMANN", "team": 4 },
	{ "id": 12, "text": "KONZERT", "team": 0 },
	{ "id": 13, "text": "SCHOKOLADE", "team": 1 },
	{ "id": 14, "text": "JET", "team": 0 },
	{ "id": 15, "text": "DINOSAURIER", "team": 2 },
	{ "id": 16, "text": "PIRAT", "team": 0 },
	{ "id": 17, "text": "HUPE", "team": 3 },
	{ "id": 18, "text": "PINGUIN", "team": 4 },
	{ "id": 19, "text": "SPINNE", "team": 0 },
];
// 

// show Bootstrap Toast to communicate with user
const showToast = (title, message, time) => {
	//console.log(`${title}: ${message} ${time}`);
}

// called when settings change
const changedSettings = () => {

	// get game size and game language
	const size = document.getElementById("idSizeSelect").value.split('x');
	const lang = document.getElementById("idGameLanguageSelect").value;

	// send changes to server
	sendSettings(size, lang);
}

// send settings to server
const sendSettings = (size, lang) => {
	// send 'set setting' event with board_size and game language to server
	socket.emit('set setting', { 'board_size': { 'x': parseInt(size[0]), 'y': parseInt(size[1]) }, 'lang': lang }, (response) => {
	});
}

// called when a user wants to join a team with role
const joinTeam = (e) => {

	const btn = e.srcElement;
	const data = btn.previousElementSibling.id; // z.B. idSpymaster2
	const team = parseInt(data.slice(-1));
	const role = data.slice(2, -1);

	// to be deleted
	btn.previousSibling.nodeValue = localStorage.getItem('username');
	btn.classList.add('visually-hidden');
	//

	// send 'set team' event with team and role to server
	socket.emit('set team', { 'team': team, role: role }, (response) => {
		if (response) {
			btn.previousSibling.nodeValue = localStorage.getItem('username');
			btn.classList.add('visually-hidden');
		}
	});
}

// called when admin starts the game
const startGame = () => {

	// send 'start game' event so server
	socket.emit('start game', (response) => {
	});

	// to be deleted
	const size = document.getElementById("idSizeSelect").value.split('x');
	document.getElementById("idGameSettings").remove();
	createBoard(size[0], size[1]);
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
			socket.emit('set username', { 'username': localStorage.getItem('username') }, (response) => {
			});
		}
	}
}

const showPlayers = (data) => {

	//dummy data
	const players = [
		{ "name": "julian", "role": "Operative", "team": 1 },
		{ "name": "3 backflip", "role": "Spymaster", "team": 2 }
	];
	//

	// for each button to join a team
	document.querySelectorAll("#idButtonTeam").forEach(btn => {

		const data = btn.previousElementSibling.id; // z.B. idSpymaster2
		const team = parseInt(data.slice(-1));
		const role = data.slice(2, -1);

		// find entry for this player in players
		const player = players.filter(player => (player.role == role && player.team == team));

		// if entry exists show player else show button
		if(player.length == 1){
			btn.previousSibling.nodeValue = player[0].name;
			btn.classList.add('visually-hidden');
		}else{
			btn.previousSibling.nodeValue = '';
			btn.classList.remove('visually-hidden');
		}
	});
}

// update game board
const updateBoard = (words) => {

	words.forEach(word => {
		btn = document.getElementById(word.id);
		// set style for word card
		if(word.team) btn.setAttribute('style', `color: inherit; ${getStyle[word.team]}`);
		// set text
		if(word.text) btn.childNodes[0].nodeValue = word.text;
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
			newWord.setAttribute('class', 'd-flex btn border border-2 myborder w-100 fw-bold m-1 align-items-center justify-content-center text-break');
			newWord.setAttribute('style', 'color: inherit; border-color: white !important');
			newWord.appendChild(document.createTextNode(''));
			newWord.addEventListener('click', wordPressed);
			div.appendChild(newWord);
		}
		gameBoard.appendChild(div);
	}
	updateBoard(words);
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
	})

	socket.on('server message', data => {
		//console.log(data);
	});

	socket.on('show settings', settings => {
		document.getElementById("idSizeSelect").value = `${settings.board_size.x}x${settings.board_size.y}`;
		document.getElementById("idGameLanguageSelect").value = settings.lang;
	});

	socket.on('show players', data => {
		showPlayers(data);
	});

	socket.on('start game', data => {
		document.getElementById("idGameSettings").remove();
		createBoard(8, 8);
	});

	socket.on('show cards', data => {
		updateBoard(data);
	});

	socket.on('show spymaster hint', data => {
		//console.log(data); //tbd
	});

	socket.on('perform operative action', data => {
		//console.log(data); //tbd
	});

	socket.on('perform spymaster action', data => {
		document.getElementById("idClueBtn").classList.remove('visually-hidden');
	});

	socket.on('end game', data => {
		//console.log(data); //tbd
	});
}
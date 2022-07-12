const namespace = '/';
let socket;

const icons =  {
	'info': 'bi-info-square-fill',
	'warning': 'bi-exclamation-octagon-fill',
	'error': 'bi-x-octagon-fill'
}

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
const showToast = (title, message, icon, subtitle) => {
	const toast =
		`<div id="idToast" class="toast bg-light" role="alert" aria-live="assertive" aria-atomic="true">
		<div class="toast-header">
			<i id="idToastIcon" class="bi ${icon} me-2"></i>
			<strong id="idToastHeader" class="me-auto">${title}</strong>
			<small id="idToastTime">${subtitle}</small>
			<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
		</div>
		<div id="idToastMessage" class="toast-body">${message}</div>
	</div>`
	document.getElementById("idToastContainer").insertAdjacentHTML('beforeend', toast);
	const newToast = new bootstrap.Toast(document.getElementById("idToastContainer").lastElementChild);
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

	// get team and role of button
	const data = e.target.previousElementSibling.id; // z.B. idSpymaster2
	const team = parseInt(data.slice(-1), 10);
	const role = data.slice(2, -1);

	// send 'set team' event with team and role to server
	socket.emit('set team', { team, role });
}

// called when start game button is clicked
const startGame = () => {
	// send 'start game' event so server
	socket.emit('start game');
}

// called when word card is left-clicked
const wordPressed = (e) => {
	// toogle border-style between solid and dashed
	e.target.classList.toggle('border');
}

// called when Spymaster sends clue
const performSpymasterAction = () => {

	// get clue and cluenumber
	const clue = document.getElementById("idClueInput").value;
	const cluenumber = parseInt(document.getElementById("idClueNumberInput").value);

	// send 'performed spymaster action' event with clue and cluenumber to server
	socket.emit('performed spymaster action', { 'hint': clue, 'amount': cluenumber }, (response) => {
		if (response) {
			document.getElementById("idClueBtn").classList.add('visually-hidden');
		}
	});
}

// called when word card is right-clicked
const performOperativeAction = (e) => {

	// prevent contextMenu
	e.preventDefault();

	// send 'performed operative action' event with id of word card so server
	socket.emit('performed operative action', { 'id': e.target.id }, (response) => {
		if(response.endturn){
			document.getElementById("idEndTurnBtn").classList.add('visually-hidden');
		}
	});
}

// called when end turn button is clicked
const endTurn = () => {

	// send performed operative action event to server
	socket.emit('performed operative action', { 'id': -1 }, (response) => {
		if (response.successfull) {
			// hide end turn button
			document.getElementById("idEndTurn").classList.add('visually-hidden');
		}
	});
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
	document.getElementById("idEndTurnBtn").addEventListener('click', endTurn);
});

// send Username to Server
const setUsername = () => {

	// only if there is a username in local storage and user ist connected to server
	if (localStorage.getItem('username') && socket.connected) {

		// send 'set username' event with username to server
		socket.emit('set username', { 'username': localStorage.getItem('username') }, (response) => {
			if(!response) showToast('Error', 'Could not set username', icons['warning'], 'now');
		});
	}
}

// show all Players 
const showPlayers = (players) => {

	// for each button to join a team
	document.querySelectorAll("#idButtonTeam").forEach(btn => {

		// get team and role of this button
		const data = btn.previousElementSibling.id; // z.B. idSpymaster2
		const team = parseInt(data.slice(-1), 10);
		const role = data.slice(2, -1);

		// find entry of corresponding player in players
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

	// saving player team and role in local storage
	const me = players.filter(player => (player.me))[0];
	console.log(me)
	localStorage.setItem('team', me.team);
	localStorage.setItem('role', me.role);
}

// update game board
const updateBoard = (words) => {

	// for each word
	words.forEach(word => {
		const btn = document.getElementById(word.id);
		// set style of word card
		if (word.team != undefined) btn.setAttribute('style', `${getStyle[word.team]}`);
		// set text of word card
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
			//newWord.setAttribute('style', 'color: inherit;');
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

	socket.on('show game status', (data) => {
		document.getElementById("idGameStatusMessage").firstChild.nodeValue = data.message;
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
		document.getElementById("idGameStatus").classList.remove('visually-hidden')
		createBoard(data.board_size.x, data.board_size.y);
	});

	socket.on('show cards', cards => {
		updateBoard(cards);
	});

	socket.on('perform spymaster action', () => {
		document.getElementById("idClueBtn").classList.remove('visually-hidden');
		document.getElementById("idClueInput").value = "";
		document.getElementById("idClueNumberInput").value = "";
	});

	socket.on('perform operative action', () => {
		document.getElementById("idEndTurnBtn").classList.remove('visually-hidden');
	});

	socket.on('end game', data => {
		console.log(data);
	});
}
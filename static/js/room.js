const namespace = '/';
let socket;

const icons = {
	info: 'bi-info-square-fill',
	warning: 'bi-exclamation-octagon-fill',
	error: 'bi-x-octagon-fill'
}

const getWordStyle = {
	0: 'teamunknwon',
	1: 'teamblue',
	2: 'teamred',
	3: 'teamgreen',
	4: 'teamorange',
	5: 'teamneutral',
	6: 'teamblack'
}

const particle = {
	'emitters': {
		'position': {
			'x': 50,
			'y': 100
		},
		'rate': {
			'quantity': 5,
			'delay': 0.15
		}
	},
	'particles': {
		'color': {
			'value': [
				'#1E00FF',
				'#FF0061',
				'#E1FF00',
				'#00FF9E'
			]
		},
		'move': {
			'decay': 0.05,
			'direction': 'top',
			'enable': true,
			'gravity': {
				'enable': true
			},
			'outModes': {
				'top': 'none',
				'default': 'destroy'
			},
			'speed': {
				'min': 75,
				'max': 150
			}
		},
		'number': {
			'value': 0
		},
		'opacity': {
			'value': 1
		},
		'rotate': {
			'value': {
				'min': 0,
				'max': 360
			},
			'direction': 'random',
			'animation': {
				'enable': true,
				'speed': 30
			}
		},
		'tilt': {
			'direction': 'random',
			'enable': true,
			'value': {
				'min': 0,
				'max': 360
			},
			'animation': {
				'enable': true,
				'speed': 30
			}
		},
		'size': {
			'value': 3,
			'animation': {
				'enable': true,
				'startValue': 'min',
				'count': 1,
				'speed': 16,
				'sync': true
			}
		},
		'roll': {
			'darken': {
				'enable': true,
				'value': 25
			},
			'enlighten': {
				'enable': true,
				'value': 25
			},
			'enable': true,
			'speed': {
				'min': 5,
				'max': 15
			}
		},
		'wobble': {
			'distance': 30,
			'enable': true,
			'speed': {
				'min': -7,
				'max': 7
			}
		},
		'shape': {
			'type': [
				'circle',
				'square',
				'triangle',
				'polygon'
			],
			'options': {
				'polygon': [
					{
						'sides': 5
					},
					{
						'sides': 6
					}
				]
			}
		}
	}
}

// show Bootstrap Toast to communicate with user
const showToast = (title, message, icon, subtitle) => {
	const toast =
		`<div id='idToast' class='toast bg-light' role='alert' aria-live='assertive' aria-atomic='true'>
		<div class='toast-header'>
			<i id='idToastIcon' class='bi ${icon} me-2'></i>
			<strong id='idToastHeader' class='me-auto'>${title}</strong>
			<small id='idToastTime'>${subtitle}</small>
			<button type='button' class='btn-close' data-bs-dismiss='toast' aria-label='Close'></button>
		</div>
		<div id='idToastMessage' class='toast-body'>${message}</div>
	</div>`
	document.querySelector('#idToastContainer').insertAdjacentHTML('beforeend', toast);
	const newToast = new bootstrap.Toast(document.querySelector('#idToastContainer').lastElementChild);
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
	const size = document.querySelector('#idSizeSelect').value.split('x');
	const lang = document.querySelector('#idGameLanguageSelect').value;

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
	e.target.classList.toggle('dashedborder');
}

// called when Spymaster sends clue
const performSpymasterAction = () => {

	// get clue and cluenumber
	const clue = document.querySelector('#idClueInput').value;
	const cluenumber = parseInt(document.querySelector('#idClueNumberInput').value, 10);

	// send 'performed spymaster action' event with clue and cluenumber to server
	socket.emit('performed spymaster action', { 'hint': clue, 'amount': cluenumber }, (response) => {
		if (response) {
			document.querySelector('#idClueBtn').classList.add('visually-hidden');
		}
	});
}

// called when word card is right-clicked
const performOperativeAction = (e) => {

	// prevent contextMenu
	e.preventDefault();

	// send 'performed operative action' event with id of word card so server
	socket.emit('performed operative action', { 'id': e.target.id.replace('idWord', '') }, (successfull, endturn) => {
		if (endturn) {
			document.querySelector('#idEndTurnBtn').classList.add('visually-hidden');
		}
	});
}

// called when end turn button is clicked
const endTurn = () => {

	// send performed operative action event to server
	socket.emit('performed operative action', { 'id': -1 }, (successfull, endturn) => {
		if (endturn) {
			// hide end turn button
			document.querySelector('#idEndTurnBtn').classList.add('visually-hidden');
		}
	});
}

// add EventListener when DOM ist loaded
document.addEventListener('DOMContentLoaded', () => {

	document.querySelector('#idSizeSelect').addEventListener('change', changedSettings);
	document.querySelector('#idGameLanguageSelect').addEventListener('change', changedSettings);
	document.querySelectorAll('.teambtn').forEach(btn => {
		btn.addEventListener('click', joinTeam);
	});
	document.querySelector('#idStartGameBtn').addEventListener('click', startGame);
	document.querySelector('#idClueForm').addEventListener('submit', performSpymasterAction);
	document.querySelector('#idEndTurnBtn').addEventListener('click', endTurn);
});

// send Username to Server
const setUsername = () => {

	// only if there is a username in local storage and user ist connected to server
	if (localStorage.getItem('username') && socket.connected) {

		// send 'set username' event with username to server
		socket.emit('set username', { 'username': localStorage.getItem('username') }, (response) => {
			if (!response) showToast('Error', 'Could not set username', icons.warning, 'now');
		});
	}
}

// show all Players 
const showPlayers = (players) => {

	// for each button to join a team
	document.querySelectorAll('.teambtn').forEach(btn => {

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
}

// update game board
const updateBoard = (words) => {
	// for each word
	words.forEach(word => {
		const btn = document.querySelector(`#idWord${word.id}`);
		// set style of word card
		if (typeof word.team !== 'undefined') {
			if (!word.turned) {
				btn.classList.add(`${getWordStyle[word.team]}`);
			} else {
				btn.classList.remove(`${getWordStyle[word.team]}`);
				btn.classList.add(`turned${getWordStyle[word.team]}`);
			}
		}
		// set text of word card
		if (word.text) btn.childNodes[0].nodeValue = word.text;
	});
}

// create game board
const createBoard = (columns, rows) => {
	const gameBoard = document.querySelector('#idGameBoard');
	for (let i = 0; i < rows; i++) {
		const div = document.createElement('div');
		div.setAttribute('class', 'd-flex flex-row h-100 justify-content-between flex-grow-1 text-align-center');
		for (let j = 0; j < columns; j++) {
			const newWord = document.createElement('div');
			newWord.setAttribute('id', `idWord${i * columns + j}`)
			newWord.setAttribute('class', 'd-flex wordborder roundedBorder w-100 fw-bold m-1 align-items-center justify-content-center text-break');
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
		document.querySelector('#idGameLanguageSelect').value = localStorage.getItem('language');
		document.querySelector('#idGameLanguageSelect').dispatchEvent(new Event('change'));
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
		showToast(data.title, data.message, data.icon, data.subtitle);
	});

	socket.on('show game status', (data) => {
		document.querySelector('#idGameStatusMessage').firstChild.nodeValue = data.message;
	});

	socket.on('show settings', settings => {
		document.querySelector('#idSizeSelect').value = `${settings.board_size.x}x${settings.board_size.y}`;
		document.querySelector('#idGameLanguageSelect').value = settings.lang;
	});

	socket.on('show players', players => {
		showPlayers(players);
	});

	socket.on('start game', (data) => {
		document.querySelector('#idGameSettings').remove();
		document.querySelector('#idGameStatus').classList.remove('visually-hidden')
		createBoard(data.board_size.x, data.board_size.y);
	});

	socket.on('show cards', cards => {
		updateBoard(cards);
	});

	socket.on('perform spymaster action', () => {
		document.querySelector('#idClueBtn').classList.remove('visually-hidden');
		document.querySelector('#idClueInput').value = '';
		document.querySelector('#idClueNumberInput').value = '';
	});

	socket.on('perform operative action', () => {
		document.querySelector('#idEndTurnBtn').classList.remove('visually-hidden');
	});

	socket.on('end game', data => {
		if (data.winner_team) {
			document.querySelector('#idGameStatusMessage').firstChild.nodeValue = `Team ${data.winner_team} won the game!`;
		} else if (data.looser_team) {
			document.querySelector('#idGameStatusMessage').firstChild.nodeValue = `Team ${data.looser_team} lost the game!`;
		}
		tsParticles.load('tsparticles', particle);
	});
}
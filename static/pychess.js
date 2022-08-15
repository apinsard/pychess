function escapeHtml(unsafe) {
    return unsafe
         .replaceAll('&', "&amp;")
         .replaceAll('<', "&lt;")
         .replaceAll('>', "&gt;")
         .replaceAll('"', "&quot;")
         .replaceAll("'", "&#039;");
}

class Position {

  constructor(game, board) {
    this.game = game;
    this.board = board;
    this.update();
  }

  update() {
    const self = this;
    const fen = this.game.fen();
    fetch(`/api/position/fen/${fen}`)
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      self.id = data.id;
      self.setMoves(data.moves);
    });
    this.board.position(fen);
  }

  setMoves(moves) {
    this.moves = moves;
    let list = '<dl>';
    let tabIndex = 1;
    for (const [k, v] of Object.entries(moves)) {
      const comment = (v.comment || '').split('\n').map(escapeHtml).join('<br>');
      let moveClass = 'unrated-move';
      if ('rate' in v) {
        if (v.rate > 0)
          moveClass = 'best-move';
        else if (v.rate < 0)
          moveClass = 'mistake-move';
        else
          moveClass = 'playable-move';
      }
      list += `<dt><span tabindex="${tabIndex}" class="move ${moveClass}">${k}</span></dt><dd>${comment}</dd>`;
      tabIndex++;
    }
    list += '</dl>';
    document.getElementById('moves').innerHTML = list;
    const firstMove = document.querySelector('.move');
    if (firstMove)
      firstMove.focus();
    else
      document.activeElement.blur();
  }

  addMove(move, rate=null, comment="") {
    const self = this;
    const moves = this.moves;
    moves[move] = {};
    if (rate !== null)
      moves[move].rate = rate;
    if (comment)
      moves[move].comment = comment;
    const payload = JSON.stringify(moves);
    fetch(`/api/position/save/${this.id}`, {method: 'POST', body: payload})
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      self.setMoves(data.moves);
    });
  }

  deleteMove(move) {
    const self = this;
    const moves = this.moves;
    delete moves[move];
    const payload = JSON.stringify(moves);
    fetch(`/api/position/save/${this.id}`, {method: 'POST', body: payload})
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      self.setMoves(data.moves);
    });
  }
}

const game = new Chess();

const board = Chessboard('board', {
  pieceTheme: '/static/vendor/chessboardjs/img/chesspieces/wikipedia/{piece}.png',
  position: 'start',
  draggable: true,
  onDragStart: function(source, piece, position, orientation) {
    if (game.game_over())
      return false;

    if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
      return false;
    }
  },
  onDrop: function(source, target) {
    const move = game.move({
      from: source,
      to: target,
      promotion: 'q',
    });
    if (move === null)
      return 'snapback';
    if (!(move.san in position.moves)) {
      position.addMove(move.san);
    }
  },
  onSnapEnd: function() {
    position.update();
  },
});


const position = new Position(game, board);

document.getElementById('addMove').addEventListener('submit', (event) => {
  event.preventDefault();
  const fd = new FormData(event.target);
  const move = fd.get('move').trim();
  const comment = fd.get('comment');
  if (move === '')
    return false;
  let rate = fd.get('rate');
  if (rate === "")
    rate = null;

  if (event.submitter.name === 'delete') {
    position.deleteMove(move);
  }
  else {
    position.addMove(move, rate, comment);
    event.target.reset();
    if (event.submitter.name === 'play') {
      if (game.move(move))
        position.update();
    }
  }
});

document.getElementById('back').addEventListener('click', (event) => {
  game.undo();
  position.update();
});
document.getElementById('flip').addEventListener('click', (event) => {
  board.flip();
  position.update();
});
document.addEventListener('keyup', (event) => {
  if (document.activeElement.form) {
    if (event.key === 'Enter') {
      if (event.ctrlKey)
        document.activeElement.form.add.click();
      else if (event.shiftKey)
        document.activeElement.form.play.click();
    }
  }
  else if (event.key === 'ArrowLeft') {
    game.undo();
    position.update();
  }
  else if (document.activeElement.classList.contains('move')) {
    if (event.key === 'Enter') {
      document.activeElement.click();
    }
    else {
      const moveId = document.activeElement.textContent.trim();
      const rate = ['M', 'P', 'B'].indexOf(event.key.toUpperCase()) - 1;
      if (rate >= -1) {
        const moveData = position.moves[moveId];
        if (event.shiftKey) {
          const form = document.getElementById('addMove');
          form.move.value = moveId;
          form.rate.value = rate;
          form.comment.value = moveData.comment || '';
          form.comment.focus();
        }
        else {
          position.addMove(moveId, rate, moveData.comment);
        }
      }
    }
  }
});
document.getElementById('moves').addEventListener('click', (event) => {
  if (event.target.classList.contains('move') && event.button == 0) {
    const moveId = event.target.textContent.trim();
    if (event.ctrlKey) {
      const moveData = position.moves[moveId];
      const form = document.getElementById('addMove');
      form.move.value = moveId;
      form.rate.value = moveData.rate || '0';
      form.comment.value = moveData.comment || '';
      form.comment.focus();
    }
    else {
      const move = game.move(moveId);
      if (move !== null)
        position.update();
    }
  }
});

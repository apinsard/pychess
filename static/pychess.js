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
    for (const [k, v] of Object.entries(moves)) {
      const comment = v.comment || '';
      let moveClass = 'unrated-move';
      if ('rate' in v) {
        if (v.rate > 0)
          moveClass = 'best-move';
        else if (v.rate < 0)
          moveClass = 'mistake-move';
        else
          moveClass = 'playable-move';
      }
      list += `<dt class="${moveClass}">${k}</dt><dd>${comment}</dd>`;
    }
    list += '</dl>';
    document.getElementById('moves').innerHTML = list;
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
  },
  onSnapEnd: function() {
    position.update();
  },
});


const position = new Position(game, board);

document.getElementById('addMove').addEventListener('submit', (event) => {
  event.preventDefault();
  const fd = new FormData(event.target);
  const move = fd.get('move');
  const comment = fd.get('comment');
  if (move === '')
    return false;
  let rate = fd.get('rate');
  if (rate === "")
    rate = null;
  position.addMove(move, rate, comment);
  event.target.reset();
});

document.getElementById('back').addEventListener('click', (event) => {
  game.undo();
  position.update();
});

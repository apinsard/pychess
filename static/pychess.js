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
  }

  setMoves(moves) {
    this.moves = moves;
    let list = '<dl>';
    for (const [k, v] of Object.entries(moves)) {
      let title = k;
      let comment = "";
      if ('rate' in v)
        title += ` (${v.rate})`;
      if ('comment' in v)
        comment = v.comment;
      list += `<dt>${title}</dt><dd>${comment}</dd>`;
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
    const fen = game.fen();
    board.position(fen);
    position.update();
  },
});


const position = new Position(game, board);

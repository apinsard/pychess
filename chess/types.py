# Copyright (c) 2022 Antoine Pinsard
import re

__all__ = ['Piece', 'Position']


class PieceMetaclass(type):
    """Piece metaclass used to instantiate all pieces upon class creation."""

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        for color in ['WHITE', 'BLACK']:
            for role in ['PAWN', 'KING', 'QUEEN', 'ROOK', 'KNIGHT', 'BISHOP']:
                piece = cls(getattr(cls, role), getattr(cls, color))
                setattr(cls, f'{color}_{role}', piece)
        return cls


class Piece(metaclass=PieceMetaclass):
    """Represent a piece type (role and color).

    >>> a = Piece(Piece.ROOK, Piece.WHITE)
    >>> b = Piece(Piece.ROOK, Piece.WHITE)
    >>> a is b
    True
    >>> Piece(Piece.KING, Piece.BLACK) is Piece.BLACK_KING
    True
    """

    WHITE = 0
    BLACK = 1
    COLOR_CHOICES = {
        WHITE: "White",
        BLACK: "Black",
    }

    PAWN = 0
    KING = 1
    QUEEN = 4
    ROOK = 5
    KNIGHT = 6
    BISHOP = 7
    ROLE_CHOICES = {
        PAWN: "Pawn",
        KING: "King",
        QUEEN: "Queen",
        ROOK: "Rook",
        KNIGHT: "Knight",
        BISHOP: "Bishop",
    }

    __cached_pieces = {}

    def __new__(cls, role, color):
        """Avoid instancing twice the same piece."""
        if (role, color) not in cls.__cached_pieces:
            cls.__cached_pieces[role, color] = super().__new__(cls)
        return cls.__cached_pieces[role, color]

    def __init__(self, role, color):
        assert role in self.ROLE_CHOICES
        assert color in self.COLOR_CHOICES
        self.color = color
        self.role = role

    def __repr__(self):
        return "<chess.Piece: {color} {role}>".format(
            role=self.ROLE_CHOICES[self.role],
            color=self.COLOR_CHOICES[self.color],
        )

    def __str__(self):
        return self.as_unicode()

    def __int__(self):
        return int(self.as_bitstring(), 2)

    def as_unicode(self, colored=False):
        icon = {
            self.KING: '\u265A',
            self.QUEEN: '\u265B',
            self.ROOK: '\u265C',
            self.BISHOP: '\u265D',
            self.KNIGHT: '\u265E',
            self.PAWN: '\u265F',
        }.get(self.role)
        if colored:
            color = '\033[37m' if self.color == self.WHITE else '\033[30m'
            icon = f'{color}{icon}'
        elif self.color == self.WHITE:
            icon = chr(ord(icon) - 6)
        return icon

    def as_bitstring(self):
        """Returns a 4 bits representation of the piece.

        The first bit gives the color:
            0 White
            1 Black

        The next 3 bits represent the role:
            000 Pawn
            001 King
            100 Queen
            101 Rook
            110 Knight
            111 Bishop
        """
        bitstring = str(self.color) + bin(self.role)[2:].zfill(3)
        return bitstring

    def as_fen(self):
        c = {
            self.KING: 'K',
            self.QUEEN: 'Q',
            self.ROOK: 'R',
            self.BISHOP: 'B',
            self.KNIGHT: 'N',
            self.PAWN: 'P',
        }.get(self.role)
        if self.color is self.BLACK:
            c = c.lower()
        return c

    @classmethod
    def from_fen(cls, fen):
        color = int(fen.islower())
        role = {
            'K': cls.KING,
            'Q': cls.QUEEN,
            'R': cls.ROOK,
            'B': cls.BISHOP,
            'N': cls.KNIGHT,
            'P': cls.PAWN,
        }.get(fen.upper())
        return cls(role, color)


class Castles:

    WK = 8
    WQ = 4
    BK = 2
    BQ = 1

    @property
    def wk(self):
        """White may O-O"""
        return self.can_castle(self.WK)

    @wk.setter
    def wk(self, value):
        return self.set_castle(self.WK, value)

    @property
    def wq(self):
        """White may O-O-O"""
        return self.can_castle(self.WQ)

    @wq.setter
    def wq(self, value):
        return self.set_castle(self.WQ, value)

    @property
    def bk(self):
        """Black may O-O"""
        return self.can_castle(self.BK)

    @bk.setter
    def bk(self, value):
        return self.set_castle(self.BK, value)

    @property
    def bq(self):
        """Black may O-O-O"""
        return self.can_castle(self.BQ)

    @bq.setter
    def bq(self, value):
        return self.set_castle(self.BQ, value)

    def __init__(self, castles):
        self.castles = castles

    def can_castle(self, castle):
        return self.castles & castle == castle

    def set_castle(self, castle, value):
        if value:
            self.castles |= castle
        else:
            self.castles &= ~castle

    def __int__(self):
        return self.castles

    def __bool__(self):
        return bool(self.castles)

    def __str__(self):
        return self.as_fen()

    def __repr__(self):
        return "<chess.Castles: {}>".format(self)

    def as_fen(self):
        return ''.join([
            'K' if self.wk else '',
            'Q' if self.wq else '',
            'k' if self.bk else '',
            'q' if self.bq else '',
        ]) or '-'


class Position:

    @property
    def castles(self):
        """Possible castles."""
        return self._castles

    @castles.setter
    def castles(self, value):
        """Possible castles can be given as:
            - A Castles instance
            - A dict mapping the castle type ('wk', 'wq', 'bk', 'bq') to a boolean
              (False values may be omitted)
            - A 4-uple or list of booleans in order (wk, wq, bk, bq)
            - A 4-bit string in order mentionned above (may be prefixed with 0b or not)
            - The integer representation of the 4-bit string mentionned above

        May also be set to None, in which case, possible castles will be guessed according
        to the position of the kings and rooks.
        """
        if value is None:
            value = self._guess_castles()
        if isinstance(value, dict):
            value = (
                value.get('wk', False),
                value.get('wq', False),
                value.get('bk', False),
                value.get('bq', False),
            )
        if isinstance(value, (tuple, list)):
            assert len(value) == 4
            value = sum([2**(3-i) * value[i] for i in range(4)])
        if isinstance(value, str):
            if value.startswith('0b'):
                value = value[2:]
            assert len(value) == 4
            value = int(value, 2)
        if not isinstance(value, Castles):
            value = Castles(value)
        self._castles = value

    @property
    def enpassant(self):
        """The column of the pawn that maybe captured en-passant if any. None otherwise."""
        if self._enpassant > 0:
            return self._enpassant - 2**3
        else:
            return None

    @enpassant.setter
    def enpassant(self, value):
        if value is None:
            self._enpassant = 0
        else:
            self._enpassant = value + 2**3

    def __init__(self, cells=None, castles=None, next_to_move=Piece.WHITE, enpassant=None):
        if cells is None:
            self.cells = [None] * 64
        else:
            self.cells = cells
        self.castles = castles
        self.next_to_move = next_to_move
        self.enpassant = enpassant

    def __repr__(self):
        return "<chess.Position: {}>".format(int(self))

    def __str__(self):
        return self.ascii_board(coordinates=True, colored=False)

    def __int__(self):
        return int(self.as_bitstring(), 2)

    def __getitem__(self, pos):
        pos = self.__flatten_pos(pos)
        return self.cells[pos]

    def __setitem__(self, pos, value):
        pos = self.__flatten_pos(pos)
        self.cells[pos] = value

    def __iter__(self):
        return iter(self.cells)

    def ascii_board(self, *, coordinates=True, colored=False):
        if colored:
            return self.colored_ascii_board(coordinates=coordinates)
        board = ''
        if coordinates:
            board += '   '
        board += '+---' * 8 + '+\n'
        for row in range(8):
            if coordinates:
                board += ' {} '.format(8 - row)
            board += '|'
            for col in range(8):
                cell = self[col, 7-row]
                if cell is None:
                    board += '   '
                else:
                    board += f' {cell} '
                board += '|'
            board += '\n'
            if coordinates:
                board += '   '
            board += '+---' * 8 + '+\n'
        if coordinates:
            board += '     a   b   c   d   e   f   g   h  '
        return board

    def colored_ascii_board(self, *, coordinates=True):
        board = ''
        for row in range(8):
            if coordinates:
                board += ' {} '.format(8 - row)
            for col in range(8):
                board += (
                    '\033[46m' if (
                        col % 2 == row % 2
                    )
                    else '\033[44m'
                )
                cell = self[col, 7-row]
                if cell is None:
                    board += '   '
                else:
                    board += ' ' + cell.as_unicode(colored=True) + ' '
            board += '\033[0m\n'
        if coordinates:
            board += '    a  b  c  d  e  f  g  h '
        return board

    def get_king_position(self, color):
        for pos, cell in enumerate(self.cells):
            if cell is not None and cell.role == Piece.KING and cell.color == color:
                return pos

    def as_bitstring(self):
        """Returns a bitstring representation of the position.

        The right-most bit represents the next color to move.

        The next 4 bits represents possible castles.

        If white king's position cannot be infered from possible castles,
        its position is encoded on the next 6 bits.

        If black king's position cannot be infered from possible castles,
        its position is encoded on the next 6 bits.

        The next bit represents the possibility of an en-passant capture.
        In such case, the column of the capturable pawn is encoded on the next
        3 bits.

        Then for each cell from a1 to h8, omitting the kings cells and the
        "castleable" rooks cells:

            If the cell is empty, it is encoded with a single 0. Otherwise,
            it is encoded with a 1, followed one bit for the piece color,
            followed by the piece role:
                - Two bits representation of the role for a piece on the first or last row
                - A single 0 for a pawn
                - A 1 followed by two bits representation of the role otherwise.
        """
        bitstring = ''
        bitstring += str(self.next_to_move)
        bitstring += bin(int(self.castles))[2:].zfill(4)
        if not (self.castles.wk or self.castles.wq):
            bitstring += bin(self.get_king_position(Piece.WHITE))[2:].zfill(6)
        if not (self.castles.bk or self.castles.bq):
            bitstring += bin(self.get_king_position(Piece.BLACK))[2:].zfill(6)
        bitstring += bin(self._enpassant)[2:]
        for i, cell in enumerate(self.cells):
            if cell is None:
                bitstring += '0'
            elif not self._is_deterministic_cell(i, cell):
                piece = cell.as_bitstring()
                if cell.role == Piece.PAWN:
                    piece = piece[:2]
                elif i < 8 or i >= (64 - 8):
                    # First row and last row can't have pawns.
                    piece = piece[0] + piece[2:]
                bitstring += '1' + piece
        # Revert the bitstring because the first zeros are significants while the last aren't.
        bitstring = bitstring[::-1]
        return bitstring

    def as_fen(self):
        fen = ''
        for row in range(7, -1, -1):
            for col in range(8):
                cell = self[col, row]
                if cell is None:
                    fen += '1'
                else:
                    fen += cell.as_fen()
            fen += '/'
        fen = re.sub('1+', lambda m: str(len(m[0])), fen[:-1])

        fen += ' '
        if self.next_to_move == Piece.WHITE:
            fen += 'w'
        else:
            fen += 'b'

        fen += ' ' + self.castles.as_fen()

        fen += ' '
        if self.enpassant:
            fen += chr(ord('a') + self.enpassant)
            if self.next_to_move == Piece.WHITE:
                fen += '6'
            else:
                fen += '3'
        else:
            fen += '-'

        return fen

    def _is_deterministic_cell(self, pos, piece):
        king = piece and piece.role == Piece.KING
        a1 = pos == 0 and self.castles.wq
        h1 = pos == 7 and self.castles.wk
        a8 = pos == 56 and self.castles.bq
        h8 = pos == 63 and self.castles.bk
        return king or a1 or h1 or a8 or h8

    def _guess_castles(self):
        return {
            'wk': self._guess_castle('h1'),
            'wq': self._guess_castle('a1'),
            'bk': self._guess_castle('h8'),
            'bq': self._guess_castle('a8'),
        }

    def _guess_castle(self, rook_pos):
        color = Piece.WHITE if rook_pos[1] == '1' else Piece.BLACK
        rook = self[rook_pos]
        king = self['e' + rook_pos[1]]
        if rook is None or king is None:
            return False
        return rook == Piece(Piece.ROOK, color) and king == Piece(Piece.KING, color)

    def _might_enpassant(self, col):
        row = 5 if self.next_to_move == Piece.WHITE else 4
        might_ep = False
        if col > 0:
            might_ep = might_ep or self[col-1, row] == Piece(Piece.PAWN, self.next_to_move)
        if col < 7:
            might_ep = might_ep or self[col+1, row] == Piece(Piece.PAWN, self.next_to_move)
        return might_ep

    @classmethod
    def decompress(cls, bitstring):
        """Restore a Position instance from a compressed bitstring
        or its integer representation.

        Reverse process of as_bitstring()
        """
        position = cls()
        if isinstance(bitstring, int):
            bitstring = bin(bitstring)[2:]
        bitstring = bitstring[::-1]
        position.next_to_move = int(bitstring[0])
        position.castles = bitstring[1:5]
        bitstring = bitstring[5:]

        if position.castles.wk or position.castles.wq:
            w_king_pos = 'e1'
            if position.castles.wk:
                position['h1'] = Piece.WHITE_ROOK
            if position.castles.wq:
                position['a1'] = Piece.WHITE_ROOK
        else:
            w_king_pos = int(bitstring[:6], 2)
            bitstring = bitstring[6:]
        position[w_king_pos] = Piece.WHITE_KING

        if position.castles.bk or position.castles.bq:
            b_king_pos = 'e8'
            if position.castles.bk:
                position['h8'] = Piece.BLACK_ROOK
            if position.castles.bq:
                position['a8'] = Piece.BLACK_ROOK
        else:
            b_king_pos = int(bitstring[:6], 2)
            bitstring = bitstring[6:]
        position[b_king_pos] = Piece.BLACK_KING

        if bitstring[0] == '1':
            position._enpassant = int(bitstring[1:4], 2)
            bitstring = bitstring[4:]
        else:
            bitstring = bitstring[1:]

        i = 0
        pos = 0
        while i < len(bitstring):
            if position[pos] is not None:
                pos += 1
                continue
            if bitstring[i] == '1':
                piece = (bitstring[i+1:i+5] + '0000')[:4]
                color = int(piece[0])
                if pos < 8 or pos >= (64 - 8):
                    role = int('1' + piece[1:3], 2)
                    i += 3
                elif piece[1] == '0':
                    role = 0
                    i += 2
                else:
                    role = int(piece[1:], 2)
                    i += 4
                position[pos] = Piece(role, color)
            i += 1
            pos += 1

        return position

    @classmethod
    def load_fen(cls, fen):
        position = cls()
        parts = fen.split()

        rows = parts[0].split('/')
        for i, row in enumerate(rows):
            col = 0
            for c in row:
                if c.isnumeric():
                    for j in range(int(c)):
                        position[col, 7-i] = None
                        col += 1
                else:
                    position[col, 7-i] = Piece.from_fen(c)
                    col += 1

        if len(parts) > 1 and parts[1] == 'b':
            position.next_to_move = Piece.BLACK

        if len(parts) > 2:
            position.castles = {
                'wk': 'K' in parts[2],
                'wq': 'Q' in parts[2],
                'bk': 'k' in parts[2],
                'bq': 'q' in parts[2],
            }
        else:
            position._guess_castles()

        if len(parts) > 3 and parts[3] != '-':
            enpassant = ord('a') - ord(parts[3][0].lower())
            if position._might_enpassant(enpassant):
                position.enpassant = enpassant

        return position

    @classmethod
    def initial(cls):
        """Returns the initial position of a chess board."""
        row_1 = [
            Piece(role, Piece.WHITE)
            for role in [
                Piece.ROOK,
                Piece.KNIGHT,
                Piece.BISHOP,
                Piece.QUEEN,
                Piece.KING,
                Piece.BISHOP,
                Piece.KNIGHT,
                Piece.ROOK,
            ]
        ]
        row_2 = [Piece.WHITE_PAWN] * 8
        row_7 = [Piece.BLACK_PAWN] * 8
        row_8 = [
            Piece(role, Piece.BLACK)
            for role in [
                Piece.ROOK,
                Piece.KNIGHT,
                Piece.BISHOP,
                Piece.QUEEN,
                Piece.KING,
                Piece.BISHOP,
                Piece.KNIGHT,
                Piece.ROOK,
            ]
        ]
        cells = row_1 + row_2 + [None] * 32 + row_7 + row_8
        return cls(cells, castles='1111')

    @staticmethod
    def __flatten_pos(pos):
        if isinstance(pos, (str, tuple)):
            col, row = pos
            if isinstance(col, str):
                col = ord(col.upper()) - ord('A')
                row = int(row) - 1
            pos = row * 8 + col
        elif not isinstance(pos, int):
            raise KeyError(f"Invalid cell identifier: {pos!r}")
        return pos

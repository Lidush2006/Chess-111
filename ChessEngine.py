"""
отвечает за хранение информации о текущем положении игры ну типа партии.
отвечает за допустимость ходов и введет список ходов
"""
class GameState:
    def __init__(self):
        """
        это чтовроде двух мерного (2д) списка 8 на 8 и они обозначенны 2 символами первый значит тип (b или w) а второй значит конкретную фигуру 'R', 'N', 'B'...и тд
        инициализирует шахматную доску и связанные с ней параметры состояния игры
        """
        self.board = [ # типа это скелет основа самой доски
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True#
        self.move_log = []#Список сделанных ходов (для отмены/повтора)
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)#Текущие координаты королей.
        self.checkmate = False#
        self.stalemate = False#
        self.in_check = False#
        self.pins = []#
        self.checks = []#
        self.enpassant_possible = ()  # координаты квадрата, в котором возможен захват
        self.enpassant_possible_log = [self.enpassant_possible]#
        self.current_castling_rights = CastleRights(True, True, True, True)#Текущие права на рокировку
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,#История изменений прав на рокировку.
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
       Принимает ход в качестве параметра и выполняет его.
        (это не сработает при рокировке, продвижении пешки и переходе в другую команду)
        """
        self.board[move.start_row][move.start_col] = "--"  # Убираем фигуру с начальной позиции
        self.board[move.end_row][move.end_col] = move.piece_moved  # Ставим её на конечную позицию
        self.move_log.append(move)  # Сохраняем ход в лог
        self.white_to_move = not self.white_to_move  # Передаём ход другому игроку
        # Если ходит король, обновляем его позицию
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)
#УСЛОЖНЕНИЕ !!!
        #Превращение пешки
        if move.is_pawn_promotion:

            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q" # По умолчанию в ферзя

        # Взятие на проходе
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # # Удаляем пешку, которая "перепрыгнула" через битое поле

        # Поле enpassant_possible обновляется, если пешка походила на 2 клетки
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # перемещение ладьи
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # king-side castle move
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # Перемещаем ладью
                self.board[move.end_row][move.end_col + 1] = '--'  # Удаляем старую ладью
            else:  # Длинная рокировка (O-O-O)
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]  # Перемещаем ладью
                self.board[move.end_row][move.end_col - 2] = '--'  # Удаляем старую ладью

        self.enpassant_possible_log.append(self.enpassant_possible) # Лог взятия на проходе

        # Лог прав на рокировку, обновите права на рокировку - всякий раз, когда это ход ладьей или королем
        self.updateCastleRights(move) # Обновляем текущие права
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks, # Сохраняем в историю
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):

        """
        Отменить последний ход Усложнение
        """
        if len(self.move_log) != 0:  # убедись, что есть шаг, который нужно отменить
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # меняйте игроков местами
            # при необходимости измените положение короля
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # отменить случайное перемещение
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # оставьте посадочный квадрат пустым
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            self.castle_rights_log.pop()
            self.current_castling_rights = self.castle_rights_log[
                -1]   # устанавливаем текущие права на рокировку равными последнему элементу в списке
            # отмена рокировки
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # queen-side
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Проверка взятия ладьи
        """
        if move.piece_captured == "wR":  # Если съели белую ладью
            if move.end_col == 0:  # Левая ладья (a1)
                self.current_castling_rights.wqs = False  # Запрет длинной рокировки белых
            elif move.end_col == 7:  # Правая ладья (h1)
                self.current_castling_rights.wks = False  # Запрет короткой рокировки белых
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # потеря длинной рокировки чёрных
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # потеря короткой рокировки чёрных
                self.current_castling_rights.bks = False

        if move.piece_moved == 'wK': #Проверка хода королём
            self.current_castling_rights.wqs = False# Запрет обеих рокировок
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK':
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR': #Проверка хода ладьёй
            if move.start_row == 7:
                if move.start_col == 0:  # left rook
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # right rook
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # left rook
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # right rook
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Сохранение текущих прав на рокировку.
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # Проверка шахов и связок
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()
                check = self.checks[0]  # данные о шахе
                check_row = check[0] # ряд атакующей фигуры
                check_col = check[1]# колонка атакующей фигуры
                piece_checking = self.board[check_row][check_col] # фигура, объявляющая шах
                valid_squares = []  # клетки, на которые могут пойти фигуры (для защиты)
# если шах от коня - нужно либо взять коня, либо уйти королём, другие фигуры можно блокировать
                if piece_checking[1] == "N":  # если шах от коня
                    valid_squares = [(check_row, check_col)]  # только взятие коня
                else:
                    # вычисляем клетки между атакующей фигурой и королём
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[
                            1] == check_col:
                            break

                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != "K":
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:  # double check, king has to move
                self.getKingMoves(king_row, king_col, moves)
        else:  # not in check - all moves are fine
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:

                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Определить, находится ли текущий игрок под шахом
        """
        if self.white_to_move: #проверяем, атакован ли белый король
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:               #проверяем, атакован ли черный король
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Определите, может ли враг атаковать столбец квадратного row col
        """
        self.white_to_move = not self.white_to_move
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Все ходы без счета.
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # вызывает соответствующую функцию перемещения в зависимости от типа элемента
        return moves

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else:
                            break
                else:
                    break
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        все ходы пешки
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # 2 square pawn advance
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # capture to the left
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # king right of the pawn
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):
        """
        все ходы ладьи
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][
                    1] != "Q":  # нельзя снимать ферзя при ходах ладьей, можно снимать только при ходах слоном
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # empty space is valid
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # capture enemy piece
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getKnightMoves(self, row, col, moves):
        """
        все ходы для коня, расположенного в начале строки, и добавим их в список
        """
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
        все ходы для слона, расположенного в начале строки, и добавьте их в список.
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # capture enemy piece
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getQueenMoves(self, row, col, moves):#метод getQueenMoves генерирует все возможные ходы ферзя на шахматной доске, используя уже реализованные методы для ладьи (getRookMoves) и слона (getBishopMoves)
        """
        все ходы для ферзя, расположенного в конце строки, и добавьте их в список.
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Получите все ходы короля, расположенного в начале строки, и добавьте их в список.
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # не союзная фигура - пустая или вражеская
                    # поместите короля на крайнюю клетку
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # верните короля на прежнее место
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        все допустимые ходы короля (ряд, столбец) и добавьте их в список ходов
        """
        if self.squareUnderAttack(row, col):
            return  # не могу закрыть замок, находясь под контролем
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))

# права ракировки
class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    # в шахматах поля на доске обозначаются символами, одним из которых является число от 1 до 8 (которое соответствует строкам).
    # а вторая буква - это буква между a-f (соответствует столбцам), чтобы использовать это обозначение, нам нужно сопоставить наши координаты [row][col]

    #словари нужны для перевода между шахматной нотацией (например, "e2") и индексами матрицы (строка, столбец)
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0} # переводит ряды для матрицы в обозначении от 7 до 0
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()} #обратный словарь, чтобы перевести индекс строки (0–7) обратно в шахматный номер ("8"–"1")
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}#преобразует букву столбца ("a"–"h") в индекс столбца матрицы (0–7).
    cols_to_files = {v: k for k, v in files_to_cols.items()}#обратный словарь, чтобы перевести индекс столбца (0–7) обратно в букву ("a"–"h")
    ''' 
    хранящий информацию о перемещении фигуры
    '''
    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0] #откуда пошла фигура
        self.start_col = start_square[1]#
        self.end_row = end_square[0]#куда пошла фигура.
        self.end_col = end_square[1]#
        self.piece_moved = board[self.start_row][self.start_col]#фигура, которая делает ход (например, "wp" — белая пешка
        self.piece_captured = board[self.end_row][self.end_col]#фигура, которая была съедена (если есть
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (#был ли ход взятием
                self.piece_moved == "bp" and self.end_row == 7)
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # castle move
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
Переопределение метода сравнения (equals)
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square

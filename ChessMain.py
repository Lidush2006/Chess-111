"""
Это главный файл я знаю что обычно файл Engine главный, но я их перепутал в самом начале а испровлять было поздно
обрабатывает пользовательские данные
показываеттекущее положение игры
"""
import pygame as p
import ChessEngine, ChessAI
import sys
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 512 # ширина и высота равна 512 можно другое число но это просто больше подходит оно должно быть четным и
MOVE_LOG_PANEL_WIDTH = 250 #Фиксированная ширина панели
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT #Высота панели равна высоте шахматной доски
DIMENSION = 8 # размеры доски 8 на 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION # размер квадрата высоту - ширену делим на размер
MAX_FPS = 15 # качество изображения, нужно для анимации (не ставь больше ато логает,, мо дар боста)
IMAGES = {} # словарь переменых


def loadImages(): # для создания кода я отталкивался от старых джава игр нудевых поэтому тут остались некоторые рудименты
    """
    это типа синхранизирует пнг изображения чтобы их можно было использовать для вывода как полноценное игра
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        '''эту комбинацию снизу я должен был написать по отножении к каждой фигуре но это муторно и я сделал код сверху
        грубо говоря это камбинация позволяет выбрать квадрат на доске и если там есть фигура из списка то типа нарисуй это изображение распредели по экрану 
        '''
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))# размеры квадрата его масштабы

def main():
    """
    основной драйвер для нашего кода
    он будет обрабатывать вводимые пользователем данные и обновлять графику
    """
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white")) #цвет фона, потом его будет не видно, но он нужен
    game_state = ChessEngine.GameState() #нужно чтобы оно нормально работало с chessEgina
    valid_moves = game_state.getValidMoves()
    move_made = False  #  указывающая на момент совершения перемещения
    animate = False  # переменная, указывающая, когда мы должны анимировать движение
    loadImages()  # сделайте это только один раз перед циклом while
    running = True
    square_selected = ()  # изначально ни один квадрат не выбран, при этом будет отслеживаться последний клик пользователя
    player_clicks = []  # это позволит отслеживать клики игроков
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    player_one = True
    player_two = False
 # визуал анимация движения
    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            # работа с мышью
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) расположение мыши
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # пользователь дважды нажал на один и тот же квадрат
                        # УСЛОЖНЕНИЕ !!!
                        square_selected = ()  # отменить выделение
                        player_clicks = []  # четкие клики
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # добавить как для 1-го, так и для 2-го клика
                    if len(player_clicks) == 2 and human_turn:  # after 2nd click
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  # сброс кликов пользователя
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # обработчик ключей
            elif e.type == p.KEYDOWN:
                # УСЛОЖНЕНИЕ !!!
                if e.key == p.K_z:  # отмена при нажатии клавиши "z"
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_r:  # перезагрузите игру при нажатии клавиши "r"
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # Проверка условий для хода AI
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking: #Если AI ещё не начал "думать"
                ai_thinking = True
                return_queue = Queue()  # used to pass data between threads
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()
            #Если AI закончил "думать"
            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made: #анимация движения
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Повезет в следуйщий раз")
            else:
                drawEndGameText(screen, "Белые победили, ничего нового")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Победила дружба")

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    отвечает за графику и типа рисует
    """
    drawBoard(screen)  # нарисуйте квадраты на доске
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # draw pieces on top of those squares


def drawBoard(screen):
    """
  нарисуйте квадраты на доске те самы с которыми можно взаимодействовать
    верхний левый квадрат всегда светлый (правила шахмат)
    """
    global colors
    colors = [p.Color("white"), p.Color("pink")] # цвета квадратов
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    подцветка куда можно ходить УСЛОЖНЕНИЕ !!!
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green')) # последний ход
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # square_selected is a piece that can be moved
            # highlight selected square
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)  # transparency value 0 -> transparent, 255 -> opaque
            s.fill(p.Color('blue')) # выбранная фигура
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # highlight moves from that square
            s.fill(p.Color('light green')) # куда можно ходить
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

def drawPieces(screen, board):
    """
    рисуем фигуры на доске, используя файл game_state.board
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))# этот цикл можно было бы добавить в дроуборд но тогда бы былобы сложнее сделать подцветку ( типа куможно ходить)

def drawMoveLog(screen, game_state, font):
    """
    Рисует журнал перемещений типа счетчик ходов
    """
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('red'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Animating a move
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()

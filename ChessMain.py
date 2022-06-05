"""
Main driver file.
Handling user input.
Displaying current GameState object.
"""
import pygame
import ChessEngine
import ChessAI
import sys
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 514
SCORE_PANEL_WIDTH = 20
MOVE_LOG_PANEL_WIDTH = BOARD_WIDTH + SCORE_PANEL_WIDTH
MOVE_LOG_PANEL_HEIGHT = 100
SCORE_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
TILE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

# Colours
black = (0, 0, 0)
white = (255, 255, 255)
brown = (87, 58, 46)
cream = (252, 204, 116)
green = (102, 255, 0)
blue = (255,87,51)
yellow = (255, 255, 0)

prev_score = 0

def loadImages():
    """
    Initialize a global directory of images.
    This will be called exactly once in the main.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = pygame.transform.scale(pygame.image.load("images/" + piece + ".png"), (TILE_SIZE, TILE_SIZE))


def main():
    """
    The main driver for our code.
    This will handle user input and updating the graphics.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCORE_PANEL_WIDTH + BOARD_WIDTH, BOARD_HEIGHT+MOVE_LOG_PANEL_HEIGHT))
    pygame.display.set_icon(pygame.image.load('Images/bQ.png'))
    pygame.display.set_caption('Chess')
    clock = pygame.time.Clock()
    screen.fill(white)
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # flag variable for when a move is made
    animate = False  # flag variable for when we should animate a move
    loadImages()  # do this only once before while loop
    running = True
    selected_square = ()   # this will keep track of the last click of the user (tuple(row,col))
    player_clicks = []  # this will keep track of player clicks (two tuples)
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = pygame.font.SysFont("Arial", 14, False, False)
    player_one = True  # if a human is playing white, then this will be True, else False
    player_two = False  # if a human is playing white, then this will be True, else False

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # mouse handler
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    location = pygame.mouse.get_pos()  # (x, y) location of the mouse
                    col = location[0] // TILE_SIZE
                    row = location[1] // TILE_SIZE
                    if selected_square == (row, col) or col >= 8:  # user clicked the same square twice
                        selected_square = ()  # deselect
                        player_clicks = []  # clear clicks
                    else:
                        selected_square = (row, col)
                        player_clicks.append(selected_square)  # append for both 1st and 2nd click
                    if len(player_clicks) == 2 and human_turn:  # after 2nd click
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                selected_square = ()  # reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [selected_square]

            # key handler
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_z:  # undo when 'z' is pressed
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == pygame.K_r:  # reset the game when 'r' is pressed
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    selected_square = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # used to pass data between threads
                move_finder_process = Process(target=ChessAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, selected_square)
        drawScore(screen, game_state)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        pygame.display.flip()


def drawGameState(screen, game_state, valid_moves, selected_square):
    """
    Responsible for all the graphics within current game state.
    """
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, game_state, valid_moves, selected_square)
    drawPieces(screen, game_state.board)  # draw pieces on top of those squares


def drawBoard(screen):
    """
    Draw the squares on the board.
    The top left square is always light.
    """
    global colours
    colours = [cream, brown]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            colour = colours[((row + column) % 2)]
            pygame.draw.rect(screen, colour, pygame.Rect(column * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def highlightSquares(screen, game_state, valid_moves, selected_square):
    """
    Highlight square selected and moves for piece selected.
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.set_alpha(100)
        s.fill(green)
        screen.blit(s, (last_move.end_col * TILE_SIZE, last_move.end_row * TILE_SIZE))
    if selected_square != ():
        row, col = selected_square
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # selected_square is a piece that can be moved
            # highlight selected square
            s = pygame.Surface((TILE_SIZE, TILE_SIZE))
            s.set_alpha(100)  # transparency value 0 -> transparent, 255 -> opaque
            s.fill(blue)
            screen.blit(s, (col * TILE_SIZE, row * TILE_SIZE))
            # highlight moves from that square
            s.fill(yellow)
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * TILE_SIZE, move.end_row * TILE_SIZE))


def drawPieces(screen, board):
    """
    Draw the pieces on the board using the current game_state.board
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], pygame.Rect(column * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))


def drawScore(screen,game_state):
    """
    Draws the side bar with the score.

    """
    global prev_score

    score = ChessAI.scoreBoard(game_state)
    if(score<prev_score):
        score_rect = pygame.Rect(BOARD_WIDTH, 0, SCORE_PANEL_WIDTH, SCORE_PANEL_HEIGHT/2-(score/15)*(SCORE_PANEL_HEIGHT)/2)
        pygame.draw.rect(screen, black, score_rect)
    elif (score > prev_score):
        score_rect = pygame.Rect(BOARD_WIDTH, SCORE_PANEL_HEIGHT/2 - (score/15)*(SCORE_PANEL_HEIGHT)/2, SCORE_PANEL_WIDTH,SCORE_PANEL_HEIGHT/2 - (score/15)*(SCORE_PANEL_HEIGHT)/2)
        pygame.draw.rect(screen, white, score_rect)
    prev_score = score



def drawMoveLog(screen, game_state, font):
    """
    Draws the move log.

    """
    move_log_rect = pygame.Rect(0, BOARD_HEIGHT, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    pygame.draw.rect(screen, black, move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 8
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, white)
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    font = pygame.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, black)
    text_location = pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, black)
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Animating a move
    """
    global colours
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        colour = colours[(move.end_row + move.end_col) % 2]
        end_square = pygame.Rect(move.end_col * TILE_SIZE, move.end_row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, colour, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = pygame.Rect(move.end_col * TILE_SIZE, enpassant_row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
import numpy as np
import pygame as pg
#from Chess import ChessEngine, ChessFunctions, ChessBot
from ChessFunctions import TableWidth, TableHeight, SQ_Size, MAX_FPS, GameOngoing, GameEnded, Winner
#from Chess import ChessBot
#from ChessEngine import screen
import ChessEngine, ChessFunctions, ChessBot

#TODO Look into ideas on using multiple CPU cores to calculate faster
def LoadImages():
    pieces = ["11", "12", "13", "14", "15", "16", "-11", "-12", "-13", "-14", "-15", "-16"]
    for piece in pieces:
        ChessFunctions.Images[piece] = pg.transform.scale(pg.image.load("Images/" + piece + ".png"), (SQ_Size, SQ_Size))

    
def main():
    global PromSQ
    pg.init()
    clock = pg.time.Clock()
    screen = pg.display.set_mode((TableWidth * 15 // 10, TableHeight), pg.SRCALPHA)
    gs = ChessEngine.GameState("White")
    Bot = ChessBot.Bot()

    StartButton = ChessFunctions.Button(TableWidth * 17 // 16, TableHeight // 8 - 40, TableWidth * 3 // 8, TableHeight // 6, "Start", "Buttons/Green.png")
    ResignButton = ChessFunctions.Button(TableWidth * 17 // 16, TableHeight * 5 // 6 - 20, TableWidth * 3 // 8, TableHeight // 6, "Resign", "Buttons/Green.png")
    RematchButton = ChessFunctions.Button(TableWidth // 4 + 40, TableHeight * 6 // 10, TableWidth // 2 - 80, TableHeight // 10, "Rematch", "Buttons/Green.png")

    LoadImages()
    running = True
    ChessFunctions.DrawBoard(gs, screen)
    ChessFunctions.DrawMenu(gs, screen, [StartButton, ResignButton, RematchButton])
    while running:

        if gs.PlayerColor == "White" and not gs.WhiteToMove and not gs.GameEnded:
            best_next_gs = Bot.FindBestMove(gs, 4)
            gs = best_next_gs
        elif gs.PlayerColor == "Black" and gs.WhiteToMove and not gs.GameEnded:
            best_next_gs = Bot.FindBestMove(gs, 4)
            gs = best_next_gs

        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.MOUSEBUTTONDOWN:
                if (gs.PlayerColor == "White" and gs.WhiteToMove) or (gs.PlayerColor == "Black" and not gs.WhiteToMove):
                    location = pg.mouse.get_pos()
                    StartButton.IsPressed(location)
                    row = location[1] // SQ_Size
                    col = location[0] // SQ_Size
                    if gs.PlayerColor == "White":
                        pass
                    elif gs.PlayerColor == "Black":
                        row = 7 - row
                        col = 7 - col
                    if location[0] < TableWidth and ChessFunctions.GameOngoing:
                        if gs.SelectedPiece:
                            if gs.WhiteToMove and row == 0 and gs.Board[gs.SelectedPiece[0]*8 + gs.SelectedPiece[1]] == 11:
                                if (row, col) in gs.LegalMovesWithSelectedPiece:
                                    gs.Promoting = True
                                    PromSQ = (row, col)
                            elif not gs.WhiteToMove and row == 7 and gs.Board[gs.SelectedPiece[0]*8 + gs.SelectedPiece[1]] == -11:
                                if (row, col) in gs.LegalMovesWithSelectedPiece:
                                    gs.Promoting = True
                                    PromSQ = (row, col)
                        if gs.Promoting:
                            if location[0] > (TableWidth-SQ_Size)//2 and location[0] < (TableHeight+SQ_Size)//2:
                                if location[1] > TableHeight//2 - 2*SQ_Size:
                                    if location[1] < TableHeight // 2 - 1 * SQ_Size and gs.WhiteToMove:
                                        gs.PromotingTo = 12
                                    elif location[1] < TableHeight // 2 - 1 * SQ_Size and not gs.WhiteToMove:
                                        gs.PromotingTo = -12
                                    elif location[1] < TableHeight // 2 and gs.WhiteToMove:
                                        gs.PromotingTo = 13
                                    elif location[1] < TableHeight // 2 and not gs.WhiteToMove:
                                        gs.PromotingTo = -13
                                    elif location[1] < TableHeight // 2 + 1 * SQ_Size and gs.WhiteToMove:
                                        gs.PromotingTo = 14
                                    elif location[1] < TableHeight // 2 + 1 * SQ_Size and not gs.WhiteToMove:
                                        gs.PromotingTo = -14
                                    elif location[1] < TableHeight // 2 + 2 * SQ_Size and gs.WhiteToMove:
                                        gs.PromotingTo = 16
                                    elif location[1] < TableHeight // 2 + 2 * SQ_Size and not gs.WhiteToMove:
                                        gs.PromotingTo = -16
                                    gs.ProbeSQ(PromSQ[0], PromSQ[1])

                        elif not gs.Promoting:
                            gs.ProbeSQ(row, col)

                        if gs.Mated[0]:
                            gs.GameEnded = True
                            ChessFunctions.EndTheGame(gs.Mated)
                        elif gs.Mated[1]:
                            gs.GameEnded = True
                            ChessFunctions.EndTheGame(gs.Mated)
                        elif gs.StaleMated:
                            gs.GameEnded = True
                            ChessFunctions.EndTheGame(gs.Mated)
                        elif gs.FiftyRuleCount >= 100:
                            gs.GameEnded = True
                            gs.FiftyRuleDraw = True
                            ChessFunctions.EndTheGame(gs.Mated)
                    if StartButton.IsPressed(location) and ChessFunctions.GameOngoing == False:
                        ChessFunctions.GameOngoing = True
                    elif ResignButton.IsPressed(location) and ChessFunctions.GameOngoing == True:
                        ChessFunctions.GameOngoing = False
                        gs.Resigned = True
                        gs.GameEnded = True
                        ChessFunctions.GameEnded = True

                    if ChessFunctions.GameEnded and RematchButton.IsPressed(location):
                        if np.random.random() - 0.5 > 0:
                            gs = ChessEngine.GameState("White")
                        else:
                            gs = ChessEngine.GameState("Black")
                        ChessFunctions.GameOngoing = True
                        ChessFunctions.GameEnded = False



        ChessFunctions.DrawGameState(screen, gs)
        ChessFunctions.DrawMenu(gs, screen, [StartButton, ResignButton, RematchButton])
        if gs.Promoting and gs.WhiteToMove:
            ChessFunctions.DrawPromotionOptions(screen, PromSQ, 1)
        elif gs.Promoting and not gs.WhiteToMove:
            ChessFunctions.DrawPromotionOptions(screen, PromSQ, -1)
        clock.tick(MAX_FPS)
        pg.display.flip()





main()



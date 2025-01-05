import pygame as pg
import pygame.gfxdraw
import copy

TableWidth = TableHeight = 512
Width = 8
SQ_Size = TableWidth // Width
MAX_FPS = 15
Images = {}
GameOngoing = False
GameEnded = False
Winner = ""


class Button():
    def __init__(self, x, y, w, h, text, image):
        self.x = x #Top left coordinate
        self.y = y #Top left coordinate
        self.w = w #width
        self.h = h #height
        self.text = text #Button Text
        self.image = image #image to be used as button

    def __copy__(self):
        # Create a new instance and copy attributes
        cls = self.__class__
        new_instance = cls.__new__(cls)
        new_instance.__dict__.update(self.__dict__)
        return new_instance

    def __deepcopy__(self, memo):
        # Create a new instance and deepcopy attributes
        cls = self.__class__
        new_instance = cls.__new__(cls)
        memo[id(self)] = new_instance
        for k, v in self.__dict__.items():
            setattr(new_instance, k, copy.deepcopy(v, memo))
        return new_instance

    def IsPressed(self, location):
        if self.x < location[0] < self.x + self.w and self.y < location[1] < self.y + self.h:
            return True
        else:
            return False

    def Draw(self, screen):
        Rect = pg.Rect(self.x, self.y, self.w, self.h)
        screen.blit(pg.transform.scale(pg.image.load(self.image), (self.w, self.h)), Rect)
        font = pg.font.Font(None, self.h*2//3)
        text_surface = font.render(self.text, True, [0, 0, 0, 255])
        text_rect = text_surface.get_rect(center=(self.x + self.w//2, self.y + self.h//2))
        screen.blit(text_surface, text_rect)




def DrawGameState(screen, gs):
    screen.fill((170, 200, 200))
    DrawBoard(gs, screen)
    DrawPieces(gs, screen)
    DrawMoves(gs, screen)


def DrawBoard(gs, screen):
    LatentColors = [[255, 255, 255, 120], [100, 180, 100, 120]]
    Colors = [[255, 255, 255, 255], [100, 180, 100, 255]]
    HighLightColors = [[150, 150, 150], [140, 255, 140]]
    if not GameOngoing:
        for r in range(Width):
            for c in range(Width):
                LatentColor = LatentColors[(r + c) % 2]
                pg.draw.rect(screen, LatentColor, pg.Rect(c * SQ_Size, r * SQ_Size, SQ_Size, SQ_Size))

    else:
        for r in range(Width):
            for c in range(Width):
                Color = Colors[(r + c) % 2]
                pg.draw.rect(screen, Color, pg.Rect(c * SQ_Size, r * SQ_Size, SQ_Size, SQ_Size))
        if gs.SelectedPiece:
            if gs.PlayerColor == "White":
                HighColor = HighLightColors[(gs.SelectedPiece[0] + gs.SelectedPiece[1]) % 2]
                pg.draw.rect(screen, HighColor, pg.Rect(gs.SelectedPiece[1] * SQ_Size, gs.SelectedPiece[0] * SQ_Size, SQ_Size, SQ_Size))
            if gs.PlayerColor == "Black":
                HighColor = HighLightColors[((gs.SelectedPiece[0]) + gs.SelectedPiece[1]) % 2]
                pg.draw.rect(screen, HighColor, pg.Rect((7 - gs.SelectedPiece[1]) * SQ_Size, (7 - gs.SelectedPiece[0]) * SQ_Size, SQ_Size, SQ_Size))

def DrawPieces(gs, screen):
    for r in range(Width):
        for c in range(Width):
            if gs.PlayerColor == "White":
                piece = (gs.Board[r*8 + c])
                if piece != 0:
                    screen.blit(Images[str(piece)], pg.Rect(c * SQ_Size, r * SQ_Size, SQ_Size, SQ_Size))
            elif gs.PlayerColor == "Black":
                piece = (gs.Board[(7-r)*8 + (7-c)])
                if piece != 0:
                    screen.blit(Images[str(piece)], pg.Rect(c * SQ_Size, r * SQ_Size, SQ_Size, SQ_Size))

def DrawMoves(gs, screen):
    CircleColor1 = (180, 180, 180, 128)
    CircleColor2 = (200, 200, 200, 128)
    for SQ in gs.LegalMovesWithSelectedPiece:
        if gs.Board[SQ[0]*8 + SQ[1]] == 0:
            if gs.PlayerColor == "White":
                pygame.gfxdraw.filled_circle(screen, (SQ[1]*SQ_Size + SQ_Size//2), (SQ[0]*SQ_Size + SQ_Size//2), SQ_Size*20//100, CircleColor1)
            elif gs.PlayerColor == "Black":
                pygame.gfxdraw.filled_circle(screen, ((7 - SQ[1])*SQ_Size + SQ_Size//2), ((7 - SQ[0])*SQ_Size + SQ_Size//2), SQ_Size*20//100, CircleColor1)
        elif gs.Board[SQ[0]*8 + SQ[1]] != 0:
            if gs.PlayerColor == "White":
                pg.draw.circle(screen, CircleColor2, (SQ[1] * SQ_Size + SQ_Size // 2, SQ[0] * SQ_Size + SQ_Size // 2), SQ_Size * 4 // 10, SQ_Size//10)
            elif gs.PlayerColor == "Black":
                pg.draw.circle(screen, CircleColor2, ((7 - SQ[1]) * SQ_Size + SQ_Size // 2, (7 - SQ[0]) * SQ_Size + SQ_Size // 2), SQ_Size * 4 // 10, SQ_Size // 10)

def DrawMenu(gs, screen, Buttons):
    StartButton = Buttons[0]
    ResignButton = Buttons[1]
    RematchButton = Buttons[2]
    if not GameOngoing:
        StartButton.Draw(screen)

        if gs.GameEnded:
            WindowRect = pg.Rect(TableWidth//4, TableHeight//4, TableHeight // 2, TableWidth // 2)
            WindowColor = (255, 255, 255, 80)
            pg.draw.rect(screen, WindowColor, WindowRect)

            if gs.Mated[0] or gs.Mated[1]:
                text = Winner + "won by checkmate"
                font = pg.font.Font(None, 24)
                text_surface = font.render(text, True, [0, 0, 0, 255])
                text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                screen.blit(text_surface, text_rect)

            elif gs.StaleMated:
                text = "Draw by Stalemate"
                font = pg.font.Font(None, 24)
                text_surface = font.render(text, True, [0, 0, 0, 255])
                text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                screen.blit(text_surface, text_rect)

            elif gs.Resigned:
                if gs.PlayerColor == "White":
                    text = "Black won by resignation"
                    font = pg.font.Font(None, 24)
                    text_surface = font.render(text, True, [0, 0, 0, 255])
                    text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                    screen.blit(text_surface, text_rect)

                if gs.PlayerColor == "Black":
                    text = "White won by resignation"
                    font = pg.font.Font(None, 24)
                    text_surface = font.render(text, True, [0, 0, 0, 255])
                    text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                    screen.blit(text_surface, text_rect)

            elif gs.FiftyRuleDraw:
                text = "Draw by fifty move rule"
                font = pg.font.Font(None, 24)
                text_surface = font.render(text, True, [0, 0, 0, 255])
                text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                screen.blit(text_surface, text_rect)

            elif gs.DrawByRepetition:
                text = "Draw by repetition"
                font = pg.font.Font(None, 24)
                text_surface = font.render(text, True, [0, 0, 0, 255])
                text_rect = text_surface.get_rect(center=(TableWidth * 50 // 100, TableHeight * 3 // 8))
                screen.blit(text_surface, text_rect)

            RematchButton.Draw(screen)

    elif GameOngoing:
        ResignButton.Draw(screen)

def DrawPromotionOptions(screen, pos, color):
    x, y = pos
    whitepieces = [12, 13, 14, 16]
    blackpieces = [-12, -13, -14, -16]
    if color == 1:
        for i, piece in enumerate(whitepieces):
            pg.draw.rect(screen, [255, 255, 255], pg.Rect(TableWidth//2 - SQ_Size//2, TableHeight//2 + (i-2)*SQ_Size, SQ_Size, SQ_Size))
            pg.draw.rect(screen, [0, 0, 0], pg.Rect(TableWidth // 2 - SQ_Size // 2, TableHeight // 2 + (i - 2) * SQ_Size, SQ_Size, SQ_Size), 2)
            screen.blit(pg.transform.scale(pg.image.load("Images/" + str(piece) + ".png"), (SQ_Size, SQ_Size)), (TableWidth//2 - SQ_Size//2, TableHeight//2 + (i-2)*SQ_Size))
    if color == -1:
        for i, piece in enumerate(blackpieces):
            pg.draw.rect(screen, [255, 255, 255], pg.Rect(TableWidth//2 - SQ_Size//2, TableHeight//2 + (i-2)*SQ_Size, SQ_Size, SQ_Size))
            pg.draw.rect(screen, [0, 0, 0], pg.Rect(TableWidth // 2 - SQ_Size // 2, TableHeight // 2 + (i - 2) * SQ_Size, SQ_Size, SQ_Size), 2)
            screen.blit(pg.transform.scale(pg.image.load("Images/" + str(piece) + ".png"), (SQ_Size, SQ_Size)), (TableWidth//2 - SQ_Size//2, TableHeight//2 + (i-2)*SQ_Size))


def HighLightSquare(screen, row, col):
    HighLightColors = [[200, 200, 200], [100, 140, 100]]
    HighColor = HighLightColors[(row + col) % 2]
    pg.draw.rect(screen, HighColor, pg.Rect(col * SQ_Size, row * SQ_Size, SQ_Size, SQ_Size))

def EndTheGame(Mated):
    global GameEnded
    global GameOngoing
    global Winner
    GameOngoing = False
    GameEnded = True
    if Mated[0]:
        Winner = "Black"
    elif Mated[1]:
        Winner = "White"
    elif not Mated[0] and not Mated[1]:
        pass




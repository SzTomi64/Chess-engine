import numpy as np
import time
import random
#import torch
#import torchvision
#import matplotlib.pyplot as plt
#from torchvision import datasets, transforms
#from torch import nn, optim
import copy

#from Chess import ChessFunctions
import ChessFunctions
import pygame as pg

#from Chess.chess_functions import fen_to_tensor
from chess_functions import fen_to_tensor
from ChessFunctions import TableWidth, TableHeight, SQ_Size, MAX_FPS
import itertools
import ChessBot

x_sq = list(itertools.product(range(8), range(8)))

class GameState():
    #White = 1, Black = 2,
    #Pawn = 1, Knight = 2, Bishop = 3, Rook = 4, King = 5, Queen = 6
    #Empty = 0
    def __init__(self, PlayerColor):
        self.PlayerColor = PlayerColor
        self.Board =[
            -14, -12, -13, -16, -15, -13, -12, -14,
            -11, -11, -11, -11, -11, -11, -11, -11,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            11, 11, 11, 11, 11, 11, 11, 11,
            14, 12, 13, 16, 15, 13, 12, 14]
        self.WhiteToMove = True
        self.MoveLog = []
        self.SelectedPiece = ()
        self.VisionOfPiece = []
        self.LegalMovesWithSelectedPiece = []
        self.WhiteInCheck = False
        self.BlackInCheck = False
        self.CastlingEnabled = [True, True, True, True]
        self.EnPassantEnabled = False
        self.EnPassantEnabledFor = []
        self.GameEnded = False
        self.Mated = [False, False]
        self.StaleMated = False
        self.Resigned = False
        self.Promoting = False
        self.PromotingTo = None
        self.FiftyRuleCount = 0
        self.FiftyRuleDraw = False
        self.DrawByRepetition = False
    def Copy(self):
        gs = GameState("White")
        gs.PlayerColor = self.PlayerColor
        gs.Board = copy.copy(self.Board)
        gs.WhiteToMove = copy.copy(self.WhiteToMove)
        gs.SelectedPiece = copy.copy(self.SelectedPiece)
        gs.VisionOfPiece = copy.deepcopy(self.VisionOfPiece)
        gs.WhiteInCheck = copy.copy(self.WhiteInCheck)
        gs.BlackInCheck = copy.copy(self.BlackInCheck)
        gs.CastlingEnabled = copy.copy(self.CastlingEnabled)
        gs.EnPassantEnabled = copy.copy(self.EnPassantEnabled)
        gs.EnPassantEnabledFor = copy.copy(self.EnPassantEnabledFor)
        gs.FiftyRuleCount = copy.copy(self.FiftyRuleCount)
        gs.FiftyRuleDraw = copy.copy(self.FiftyRuleDraw)
        gs.GameEnded = copy.copy(self.GameEnded)
        return gs

    def board_to_fen(self):
        piece_map = {
            0: '',
            11: 'P', 12: 'N', 13: 'B', 14: 'R', 15: 'K', 16: 'Q',
            -11: 'p', -12: 'n', -13: 'b', -14: 'r', -15: 'k', -16: 'q'
        }
        rows = []
        for i in range(8):
            row = self.Board[i * 8:(i + 1) * 8]
            fen_row = ''
            empty_count = 0
            for cell in row:
                if cell == 0:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece_map[cell]
            if empty_count > 0:
                fen_row += str(empty_count)
            rows.append(fen_row)

        active_color = 'w' if self.WhiteToMove else 'b'

        castling = ''
        if self.CastlingEnabled[0]:
            castling += 'K'
        if self.CastlingEnabled[1]:
            castling += 'Q'
        if self.CastlingEnabled[2]:
            castling += 'k'
        if self.CastlingEnabled[3]:
            castling += 'q'
        if not castling:
            castling = '-'

        en_passant = '-'

        return f"{'/'.join(rows)} {active_color} {castling} {en_passant}"

    def UpdateGS(self, TargetSQ):
        x, y = self.SelectedPiece
        piecetype = self.Board[x*8 + y]
        target = self.Board[TargetSQ[0]*8 + TargetSQ[1]]

        #Tracking the Fifty move rule
        if piecetype == 11 or piecetype == -11:
            self.FiftyRuleCount = 0
        elif target != 0:
            self.FiftyRuleCount = 0
        else:
            self.FiftyRuleCount += 1

        # Tracks if moves by the king and rooks will disable future castling opportunities
        if self.SelectedPiece == (7, 7) or TargetSQ == (7, 7):
            self.CastlingEnabled[0] = False
        if self.SelectedPiece == (7, 0) or TargetSQ == (7, 0):
            self.CastlingEnabled[1] = False
        if self.SelectedPiece == (0, 7) or TargetSQ == (0, 7):
            self.CastlingEnabled[2] = False
        if self.SelectedPiece == (0, 0) or TargetSQ == (0, 0):
            self.CastlingEnabled[3] = False
        if piecetype == 15:
            self.CastlingEnabled[0] = False
            self.CastlingEnabled[1] = False
        if piecetype == -15:
            self.CastlingEnabled[2] = False
            self.CastlingEnabled[3] = False

        # Enabling en passant
        if piecetype == 11:
            if self.SelectedPiece[0] == 6 and TargetSQ[0] == 4:
                self.EnPassantEnabled = True
                self.EnPassantEnabledFor = [-1, (5, self.SelectedPiece[1])]
            else:
                self.EnPassantEnabled = False
                self.EnPassantEnabledFor = []
        elif piecetype == -11:
            if self.SelectedPiece[0] == 1 and TargetSQ[0] == 3:
                self.EnPassantEnabled = True
                self.EnPassantEnabledFor = [1, (2, self.SelectedPiece[1])]
            else:
                self.EnPassantEnabled = False
                self.EnPassantEnabledFor = []
        else:
            self.EnPassantEnabled = False
            self.EnPassantEnabledFor = []

        #short castling with white
        if piecetype == 15 and (self.SelectedPiece[0], self.SelectedPiece[1] + 2) == TargetSQ:
            self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
            self.Board[TargetSQ[0]*8 + TargetSQ[1] - 1] = self.Board[7*8 + 7]
            self.Board[7*8 + 7] = 0
            self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            self.CastlingEnabled[0] = False
            self.CastlingEnabled[1] = False
        #long castle with white
        elif piecetype == 15 and (self.SelectedPiece[0], self.SelectedPiece[1] - 2) == TargetSQ:
            self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
            self.Board[TargetSQ[0]*8 + TargetSQ[1] + 1] = self.Board[7*8 + 0]
            self.Board[7*8 + 0] = 0
            self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            self.CastlingEnabled[0] = False
            self.CastlingEnabled[1] = False
        #short castle with black
        elif piecetype == -15 and (self.SelectedPiece[0], self.SelectedPiece[1] + 2) == TargetSQ:
            self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
            self.Board[TargetSQ[0]*8 + TargetSQ[1] - 1] = self.Board[0*8 + 7]
            self.Board[0*8 + 7] = 0
            self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            self.CastlingEnabled[2] = False
            self.CastlingEnabled[3] = False
        #long castle with black
        elif piecetype == -15 and (self.SelectedPiece[0], self.SelectedPiece[1] - 2) == TargetSQ:
            self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
            self.Board[TargetSQ[0]*8 + TargetSQ[1] + 1] = self.Board[0*8 + 0]
            self.Board[0*8 + 0] = 0
            self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            self.CastlingEnabled[2] = False
            self.CastlingEnabled[3] = False


        #EnPassant and Promotion
        elif piecetype == 11:
            if self.Promoting:
                self.Board[TargetSQ[0]*8 +TargetSQ[1]] = self.PromotingTo
                self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                self.Promoting = False
                self.PromotingTo = None
            elif (self.SelectedPiece[0] - 1, self.SelectedPiece[1] - 1) == TargetSQ:
                if self.Board[TargetSQ[0]*8 + TargetSQ[1]] == 0 and self.SelectedPiece[0] == 3:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]-1] = 0
                else:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            elif (self.SelectedPiece[0] - 1, self.SelectedPiece[1] + 1) == TargetSQ:
                if self.Board[TargetSQ[0]*8 + TargetSQ[1]] == 0 and self.SelectedPiece[0] == 3:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]+1] = 0
                else:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            else:
                self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0

        elif piecetype == -11:
            if self.Promoting:
                self.Board[TargetSQ[0]*8 + TargetSQ[1]] = self.PromotingTo
                self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                self.Promoting = False
                self.PromotingTo = None
            elif (self.SelectedPiece[0] + 1, self.SelectedPiece[1] - 1) == TargetSQ:
                if self.Board[TargetSQ[0]*8 + TargetSQ[1]] == 0 and self.SelectedPiece[0] == 4:
                    self.Board[TargetSQ[0]*8 +TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]-1] = 0
                else:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            elif (self.SelectedPiece[0] + 1, self.SelectedPiece[1] + 1) == TargetSQ:
                if self.Board[TargetSQ[0]*8 + TargetSQ[1]] == 0 and self.SelectedPiece[0] == 4:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]+1] = 0
                else:
                    self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                    self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0
            else:
                self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
                self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0

        #Standard moves
        else:
            self.Board[TargetSQ[0]*8 + TargetSQ[1]] = piecetype
            self.Board[self.SelectedPiece[0]*8 + self.SelectedPiece[1]] = 0

        if self.WhiteToMove:
            self.IsBlackInCheck()
        elif not self.WhiteToMove:
            self.IsWhiteInCheck()

        # Passes the turn to the opponent
        if self.WhiteToMove:
            self.WhiteToMove = False
        else:
            self.WhiteToMove = True

    def ProbeSQ(self, row, col):
        if not self.SelectedPiece:
            if self.WhiteToMove and self.Board[row*8 + col] > 0:
                self.SelectedPiece = (row, col)
                self.VisionOfPiece = []
                self.FindLegalMovesWithSelectedPiece()

            if not self.WhiteToMove and self.Board[row*8 + col] < 0:
                self.SelectedPiece = (row, col)
                self.VisionOfPiece = []
                self.FindLegalMovesWithSelectedPiece()
            else:
                pass

        elif self.SelectedPiece:
            if self.IsItLegalMove(row, col):
                self.UpdateGS((row, col))
                self.IsItCheckOrStalemate2()
                #self.IsItStaleMate()
                self.SelectedPiece = ()
                self.VisionOfPiece = []
                self.LegalMovesWithSelectedPiece = []

            elif self.Board[row*8 + col] == 0:
                self.SelectedPiece = ()
                self.VisionOfPiece = []
                self.LegalMovesWithSelectedPiece = []

            elif self.Board[row*8 + col] > 0 and self.WhiteToMove:
                self.SelectedPiece = (row, col)
                self.VisionOfPiece = []
                self.FindLegalMovesWithSelectedPiece()

            elif self.Board[row*8 + col] < 0 and not self.WhiteToMove:
                self.SelectedPiece = (row, col)
                self.VisionOfPiece = []
                self.FindLegalMovesWithSelectedPiece()

    def FindVisionOfPiece(self, r, c):
        self.VisionOfPiece = []
        #Knights work well
        if self.Board[r*8 + c] == 12 or self.Board[r*8 + c] == -12: # If the selected piece is a white knight
            self.VisionOfPiece = [(r-2, c-1), (r-2, c+1), (r-1, c-2), (r-1, c+2), (r+1, c-2), (r+1, c+2), (r+2, c-1), (r+2, c+1)]
            self.VisionOfPiece = [t for t in self.VisionOfPiece if t[0] <= 7 and t[0] >= 0 and t[1] <= 7 and t[1] >= 0]

        elif self.Board[r*8 + c] == 11:  # If the selected piece is a white pawn
            if r-1 >= 0:
                if self.Board[(r-1)*8 + c] == 0:
                    self.VisionOfPiece.append((r-1, c))
            if r-2 >= 0:
                if self.Board[(r-2)*8 + c] == 0 and r == 6:
                    self.VisionOfPiece.append((r-2, c))

            self.VisionOfPiece.append((r-1, c+1))
            self.VisionOfPiece.append((r-1, c-1))

            self.VisionOfPiece = [t for t in self.VisionOfPiece if t[0] <= 7 and t[0] >= 0 and t[1] <= 7 and t[1] >= 0]
        elif self.Board[r*8 + c] == -11:  # If the selected piece is a black pawn
            if r+1 <= 7:
                if self.Board[(r+1)*8 + c] == 0:
                    self.VisionOfPiece.append((r+1, c))
            if r+2 <= 7:
                if self.Board[(r+2)*8 + c] == 0 and r == 1:
                    self.VisionOfPiece.append((r+2, c))

            self.VisionOfPiece.append((r+1, c+1))
            self.VisionOfPiece.append((r+1, c-1))

            self.VisionOfPiece = [t for t in self.VisionOfPiece if t[0] <= 7 and t[0] >= 0 and t[1] <= 7 and t[1] >= 0]

        #Bishops should work fine
        elif self.Board[r*8 + c] == 13 or self.Board[r*8 + c] == -13: # If Selected Piece is a white bishop
            iter = [1, 2, 3, 4, 5, 6, 7, 8]
            for k in iter:
                if r-k >= 0 and c-k >= 0:
                    if self.Board[(r-k)*8 + (c-k)] != 0:
                        self.VisionOfPiece.append((r-k, c-k))
                        break
                    else:
                        self.VisionOfPiece.append((r-k, c-k))

            for k in iter:
                if r-k >= 0 and c+k <= 7:
                    if self.Board[(r-k)*8 + (c+k)] != 0:
                        self.VisionOfPiece.append((r-k, c+k))
                        break
                    else:
                        self.VisionOfPiece.append((r-k, c+k))

            for k in iter:
                if r+k <= 7 and c-k >= 0:
                    if self.Board[(r+k)*8 + (c-k)] != 0:
                        self.VisionOfPiece.append((r+k, c-k))
                        break
                    else:
                        self.VisionOfPiece.append((r+k, c-k))

            for k in iter:
                if r+k <= 7 and c+k <= 7:
                    if self.Board[(r+k)*8 + (c+k)] != 0:
                        self.VisionOfPiece.append((r+k, c+k))
                        break
                    else:
                        self.VisionOfPiece.append((r+k, c+k))

        #Rooks should work fine
        elif self.Board[r*8 + c] == 14 or self.Board[r*8 + c] == -14: # White rook
            iter = [1, 2, 3, 4, 5, 6, 7, 8]

            for k in iter:
                if r - k >= 0:
                    if self.Board[(r - k)*8 + c] != 0:
                        self.VisionOfPiece.append((r - k, c))
                        break
                    else:
                        self.VisionOfPiece.append((r - k, c))

            for k in iter:
                if r + k <= 7:
                    if self.Board[(r + k)*8 + c] != 0:
                        self.VisionOfPiece.append((r + k, c))
                        break
                    else:
                        self.VisionOfPiece.append((r + k, c))

            for k in iter:
                if c - k >= 0:
                    if self.Board[r*8 + (c - k)] != 0:
                        self.VisionOfPiece.append((r, c - k))
                        break
                    else:
                        self.VisionOfPiece.append((r, c - k))

            for k in iter:
                if c + k <= 7:
                    if self.Board[r*8 + (c + k)] != 0:
                        self.VisionOfPiece.append((r, c + k))
                        break
                    else:
                        self.VisionOfPiece.append((r, c + k))

        #Queens should be fine
        elif self.Board[r*8 + c] == 16 or self.Board[r*8 + c] == -16: #White Queen
            iter = [1, 2, 3, 4, 5, 6, 7, 8]
            for k in iter:
                if r - k >= 0 and c - k >= 0:
                    if self.Board[(r - k)*8 + (c - k)] != 0:
                        self.VisionOfPiece.append((r - k, c - k))
                        break
                    else:
                        self.VisionOfPiece.append((r - k, c - k))

            for k in iter:
                if r - k >= 0 and c + k <= 7:
                    if self.Board[(r - k)*8 + (c + k)] != 0:
                        self.VisionOfPiece.append((r - k, c + k))
                        break
                    else:
                        self.VisionOfPiece.append((r - k, c + k))

            for k in iter:
                if r + k <= 7 and c - k >= 0:
                    if self.Board[(r + k)*8 + (c - k)] != 0:
                        self.VisionOfPiece.append((r + k, c - k))
                        break
                    else:
                        self.VisionOfPiece.append((r + k, c - k))

            for k in iter:
                if r + k <= 7 and c + k <= 7:
                    if self.Board[(r + k)*8 + (c + k)] != 0:
                        self.VisionOfPiece.append((r + k, c + k))
                        break
                    else:
                        self.VisionOfPiece.append((r + k, c + k))
            for k in iter:
                if r - k >= 0:
                    if self.Board[(r - k)*8 + c] != 0:
                        self.VisionOfPiece.append((r - k, c))
                        break
                    else:
                        self.VisionOfPiece.append((r - k, c))

            for k in iter:
                if r + k <= 7:
                    if self.Board[(r + k)*8 + c] != 0:
                        self.VisionOfPiece.append((r + k, c))
                        break
                    else:
                        self.VisionOfPiece.append((r + k, c))

            for k in iter:
                if c - k >= 0:
                    if self.Board[r*8 + (c - k)] != 0:
                        self.VisionOfPiece.append((r, c - k))
                        break
                    else:
                        self.VisionOfPiece.append((r, c - k))

            for k in iter:
                if c + k <= 7:
                    if self.Board[r*8 + (c + k)] != 0:
                        self.VisionOfPiece.append((r, c + k))
                        break
                    else:
                        self.VisionOfPiece.append((r, c + k))

        elif self.Board[r*8 + c] == 15 or self.Board[r*8 + c] == -15: #white king
            self.VisionOfPiece = [(r-1, c), (r-1, c-1), (r, c-1), (r+1, c-1), (r+1, c), (r+1, c+1), (r, c+1), (r-1, c+1)]
            self.VisionOfPiece = [t for t in self.VisionOfPiece if t[0] <= 7 and t[0] >= 0 and t[1] <= 7 and t[1] >= 0]

    def FindLegalMovesWithSelectedPiece(self):
        self.LegalMovesWithSelectedPiece = []
        self.FindVisionOfPiece(self.SelectedPiece[0], self.SelectedPiece[1])
        PotentialMoves = copy.deepcopy(self.VisionOfPiece)
        if self.WhiteToMove:
            PotentialMoves = [k for k in PotentialMoves if self.Board[k[0]*8 + k[1]] < 1]
        elif self.WhiteToMove == False:
            PotentialMoves = [k for k in PotentialMoves if self.Board[k[0]*8 + k[1]] > -1]


        x, y = self.SelectedPiece
        piecetype = self.Board[x*8 + y]

        if piecetype == 11: #Checking if there is a piece for a pawn to take
            if x-1 >= 0 and y-1 >= 0:
                if self.Board[(x-1)*8 + (y-1)] == 0:
                    if (x-1, y-1) in PotentialMoves:
                        if self.EnPassantEnabled and self.EnPassantEnabledFor[0] == 1:
                            if (x-1, y-1) == self.EnPassantEnabledFor[1]:
                                pass
                            else:
                                PotentialMoves.remove((x - 1, y - 1))
                        else:
                            PotentialMoves.remove((x - 1, y - 1))
            if x - 1 >= 0 and y + 1 <= 7:
                if self.Board[(x-1)*8 + (y+1)] == 0:
                    if (x - 1, y + 1) in PotentialMoves:
                        if self.EnPassantEnabled and self.EnPassantEnabledFor[0] == 1:
                            if (x - 1, y + 1) == self.EnPassantEnabledFor[1]:
                                pass
                            else:
                                PotentialMoves.remove((x-1, y+1))
                        else:
                            PotentialMoves.remove((x - 1, y+1))
            if x == 6:
                if self.Board[(x - 2)*8 + y] != 0 or self.Board[(x - 1)*8 + y]:
                    if (x-2, y) in PotentialMoves:
                        PotentialMoves.remove((x - 2, y))

        elif piecetype == -11:
            if x + 1 <= 7 and y - 1 >= 0:
                if self.Board[(x+1)*8 + (y-1)] == 0:
                    if (x + 1, y - 1) in PotentialMoves:
                        if self.EnPassantEnabled and self.EnPassantEnabledFor[0] == -1:
                            if (x + 1, y - 1) == self.EnPassantEnabledFor[1]:
                                pass
                            else:
                                PotentialMoves.remove((x+1, y-1))
                        else:
                            PotentialMoves.remove((x + 1, y - 1))
            if x + 1 <= 7 and y + 1 <= 7:
                if self.Board[(x+1)*8 + (y+1)] == 0:
                    if (x + 1, y + 1) in PotentialMoves:
                        if self.EnPassantEnabled and self.EnPassantEnabledFor[0] == -1:
                            if (x + 1, y + 1) == self.EnPassantEnabledFor[1]:
                                pass
                            else:
                                PotentialMoves.remove((x+1, y+1))
                        else:
                            PotentialMoves.remove((x + 1, y + 1))
            if x == 1:
                if self.Board[(x + 2)*8 + y] != 0 or self.Board[(x + 1)*8 + y]:
                    if (x+2, y) in PotentialMoves:
                        PotentialMoves.remove((x + 2, y))

        #short and long castle by white
        elif piecetype == 15:
            VisionOfEnemy = self.FindVisionOfColor(-1)
            if self.CastlingEnabled[0] and not self.WhiteInCheck:
                if self.Board[x*8 + (y + 1)] == 0:
                    if self.Board[x*8 + (y + 2)] == 0:
                        if (x, y+1) not in VisionOfEnemy:
                            if (x, y + 2) not in VisionOfEnemy:
                                PotentialMoves.append((x, y + 2))

            if self.CastlingEnabled[1] and not self.WhiteInCheck:
                if self.Board[x*8 + (y - 1)] == 0:
                    if self.Board[x*8 + (y - 2)] == 0:
                        if self.Board[x*8 + (y - 3)] == 0:
                            if (x, y-1) not in VisionOfEnemy:
                                if (x, y - 2) not in VisionOfEnemy:
                                    PotentialMoves.append((x, y - 2))
        # short and long castle by black
        elif piecetype == -15:
            VisionOfEnemy = self.FindVisionOfColor(1)
            if self.CastlingEnabled[2] and not self.BlackInCheck:
                if self.Board[x*8 + (y + 1)] == 0:
                    if self.Board[x*8 + (y + 2)] == 0:
                        if (x, y + 1) not in VisionOfEnemy:
                            if (x, y + 2) not in VisionOfEnemy:
                                PotentialMoves.append((x, y + 2))

            if self.CastlingEnabled[3] and not self.BlackInCheck:
                if self.Board[x*8 + (y - 1)] == 0:
                    if self.Board[x*8 + (y - 2)] == 0:
                        if self.Board[x*8 + (y - 3)] == 0:
                            if (x, y - 1) not in VisionOfEnemy:
                                if (x, y - 2) not in VisionOfEnemy:
                                    PotentialMoves.append((x, y - 2))

        for k in PotentialMoves:
            gs_fut = self.Copy()
            gs_fut.UpdateGS(k)
            if self.WhiteToMove:
                gs_fut.IsWhiteInCheck()
                if not gs_fut.WhiteInCheck:
                    self.LegalMovesWithSelectedPiece.append(k)
            elif not self.WhiteToMove:
                gs_fut.IsBlackInCheck()
                if not gs_fut.BlackInCheck:
                    self.LegalMovesWithSelectedPiece.append(k)

    def IsWhiteInCheck(self):
        KinglocWhite = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] == 15]
        KinglocWhite = KinglocWhite[0]
        if KinglocWhite in self.FindVisionOfColor(-1):
            self.WhiteInCheck = True
        else:
            self.WhiteInCheck = False

    def IsBlackInCheck(self):
        KinglocBlack = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] == -15]
        KinglocBlack = KinglocBlack[0]
        if KinglocBlack in self.FindVisionOfColor(1):
            self.BlackInCheck = True
        else:
            self.BlackInCheck = False

    def FindVisionOfColor(self, color):

        Vision = []
        if color > 0:
            Pieceloc = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] > 0]
            for (r, c) in Pieceloc:
                self.FindVisionOfPiece(r, c)
                for (row, col) in self.VisionOfPiece:
                    Vision.append((row, col))
            VisionUnique = []
            for x in Vision:
                if x not in VisionUnique:
                    VisionUnique.append(x)
            VisionUnique.sort()
            return VisionUnique

        if color < 0:
            Pieceloc = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] < 0]
            for (r, c) in Pieceloc:
                self.FindVisionOfPiece(r, c)
                for (row, col) in self.VisionOfPiece:
                    Vision.append((row, col))
            VisionUnique = []
            for x in Vision:
                if x not in VisionUnique:
                    VisionUnique.append(x)
            VisionUnique.sort()
            return VisionUnique

    def IsItLegalMove(self, row, col):
        if (row, col) in self.LegalMovesWithSelectedPiece:
            return True

        else:
            return False

    def IsItCheckOrStalemate2(self):
        if self.WhiteToMove:
            Pieceloc = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] > 0]
            for (r, c) in Pieceloc:
                gs_test = self.Copy()
                gs_test.SelectedPiece = (r, c)
                gs_test.FindLegalMovesWithSelectedPiece()
                if gs_test.LegalMovesWithSelectedPiece:
                    return False

            if self.WhiteInCheck:
                self.Mated[0] = True
                self.GameEnded = True
                return True
            else:
                self.StaleMated = True
                self.GameEnded = True
                return True

        else:
            Pieceloc = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] < 0]
            for (r, c) in Pieceloc:
                gs_test = self.Copy()
                gs_test.SelectedPiece = (r, c)
                gs_test.FindLegalMovesWithSelectedPiece()
                if gs_test.LegalMovesWithSelectedPiece:
                    return False

            if self.BlackInCheck:
                self.Mated[1] = True
                self.GameEnded = True
                return True
            else:
                self.StaleMated = True
                self.GameEnded = True
                return True

    def IsGameOver(self):
        #self.IsItCheckOrStalemate2()
        if self.Mated[0] or self.Mated[1]:
            self.GameEnded = True
            return True
        elif self.StaleMated:
            self.GameEnded = True
            return True
        elif self.FiftyRuleCount >= 100:
            self.GameEnded = True
            return True
        else:
            return False

    #Here comes the hard territory, coding the ChessBot.
    #An evaluation function that takes a snapshot of the current gamestate,
    #and gives it a rating without looking at future moves.
    #TODO FindLegalMoves and IsItCheckOrStalemate both screw up castling
    def GeneratePotentialBoards(self):


        x = range(8)
        FutureBoards = []

        piece_filter = (lambda sq: self.Board[sq[0]*8 + sq[1]] > 0) if self.WhiteToMove else (lambda sq: self.Board[sq[0]*8 + sq[1]] < 0)
        Pieceloc = [sq for sq in x_sq if piece_filter(sq)]
        for (r, c) in Pieceloc:
            gs_test = self.Copy()
            gs_test.SelectedPiece = (r, c)
            gs_test.FindLegalMovesWithSelectedPiece()
            piece = gs_test.Board[r*8 + c]
            is_pawn_promotion = (piece == 11 and gs_test.WhiteToMove) or (piece == -11 and not gs_test.WhiteToMove)
            promotion_row = 0 if gs_test.WhiteToMove else 7
            promotions = [12, 13, 14, 16] if gs_test.WhiteToMove else [-12, -13, -14, -16]
            for (row, col) in gs_test.LegalMovesWithSelectedPiece:
                gs_fut = gs_test.Copy()
                if is_pawn_promotion and row == promotion_row:
                    for prom in promotions:
                        gs_fut.Promoting = True
                        gs_fut.PromotingTo = prom
                        gs_fut.UpdateGS((row, col))
                        gs_fut.IsItCheckOrStalemate2()
                        FutureBoards.append(gs_fut)
                else:
                    gs_fut.UpdateGS((row, col))
                    gs_fut.IsItCheckOrStalemate2()
                    FutureBoards.append(gs_fut)
        return FutureBoards

    def StaticEval(self, Bot):

        if self.Mated[0]:
            return -np.inf
        elif self.Mated[1]:
            return np.inf
        elif self.StaleMated:
            return 0

        else:
            fen = self.board_to_fen()
            input = fen_to_tensor(fen)
            eval = Bot.model(input).item()
            return eval
        #else:
        #    eval = 0
        #    x = range(8)
        #    Pieceloc = [SQ for SQ in x_sq if self.Board[SQ[0]*8 + SQ[1]] != 0]
        #    for piece in Pieceloc:
        #        piecetype = self.Board[piece[0]*8 + piece[1]]
        #        piecesign = np.sign(piecetype)
        #        eval += Bot.Values(piecetype)[0]*piecesign
        #        self.FindVisionOfPiece(piece[0], piece[1])
        #        eval += Bot.Values(piecetype)[1]*len(self.VisionOfPiece)*piecesign
            return eval
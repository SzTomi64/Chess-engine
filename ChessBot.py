import pygame
import numpy as np
import time
#import torch
#import torchvision
#import matplotlib.pyplot as plt
#from torchvision import datasets, transforms
#from torch import nn, optim
import ChessEngine
import ChessFunctions
from chess_functions import *

class Bot():
    def __init__(self):
        self.eval = 0
        self.model = Eval_function(784)
        self.model.load_state_dict(torch.load('eval_model.pt'))
        self.model.eval()

        #Initial PieceValues for pawns, knights, bishops, rooks and queens
        #ActivityValues will be based on the amount of squares the piece sees
        #AttackValues will depend on how much PieceValue a given piece targets
        #DefenseValues will depend on how much PieceValue a given piece protects
        #self.PieceValues = [1, 3, 3, 5, 9, 1000]
        #self.ActivityValues = [0, 0.05, 0.05, 0.1, 0.05, 0]
        #self.AttackValues = [0, 0, 0, 0, 0, 0]
        #self.DefenseValues = [0, 0, 0, 0, 0, 0]

    #def StaticEval(self, ListGS):
    #    StatEvals = []
    #    #Ide kerül Tomi Evalja
    #    for i in range(len(ListGS)):
    #        if ListGS[i].Mated[0]:
    #            StatEvals[i] = -np.inf
    #        elif ListGS[i].Mated[1]:
    #            StatEvals[i] = np.inf
    #        elif ListGS[i].StaleMated:
    #            StatEvals[i] = 0
    #    return StatEvals

    def minimax(self, gs, depth, alpha, beta):
        if depth == 0 or gs.IsGameOver():
            x = gs.StaticEval(self)
            return x

        if gs.WhiteToMove:
            maxeval = -np.inf
            Children = gs.GeneratePotentialBoards()

            for child in Children:
                eval = self.minimax(child, depth - 1, alpha, beta)
                maxeval = max(maxeval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return maxeval

        else:
            mineval = np.inf
            Children = gs.GeneratePotentialBoards()
            for child in Children:
                eval = self.minimax(child, depth - 1, alpha, beta)
                mineval = min(mineval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return mineval

    def FindBestMove(self, gs, depth):
        best_move = None
        if gs.WhiteToMove:
            maxeval = -np.inf
            children = gs.GeneratePotentialBoards()
            for child in children:
                eval = self.minimax(child, depth - 1, -np.inf, np.inf)
                if eval > maxeval:
                    maxeval = eval
                    best_move = child
        else:
            mineval = np.inf
            children = gs.GeneratePotentialBoards()
            for child in children:
                eval = self.minimax(child, depth - 1, -np.inf, np.inf)
                if eval < mineval:
                    mineval = eval
                    best_move = child
        return best_move

    def Values(self, Piece):
        Values = []
        if Piece == 11 or Piece == -11:
            Values.append(self.PieceValues[0])
            Values.append(self.ActivityValues[0])
            Values.append(self.AttackValues[0])
            Values.append(self.DefenseValues[0])

        elif Piece == 12 or Piece == -12:
            Values.append(self.PieceValues[1])
            Values.append(self.ActivityValues[1])
            Values.append(self.AttackValues[1])
            Values.append(self.DefenseValues[1])

        elif Piece == 13 or Piece == -13:
            Values.append(self.PieceValues[2])
            Values.append(self.ActivityValues[2])
            Values.append(self.AttackValues[2])
            Values.append(self.DefenseValues[2])

        elif Piece == 14 or Piece == -14:
            Values.append(self.PieceValues[3])
            Values.append(self.ActivityValues[3])
            Values.append(self.AttackValues[3])
            Values.append(self.DefenseValues[3])

        elif Piece == 16 or Piece == -16:
            Values.append(self.PieceValues[4])
            Values.append(self.ActivityValues[4])
            Values.append(self.AttackValues[4])
            Values.append(self.DefenseValues[4])

        elif Piece == 15 or Piece == -15:
            Values.append(self.PieceValues[5])
            Values.append(self.ActivityValues[5])
            Values.append(self.AttackValues[5])
            Values.append(self.DefenseValues[5])

        return Values
import io
import pandas as pd
import zstandard as zst
import json
import numpy as np
import torch
from torch.optim import Adam
from tqdm import tqdm
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import torch.nn as nn
import copy


def read_jsonl_zst(file_path, from_i):
    with open(file_path, 'rb') as file:
        decompressor = zst.ZstdDecompressor()
        stream_reader = decompressor.stream_reader(file)
        stream = io.TextIOWrapper(stream_reader, encoding = "utf-8")
        i = -1
        for line in stream:
            i+=1
            if i >= from_i*1000000 and i<(from_i+1)*1000000: 
                yield json.loads(line)
            elif i>=(from_i+1)*1000000:
                break

class Chess_dataset(Dataset):
    def __init__(self, data, transform):
        self.data = data
        self.transform = transform

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, ind):
        position = self.data.iloc[ind, 0]
        position = self.transform(position)
        label = float(self.data.iloc[ind, 1])
        return position, torch.tensor(label/100)

def pos_cp(df):
    for i in range(len(df)):
        pos = df.iloc[i, 0]
        cp = 1000
        if 'cp' in df.iloc[i, 1][0]['pvs'][0].keys():
            cp = df.iloc[i, 1][0]['pvs'][0]['cp']
        elif df.iloc[i, 1][0]['pvs'][0]['mate']<0:
            cp = -1000
        yield pos, cp

    
def one_hot_fen(fen):
    pieces = {"P":"110000000000", "N":"001100000000", "B":"000011000000", "R":"000000110000", "Q":"000000001100", "K":"000000000011",
              "p":"-1-10000000000", "n":"00-1-100000000", "b":"0000-1-1000000", "r":"000000-1-10000", "q":"00000000-1-100", "k":"0000000000-1-1"}
    castle_dict = {"KQkq":"11111111",
              "KQk":"11111100",
              "KQq":"11110011",
              "Kkq":"11001111",
              "Qkq":"00111111",
              "KQ":"11110000",
              "Kk":"11001100",
              "Kq":"11000011",
              "Qk":"00111100",
              "Qq":"00110011",
              "kq":"00001111",
              "K":"11000000",
              "Q":"00110000",
              "k":"00001100",
              "q":"00000011",
              "-":"00000000"}
    one_hot = ""
    space_1 = fen.index(" ")
    fen_pos = fen[:space_1]
    move = fen[space_1+1]
    space_3 = space_1+3+fen[space_1+3:].index(" ")
    castle = fen[space_1+3:space_3]

    for letter in fen_pos:
        if letter.isdigit():
            one_hot += int(letter)*12*"0"
        elif letter !="/":
            one_hot += pieces[letter]
    
    if move == "w":
        one_hot += "11111111"
    else:
        one_hot += "-1-1-1-1-1-1-1-1"

    if castle in castle_dict.keys():
        one_hot += castle_dict[castle]
    else:
        one_hot += "00000000"

    return one_hot

def fen_to_tensor(fen):
    onehot = one_hot_fen(fen)
    vect = []
    sign = 0
    for item in onehot:
        if item == "-":
            sign = 1
        elif sign == 1:
            vect.append(-float(item))
            sign = 0
        else:
            vect.append(float(item))
    return torch.tensor(vect)

class Eval_function(nn.Module):
    def __init__(self, in_features):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Sigmoid(),
            nn.Linear(128, 32),
            nn.Sigmoid(),
            nn.Linear(32, 32),
            nn.Sigmoid(),
            nn.Linear(32, 1)
        )
    
    def __call__(self, x):
        return self.forward(x)
    
    def forward(self, x):
        x = self.layers(x)
        return x

def train_loop(model, optimizer, num_epochs, train_loader, val_loader, device, criterion):
    model.to(device)
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0

        loop = tqdm(enumerate(train_loader), total=len(train_loader), leave=False)

        for i, (data, targets) in loop:
            data, targets = data.to(device), targets.to(device).unsqueeze(dim = 1)
            
            outputs = model(data)
            loss = criterion(outputs, targets)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            loop.set_description(f"Epoch [{epoch+1}/{num_epochs}]")
            loop.set_postfix(loss=running_loss/(i+1))
        
        # Print average loss for the epoch
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/(i+1):.4f}")

        eval_loop(model, val_loader, device, criterion)


def eval_loop(model, val_loader, device, criterion):
    model.to(device)
    model.eval()
    loop = tqdm(enumerate(val_loader), total=len(val_loader), leave=False)
    running_loss = 0

    for j, (data, targets) in loop:
        data, targets = data.to(device), targets.to(device).unsqueeze(dim = 1)
            
        outputs = model(data)
        loss = criterion(outputs, targets)
            
        running_loss += loss.item()

        loop.set_postfix(loss=running_loss/(j+1))

    print(f"Loss: {running_loss/(j+1):.4f}")

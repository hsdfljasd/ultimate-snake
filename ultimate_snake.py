from random import *
import numpy as np
from copy import deepcopy
import math
import pygame
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, InputLayer
from tensorflow.keras.optimizers import Adam
from tkinter import *
import shelve

pygame.font.init()

def next_page(speed):
    global mainframe, FPS
    FPS = speed
    mainframe.destroy()
    mainframe = Frame(root)
    mainframe.place(relwidth=1, relheight=1)
    Label(mainframe, text="Выбери противника", font=("Arial", 16)).place(relwidth=1, relheight=0.4)
    Button(mainframe, text="Слабоумный Снейки", font=("Arial", 6), command = lambda: transit_to_game(0)).place(rely = 0.5, relx = 0.05, relwidth = 0.2, relheight=0.1)
    Button(mainframe, text="Снейкус Сойдётус", font=("Arial", 6), command = lambda:  transit_to_game(1)).place(rely = 0.5, relx = 0.25+1/30, relwidth = 0.2, relheight=0.1)
    Button(mainframe, text="Снейкус Приспособленнус", font=("Arial", 6), command = lambda: transit_to_game(2)).place(rely = 0.5, relx = 0.45+2/30, relwidth = 0.2, relheight=0.1)
    Button(mainframe, text="Северус Снейк", font=("Arial", 6), command = lambda: transit_to_game(3)).place(rely = 0.5, relx = 0.75, relwidth = 0.2, relheight=0.1)

def transit_to_game(opponent):
    global complexity
    complexity = opponent
    root.destroy()

padx = 0.06666666666666667
root = Tk()
root.geometry("450x450")
mainframe = Frame(root)
mainframe.place(relwidth=1, relheight=1)
Label(mainframe, text="Выбери скорость игры", font=("Arial", 16)).place(relwidth=1, relheight=0.4)
Button(mainframe, text="Низкая\n3 FPS", font=("Arial", 10), command = lambda: next_page(3)).place(rely = 0.5, relx = 0.1, relwidth = 0.15, relheight=0.1)
Button(mainframe, text="Средняя\n6 FPS", font=("Arial", 10), command = lambda: next_page(6)).place(rely = 0.5, relx = 0.25+padx, relwidth = 0.15, relheight=0.1)
Button(mainframe, text="Высокая\n10 FPS", font=("Arial", 10), command = lambda: next_page(10)).place(rely = 0.5, relx = 0.4+padx*2, relwidth = 0.15, relheight=0.1)
Button(mainframe, text="Я киборг\n15 FPS", font=("Arial", 10), command = lambda: next_page(15)).place(rely = 0.5, relx = 0.75, relwidth = 0.15, relheight=0.1)
root.mainloop()

width, height = 10, 10
tile = 50
W, H = tile * width, tile * height

QNetwork = Sequential()
QNetwork.add(InputLayer(input_shape=(10, )))
QNetwork.add(Dense(64, activation='relu'))
QNetwork.add(Dense(4,  activation='linear'))
QNetwork.compile(loss='mse', optimizer=Adam(learning_rate=0.0005))

storage = shelve.open("qsnake")
QNetwork.set_weights(storage["weights" + str(complexity)])

surface = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

def DetectCollision(x, y):
    if x < 0 or x >= W or y < 0 or y >= H:
        return True
    for bodyX, bodyY in body:
        if x == bodyX and bodyY-tile/2 <= y <= bodyY+tile/2:
            return True
        if y == bodyY and bodyX-tile/2 <= x <= bodyX + tile/2:
            return True
    for bodyX, bodyY in body2:
        if x == bodyX and bodyY-tile/2 <= y <= bodyY+tile/2:
            return True
        if y == bodyY and bodyX-tile/2 <= x <= bodyX + tile/2:
            return True
    return False
        

def ray_casting(x, y, angle):
    cos = math.cos(angle)
    sin = math.sin(angle)
    if abs(cos) > abs(sin):
        dx = tile * cos / abs(cos)
        dy = sin * tile
    else:
        dx = cos * tile
        dy = tile * sin / abs(sin)
    X, Y = x, y
    while True:
        X += dx
        Y += dy
        if DetectCollision(X, Y):
            dist = ((X - x)**2 + (Y-y)**2)**0.5
            return dist

def get_input(x, y, t):
    input_layer = []
    for i in range(8):
        angle = math.pi/4*i
        dist = ray_casting(x, y, angle)
        input_layer.append(dist / tile)
    if t == 0:
        input_layer += [(apple_x - body[-1][0]) / tile, (apple_y - body[-1][1])/tile]
    else:
        input_layer += [(apple_x - body2[-1][0]) / tile, (apple_y - body2[-1][1])/tile]
    return input_layer

def get_random_place():
    while True:
        x, y = randrange(width) * tile + tile//2, randrange(height) * tile + tile//2
        if not DetectCollision(x, y):
            return x, y

epoch = []
epoch2 = []

body = []
body2 = []
while True:
    X, Y = get_random_place()
    if X - 3*tile > 0:
        break
while True:
    X2, Y2 = get_random_place()
    if X2 - 3*tile > 0:
        break
body = list(reversed([(X, Y), (X-tile, Y), (X -2*tile, Y), (X - 3*tile, Y)]))
body2 = list(reversed([(X2, Y2), (X2-tile, Y2), (X2 -2*tile, Y2), (X2 - 3*tile, Y2)]))
apple_x, apple_y = get_random_place()
cur_action = 2
actions = (-1, 0), (0, -1), (1, 0), (0, 1)
eaten = 0
hungry = 0
eaten2 = hungry2 = 0
good_moves_combo = 0
dist_to_apple = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
next_state = next_state2 = None
pdx, pdy = 1, 0
score1 = score2 = 0
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            quit()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_a:
                pdx = -1
                pdy = 0
            elif e.key == pygame.K_d:
                pdx = 1
                pdy = 0
            elif e.key == pygame.K_w:
                pdx = 0
                pdy = -1
            elif e.key == pygame.K_s:
                pdx = 0
                pdy = 1
    
    state = get_input(X, Y, 0)
    array = QNetwork.predict([state], batch_size=1, verbose=0)[0]
    action = np.argmax(array)
    dx, dy = actions[action]
    X += dx * tile
    Y += dy * tile
    if X == apple_x and Y == apple_y:
        apple_x, apple_y = get_random_place()
        body.append((X, Y))
        score1 += 1
    elif DetectCollision(X, Y):
        score1 = 0
        while True:
            X, Y = get_random_place()
            if X - 3*tile > 0 and abs(Y - Y2) >= 2*tile:
                break
        body = list(reversed([(X, Y), (X-tile, Y), (X -2*tile, Y), (X - 3*tile, Y)]))
    else:
        body.append((X, Y))
        del body[0]

    X2 += pdx * tile
    Y2 += pdy * tile
    if X2 == apple_x and Y2 == apple_y:
        apple_x, apple_y = get_random_place()
        body2.append((X2, Y2))
        score2 += 1
    elif DetectCollision(X2, Y2):
        score2 = 0
        pdx, pdy = 1, 0
        while True:
            X2, Y2 = get_random_place()
            if X2 - 3*tile > 0:
                break
        body2 = list(reversed([(X2, Y2), (X2-tile, Y2), (X2 -2*tile, Y2), (X2 - 3*tile, Y2)]))
    else:
        body2.append((X2, Y2))
        del body2[0]

    surface.fill('white')
    for x, y in body:
        pygame.draw.rect(surface, "blue", (x - tile/2, y - tile/2, tile, tile))
    for x, y in body2:
        pygame.draw.rect(surface, "green", (x - tile/2, y - tile/2, tile, tile))
    pygame.draw.rect(surface, "red", (apple_x - tile/2, apple_y - tile/2, tile, tile))

    f1 = pygame.font.Font(None, 36)
    text1 = f1.render(str(score1), True,
                  "blue")
    surface.blit(text1, (10, 10))

    f1 = pygame.font.Font(None, 36)
    text1 = f1.render(str(score2), True,
                  "green")
    surface.blit(text1, (400, 10))
    
    pygame.display.update()
    
    clock.tick(FPS)

    if score1 == 10 or score2 == 10:
        break

surface.fill("black")
if score1 == 10:
    t = "Вы проиграли"
else:
    t = "Вы выиграли"
f1 = pygame.font.Font(None, 72)
text1 = f1.render(t, True,
              "red")
surface.blit(text1, ((W - text1.get_rect().width) / 2, H/2))
pygame.display.update()

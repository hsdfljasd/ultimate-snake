from random import *
import numpy as np
import math
from copy import deepcopy
import pygame
from tensorflow.keras import Model, Sequential
from tensorflow.keras.layers import Dense, InputLayer
from tensorflow.keras.optimizers import Adam
import shelve

width, height = 10, 10
tile = 50
W, H = tile * width, tile * height
maxdist = (W**2 + H ** 2)**0.5
gamma = 0.99

batchsize = 128

def train(epoch, n):
    if n == 1:
        smpl = sample(epoch, batchsize)
        target = QNetwork.predict(np.array([x[0] for x in smpl]), batch_size=batchsize, verbose=0)
        t = TargetNetwork.predict(np.array([x[1] for x in smpl]), batch_size=batchsize, verbose=0)
        for i in range(batchsize):
            action = smpl[i][2]
            reward = smpl[i][3]
            if reward >= 100 or reward <= -10:
                target[i][action] = reward
            else:
                target[i][action] = reward + gamma * np.amax(t[i])
        QNetwork.fit(np.array([x[0] for x in smpl]), target, epochs = 1, verbose=False if randrange(20) else True, batch_size = batchsize)
    else:
        smpl = sample(epoch2, batchsize)
        target = QNetwork2.predict(np.array([x[0] for x in smpl]), batch_size=batchsize, verbose=0)
        t = TargetNetwork2.predict(np.array([x[1] for x in smpl]), batch_size=batchsize, verbose=0)
        for i in range(batchsize):
            action = smpl[i][2]
            reward = smpl[i][3]
            if reward >= 100 or reward <= -10:
                target[i][action] = reward
            else:
                target[i][action] = reward + gamma * np.amax(t[i])
        QNetwork2.fit(np.array([x[0] for x in smpl]), target, epochs = 1, verbose=False if randrange(20) else True, batch_size = batchsize)

QNetwork = Sequential()
QNetwork.add(InputLayer(input_shape=(10, )))
QNetwork.add(Dense(64, activation='relu'))
QNetwork.add(Dense(4,  activation='linear'))
QNetwork.compile(loss='mse', optimizer=Adam(learning_rate=0.0005))

TargetNetwork = Sequential()
TargetNetwork.add(InputLayer(input_shape=(10, )))
TargetNetwork.add(Dense(64, activation='relu'))
TargetNetwork.add(Dense(4,  activation='linear'))
TargetNetwork.compile(loss='mse', optimizer=Adam(learning_rate=0.0005))

QNetwork2 = Sequential()
QNetwork2.add(InputLayer(input_shape=(10, )))
QNetwork2.add(Dense(64, activation='relu'))
QNetwork2.add(Dense(4,  activation='linear'))
QNetwork2.compile(loss='mse', optimizer=Adam(learning_rate=0.0005))

TargetNetwork2 = Sequential()
TargetNetwork2.add(InputLayer(input_shape=(10, )))
TargetNetwork2.add(Dense(64, activation='relu'))
TargetNetwork2.add(Dense(4,  activation='linear'))
TargetNetwork2.compile(loss='mse', optimizer=Adam(learning_rate=0.0005))

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

for ep in range(10):
    for step in range(10):
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
        for k in range(10000):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    quit()

            if min(hungry, hungry2) >= 100:
                apple_x, apple_y = get_random_place()
                hungry = hungry2 = 0
            
            if next_state != None:
                state = deepcopy(next_state)
            else:
                state = get_input(X, Y, 0)
            array = QNetwork.predict([state], batch_size=1, verbose=0)[0]
            s = sum([math.e**x for x in array])
            probabs = [math.e**x/s for x in array]
            x = randrange(1000000)
            summ=0
            for i in range(4):
                if x < summ+probabs[i]*1000000:
                    action = i
                    break
                summ += probabs[i]*1000000
            dx, dy = actions[action]
            X += dx * tile
            Y += dy * tile
            if X == apple_x and Y == apple_y:
                apple_x, apple_y = get_random_place()
                body.append((X, Y))
                eaten += 1
                hungry = 0
                reward = 3.5*eaten**0.5
                TargetNetwork.set_weights(QNetwork.get_weights())
                dist_to_apple = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                good_moves_combo += 1
            elif DetectCollision(X, Y):
                if k < 15:
                    reward = -100
                else:
                    reward = -10
                while True:
                    X, Y = get_random_place()
                    if X - 3*tile > 0:
                        break
                body = list(reversed([(X, Y), (X-tile, Y), (X -2*tile, Y), (X - 3*tile, Y)]))
                dist_to_apple = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                cur_action = 2
                eaten = 0
                good_moves_combo = 0
            else:
                hungry += 1
                body.append((X, Y))
                del body[0]
                dta = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                reward = -0.25

            if next_state2 != None:
                state2 = deepcopy(next_state2)
            else:
                state2 = get_input(X2, Y2, 1)
            array = QNetwork2.predict([state2], batch_size=1, verbose=0)[0]
            s = sum([math.e**x for x in array])
            probabs = [math.e**x/s for x in array]
            x = randrange(1000000)
            summ=0
            for i in range(4):
                if x < summ+probabs[i]*1000000:
                    action2 = i
                    break
                summ += probabs[i]*1000000
            dx, dy = actions[action2]
            X2 += dx * tile
            Y2 += dy * tile
            if X2 == apple_x and Y2 == apple_y:
                apple_x, apple_y = get_random_place()
                body2.append((X2, Y2))
                eaten2 += 1
                hungry2 = 0
                reward2 = 3.5*eaten2**0.5
                TargetNetwork2.set_weights(QNetwork2.get_weights())
                dist_to_apple = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                good_moves_combo += 1
            elif DetectCollision(X2, Y2):
                if k < 15:
                    reward2 = -100
                else:
                    reward2 = -10
                while True:
                    X2, Y2 = get_random_place()
                    if X2 - 3*tile > 0:
                        break
                body2 = list(reversed([(X2, Y2), (X2-tile, Y2), (X2 -2*tile, Y2), (X2 - 3*tile, Y2)]))
                dist_to_apple = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                cur_action = 2
                eaten2 = 0
                good_moves_combo = 0
            else:
                hungry2 += 1
                body2.append((X2, Y2))
                del body2[0]
                dta = ((X - apple_x)**2 + (Y-apple_y)**2)**0.5
                reward2 = -0.25

            next_state2 = get_input(X2, Y2, 1)
            epoch2.append([state2, next_state2, action2, reward2])
            if (len(epoch2) > 2000):
                del epoch2[0]
            if len(epoch2) > batchsize:
                train(epoch2, 2)

            next_state = get_input(X, Y, 0)
            epoch.append([state, next_state, action, reward])
            if (len(epoch) > 2000):
                del epoch[0]
            if len(epoch) > batchsize:
                train(epoch, 1)

            surface.fill('white')
            for x, y in body:
                pygame.draw.rect(surface, "blue", (x - tile/2, y - tile/2, tile, tile))
            for x, y in body2:
                pygame.draw.rect(surface, "green", (x - tile/2, y - tile/2, tile, tile))
            pygame.draw.rect(surface, "red", (apple_x - tile/2, apple_y - tile/2, tile, tile))
            
            pygame.display.update()
            clock.tick(60)

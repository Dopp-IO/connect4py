import sys
import re
# import time

#this is how boards are indexed
#  | 0 1 2 3 4 5 6 | 
#  | 7 8 . . . x x | 
#  | x x x x x x x | 
#  | x x x x x x x | 
#  | x x x x x x x | 
#  | x x x x . . n | 
# -------------------

#board dimensions
#can be adapted to other sizes
BOARD_HEIGHT = 6
BOARD_WIDTH = 7

#store the value of already seen boards
BOARDCACHE = dict()
#store the results of already computed regex searches
SEARCHCACHERED = dict()
SEARCHCACHEYELLOW = dict()

#read cache from disk
if "clearcache" not in sys.argv[1:]:
    try:
        bcachefile = open("c4bcache.txt", "r")
        srcachefile = open("c4rcache.txt", "r")
        sycachefile = open("c4ycache.txt", "r")

        for entry in bcachefile.readlines():
            entry.replace("\n", "")
            data = entry.split(":")
            BOARDCACHE[data[0]] = int(data[1])

        for entry in srcachefile.readlines():
            entry.replace("\n", "")
            data = entry.split(":")
            SEARCHCACHERED[data[0]] = int(data[1])

        for entry in sycachefile.readlines():
            entry.replace("\n", "")
            data = entry.split(":")
            SEARCHCACHEYELLOW[data[0]] = int(data[1])

        bcachefile.close()
        srcachefile.close()
        sycachefile.close()
    except:
        print("Cache is missing or corrupt. New cache will be written at end of game.")
else:
    print("Cache will not be read from file. New cache will be overwritten at end of game.")

#tokens to connect
WINTOKENS = 4

#tokens
OPEN = "-"
RED = "@"
YELLOW = "x"

#color codes
regcolor = "\033[39;49m"
redcolor = "\033[40;101m"
yelcolor = "\033[40;103m"

EMPTY = "".join(["-" for i in range(BOARD_WIDTH * BOARD_HEIGHT)])

#global lookup tables
horizontals = dict()
verticals = dict()
#\
diagonalsfor = dict()
#/
diagonalsback = dict()

#generate forward diagonal
def genfordiagonal(idx):
    while idx // BOARD_WIDTH != 0 and idx % BOARD_WIDTH != 0:
        idx = idx - BOARD_WIDTH - 1
    diags = [idx]
    while idx // BOARD_WIDTH != BOARD_HEIGHT - 1 and idx % BOARD_WIDTH != BOARD_WIDTH - 1:
        idx = idx + BOARD_WIDTH + 1
        diags.append(idx)
    return diags
    
#generate backward diagonal
def genbackdiagonal(idx):
    while idx // BOARD_WIDTH != 0 and idx % BOARD_WIDTH != BOARD_WIDTH - 1:
        idx = idx - BOARD_WIDTH + 1
    diags = [idx]
    while idx // BOARD_WIDTH != BOARD_HEIGHT - 1 and idx % BOARD_WIDTH != 0:
        idx = idx + BOARD_WIDTH - 1
        diags.append(idx)
    return diags

#generate lookups
for i in range(BOARD_HEIGHT * BOARD_WIDTH):
    horizontals[i] = [j for j in range(i//BOARD_WIDTH*BOARD_WIDTH, i//BOARD_WIDTH*BOARD_WIDTH+BOARD_WIDTH)]
    verticals[i] = [j for j in range(i%BOARD_WIDTH, BOARD_WIDTH * BOARD_HEIGHT, BOARD_WIDTH)]
    diagonalsfor[i] = genfordiagonal(i)
    diagonalsback[i] = genbackdiagonal(i)

def colorprocessor(toprocess):
    toreturn = ""
    for s in toprocess:
        if s == RED:
            toreturn = toreturn + redcolor + s
        elif s == YELLOW:
            toreturn = toreturn + yelcolor + s
        else:
            toreturn = toreturn + regcolor + s
    return toreturn

def printbrd(brd, indent):
    for i in range(BOARD_HEIGHT):
        toprint = " | " + " ".join(brd[i*BOARD_WIDTH:i*BOARD_WIDTH+BOARD_WIDTH]) + " | "
        toprint = colorprocessor(toprint)
        if indent:
            print("     " + toprint)
        else:
            print(toprint)
    if indent:
        print("     ---" + "-".join([str(i) for i in range(BOARD_WIDTH)]) + "---")
    else:
        print("---" + "-".join([str(i) for i in range(BOARD_WIDTH)]) + "---")

#takes a board, token to play and column. plays token into that column and returns resulting board
def playcol(brd, tok, col):
    idx = col
    while brd[idx] == OPEN:
        idx = idx + BOARD_WIDTH
        if idx > BOARD_HEIGHT * BOARD_WIDTH - 1:
            break
    idx = idx - BOARD_WIDTH
    if idx < 0:
        return
    return "".join([brd[i] if i != idx else tok for i in range(len(brd))])

#returns boards of all possible places a token could go
def moves(brd, tok):
    return [playcol(brd, tok, i) for i in range(BOARD_WIDTH)]

#positive if favoring red, negative if favoring yellow
def boardvalue(brd):
    if brd in BOARDCACHE:
        return BOARDCACHE[brd]
    val = 0
    slices = []
    #add horizontal slices
    for i in range(BOARD_HEIGHT):
        slices.append("".join([brd[j] for j in horizontals[i*BOARD_WIDTH]]))
    #add vertical slices
    for i in range(BOARD_WIDTH):
        slices.append("".join([brd[j] for j in verticals[i]]))
    #add forward diagonal slices
    for i in range(BOARD_WIDTH):
        slices.append("".join([brd[j] for j in diagonalsfor[i]]))
    for i in range(1, BOARD_HEIGHT):
        slices.append("".join([brd[j] for j in diagonalsfor[i*BOARD_WIDTH]]))
    #add backward diagonal slices
    for i in range(BOARD_WIDTH):
        slices.append("".join([brd[j] for j in diagonalsback[i]]))
    for i in range(1, BOARD_HEIGHT):
        slices.append("".join([brd[j] for j in diagonalsback[i*BOARD_WIDTH + BOARD_WIDTH - 1]]))

    for sl in slices:
        if sl in SEARCHCACHERED:
            result = SEARCHCACHERED[sl]
            val = val + result
        else:
            result = re.match(".*[@O-]{4,}", sl)
            if result:
                val = val + result.span()[1] - result.span()[0]
                SEARCHCACHERED[sl] = result.span()[1] - result.span()[0]
            else:
                SEARCHCACHERED[sl] = 0

        if sl in SEARCHCACHEYELLOW:
            result = SEARCHCACHEYELLOW[sl]
            val = val - result
        else:
            result = re.match(".*[x-]{4,}", sl)
            if result:
                val = val - result.span()[1] + result.span()[0]
                SEARCHCACHEYELLOW[sl] = result.span()[1] - result.span()[0]
            else:
                SEARCHCACHEYELLOW[sl] = 0

        #look for connect 4s
        result = re.match(".*@@@@", sl)
        if result:
            val = val + 10000
        
        result = re.match(".*xxxx", sl)
        if result:
            val = val - 10000

    BOARDCACHE[brd] = val

    return val

#find the best move for the given player
#returns [move, value]
def minimax(brd, depth, alpha, beta, token):
    if depth == 0 or abs(boardvalue(brd)) > 5000:
        return [-1, boardvalue(brd)]
    
    #if trying to maximize board value
    if token == RED:
        bestmove = -1
        maxeval = -100000
        for play in range(BOARD_WIDTH):
            playedbrd = playcol(brd, token, play)
            if playedbrd == None:
                continue
            mm = minimax(playedbrd, depth - 1, alpha, beta, YELLOW if token == RED else RED)
            if mm[1] > maxeval:
                maxeval = mm[1]
                bestmove = play
            alpha = max(alpha, maxeval)
            if beta <= alpha:
                break
        return [bestmove, maxeval]
    else:
        bestmove = -1
        mineval = 100000
        for play in range(BOARD_WIDTH):
            playedbrd = playcol(brd, token, play)
            if playedbrd == None:
                continue
            mm = minimax(playedbrd, depth - 1, alpha, beta, YELLOW if token == RED else RED)
            if mm[1] < mineval:
                mineval = mm[1]
                bestmove = play
            beta = min(beta, mineval)
            if beta <= alpha:
                break
        return [bestmove, mineval]

#game logic
newbrd = EMPTY
current = YELLOW if "com" in sys.argv[1:] else RED
gameover = False
while gameover == False:
    if current == RED:
        mmresult = minimax(newbrd, 7, -100000, 100000, current)
        if mmresult[0] == -1:
            print("Game over, I win")
            gamover = True
            break
        print("Your move:")
        result = playcol(newbrd, current, int(input()))
        while result == None:
            print("Invalid move, try again")
            result = playcol(newbrd, current, int(input()))
        print("You played:")
        printbrd(result, False)
        newbrd = result
        current = YELLOW
    else:
        mmresult = minimax(newbrd, 8, -100000, 100000, current)
        if mmresult[0] == -1:
            print("Good game, you win")
            gameover = True
            break
        newbrd = playcol(newbrd, current, mmresult[0])
        print("I play column " + str(mmresult[0]))
        printbrd(newbrd, True)
        current = RED

#write caches to disk
bcachefile = open("c4bcache.txt", "w+")
srcachefile = open("c4rcache.txt", "w+")
sycachefile = open("c4ycache.txt", "w+")

bcachefile.seek(0)
srcachefile.seek(0)
sycachefile.seek(0)

bcachefile.writelines([entry + ":" + str(BOARDCACHE[entry]) + "\n" for entry in BOARDCACHE])
srcachefile.writelines([entry + ":" + str(SEARCHCACHERED[entry]) + "\n" for entry in SEARCHCACHERED])
sycachefile.writelines([entry + ":" + str(SEARCHCACHEYELLOW[entry]) + "\n" for entry in SEARCHCACHEYELLOW])

bcachefile.truncate()
srcachefile.truncate()
sycachefile.truncate()

bcachefile.close()
srcachefile.close()
sycachefile.close()
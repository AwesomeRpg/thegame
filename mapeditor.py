#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A level designer for the game Star Pusher by Al Sweigart from his book
'Making Games with Python & Pygame'
http://inventwithpython.com/pygame/chapters/
"""
import pygame, sys, os, copy, logging, pprint
from pygame.locals import *

# logging.basicConfig(filename='logFile.txt', level=logging.DEBUG,
                    # format='%(asctime)s - %(levelname)s - %(message)s')
                    
FPS = 30 # frames per second to update the screen
WINDOWWIDTH = 600 # width of the program's window, in pixels
WINDOWHEIGHT = 600 # height in pixels
BOARDWIDTH = 15 # number of tiles per column
BOARDHEIGHT = 15 # number of tiles per row
MARGIN = 10
TILESIZE = 60
CAMERAMOVEMENT = 1
CAMERAMARGIN = 10

CAM_MOVE_SPEED = 5 # how many pixels per frame the camera moves

BRIGHTBLUE  = (  0, 170, 255)
WHITE       = (255, 255, 255)
DARKGRAY    = ( 40,  40,  40)
BLUE        = (  0,  50, 255)
YELLOW      = (255, 255,   0)
BGCOLOR     = BRIGHTBLUE
TEXTCOLOR   = WHITE
HIGHLIGHTCOLOR = BLUE
WALLCOLOR   = YELLOW


def main():
    global DISPLAYSURF, OBJECTIMAGES, IMAGESDICT, MOUSEIMAGES, BASICFONT
    # set initial position of the game window
    os.environ['SDL_VIDEO_WINDOW_POS'] = "40,40"
    pygame.init()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Star Pusher Editor')
    saveFile = 'userMaps.txt'
    currentLvl = 0
    mouseX = 0
    mouseY = 0
    mouseImageX = 0
    mouseImageY = 0
    leftButtonClicked = False
    rightButtonClicked = False
    # set up camera
    cameraX = 0
    cameraY = 0
    cameraLeft = False
    cameraRight = False
    cameraUp = False
    cameraDown = False
    mapWidth = BOARDWIDTH * TILESIZE
    mapHeight = BOARDHEIGHT * TILESIZE
    MAXCAMXPAN = abs(int(WINDOWWIDTH / 2) - int(mapHeight / 2)) + 50
    MAXCAMYPAN = abs(int(WINDOWHEIGHT / 2) - int(mapWidth / 2)) + 50
    
    objectIter = 0
    # read map file
    levels = readLevelsFile(saveFile)
    if levels == []:
        currentLvl = 0
        mapTiles = [[None] * BOARDHEIGHT for i in range(BOARDWIDTH)]
    else:
        currentLvl = 1
        mapTiles = convertToTiles(levels[currentLvl-1])
    
    # image dictionaries
    OBJECTIMAGES = ['#', '$', '@', '.']
    IMAGESDICT = {'uncovered goal': pygame.image.load('img\RedSelector.png'),
                  'star': pygame.image.load('img\Star.png'),
                  'wall': pygame.image.load('img\Wall_Block_Tall.png'),
                  'princess': pygame.image.load('img\princess.png')}
    MOUSEIMAGES = [IMAGESDICT['wall'],
                    IMAGESDICT['star'],
                    IMAGESDICT['princess'],
                    IMAGESDICT['uncovered goal']]
    
    while True:
        DISPLAYSURF.fill(BGCOLOR)
        
        # draw tile outlines        
        mapSurfWidth = BOARDWIDTH * TILESIZE + 1
        mapSurfHeight = BOARDHEIGHT * TILESIZE + 1
        mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
        mapSurf.fill(BGCOLOR) # start with a blank color on the surface.
                        
        for x in range(0, (BOARDWIDTH + 1) * TILESIZE, TILESIZE):
            pygame.draw.line(mapSurf, DARKGRAY, (x, 0), 
                (x, mapHeight))
        for y in range(0, (BOARDHEIGHT + 1) * TILESIZE, TILESIZE):
            pygame.draw.line(mapSurf, DARKGRAY, (0, y), 
                (mapWidth, y))
                
        # draw tiles
        for tileX in range(BOARDWIDTH):
            for tileY in range(BOARDHEIGHT):
                left, top = leftTopCoordsTile(tileX, tileY)
                if mapTiles[tileX][tileY] == '#':
                    pygame.draw.rect(mapSurf, WALLCOLOR, (left, top, 
                                     TILESIZE, TILESIZE))
                elif mapTiles[tileX][tileY] != None:
                    imgRect = pygame.Rect((tileX * TILESIZE, 
                                           tileY * TILESIZE, 
                                           TILESIZE, TILESIZE))
                    if mapTiles[tileX][tileY] == '$':
                        mapSurf.blit(IMAGESDICT['star'], imgRect)
                    elif mapTiles[tileX][tileY] == '@':
                        mapSurf.blit(IMAGESDICT['princess'], imgRect)
                    elif mapTiles[tileX][tileY] == '.':
                        mapSurf.blit(IMAGESDICT['uncovered goal'], imgRect)
                
        # Adjust mapSurf's Rect object based on the camera offset.
        mapSurfRect = mapSurf.get_rect()
        mapSurfRect.center = (int(WINDOWWIDTH / 2) + cameraX, int(WINDOWHEIGHT / 2) - cameraY)
        logging.info('mapSurfRect.center=' + str(mapSurfRect.center))
        logging.info('mapSurfRect.topleft=' + str(mapSurfRect.topleft))
        logging.info('left, top=' + str(mapSurfRect.left) + ', ' + str(mapSurfRect.top))

        # Draw mapSurf to the DISPLAYSURF Surface object.
        DISPLAYSURF.blit(mapSurf, mapSurfRect)
        
        # draw level marker
        levelSurf = BASICFONT.render('Level %s of %s' % (currentLvl, len(levels)), 1, TEXTCOLOR)
        levelRect = levelSurf.get_rect()
        levelRect.bottomleft = (20, WINDOWHEIGHT - 35)
        
        # event handler
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_DELETE: # delete current level
                    if levels != []:
                        del levels[currentLvl-1]
                        print updateSaveFile(saveFile, levels)
                        if levels == []:
                            currentLvl = 0
                            mapTiles = [[None] * BOARDHEIGHT for i in range(BOARDWIDTH)]
                        else:
                            currentLvl = 1
                            mapTiles = convertToTiles(levels[currentLvl-1])
                elif event.key == K_n: # add new level
                    currentLvl = 0
                    mapTiles = [[None] * BOARDHEIGHT for i in range(BOARDWIDTH)]
                elif event.key == K_s: # save current level
                    printMsg, currentLvl = saveToFile(saveFile, mapTiles, currentLvl)
                    levels = readLevelsFile(saveFile)
                elif event.key == K_PAGEUP: # go to previous map
                    if levels != []:
                        if currentLvl <= 1:
                            currentLvl = len(levels)
                        else: 
                            currentLvl -= 1
                        mapTiles = convertToTiles(levels[currentLvl-1])
                elif event.key == K_PAGEDOWN: # go to next map
                    if levels != []:
                        if currentLvl >= len(levels):
                            currentLvl = 1
                        else: 
                            currentLvl += 1
                        mapTiles = convertToTiles(levels[currentLvl-1])
            elif event.type == MOUSEBUTTONUP:
                clickX, clickY = event.pos
                if (mapSurfRect.right > clickX > mapSurfRect.left and
                   mapSurfRect.bottom > clickY > mapSurfRect.top):
                    if event.button == 5:
                        objectIter -= 1
                        if objectIter < 0:
                            objectIter = len(OBJECTIMAGES) - 1
                    elif event.button == 4:
                        objectIter += 1
                        if objectIter >= len(OBJECTIMAGES):
                            objectIter = 0
                    elif event.button == 1:
                        leftButtonClicked = True
                    elif event.button == 3:
                        rightButtonClicked = True
            elif event.type == MOUSEMOTION:
                mouseX, mouseY = event.pos
                if  (mouseX > WINDOWWIDTH - CAMERAMARGIN and mouseX < WINDOWWIDTH - 1 and 
                    mouseY > CAMERAMARGIN and mouseY < WINDOWHEIGHT - CAMERAMARGIN):
                    cameraRight = True
                elif (mouseX < CAMERAMARGIN and mouseX > 0 and
                    mouseY > CAMERAMARGIN and mouseY < WINDOWHEIGHT - CAMERAMARGIN):
                    cameraLeft = True
                elif (mouseY < CAMERAMARGIN and mouseY > 0 and
                    mouseX > CAMERAMARGIN and mouseX < WINDOWWIDTH - CAMERAMARGIN):
                    cameraUp = True
                elif (mouseY > WINDOWHEIGHT - CAMERAMARGIN and mouseY < WINDOWHEIGHT - 1 and
                    mouseX > CAMERAMARGIN and mouseX < WINDOWWIDTH - CAMERAMARGIN):
                    cameraDown = True
                else:
                    cameraRight = False
                    cameraLeft = False
                    cameraUp = False
                    cameraDown = False
 
        # move camera
        if cameraRight and cameraX > -MAXCAMYPAN:
            cameraX -= CAMERAMOVEMENT
        elif cameraLeft and cameraX < MAXCAMYPAN:
            cameraX += CAMERAMOVEMENT
        elif cameraUp and cameraY > -MAXCAMXPAN:
            cameraY -= CAMERAMOVEMENT
        elif cameraDown and cameraY < MAXCAMXPAN:
            cameraY += CAMERAMOVEMENT            
                
        # draw events at mouse position
        mapMouseX = mouseX - mapSurfRect.left
        mapMouseY = mouseY - mapSurfRect.top
        tileX, tileY = getTileAtPixel(mapMouseX, mapMouseY)
        if tileX != None:
            drawHighlightTile(tileX, tileY, mapSurf)
            mouseImageX = mapMouseX - (MOUSEIMAGES[objectIter].get_width() / 2)
            mouseImageY = mapMouseY - (MOUSEIMAGES[objectIter].get_height() / 2)
            mapSurf.blit(MOUSEIMAGES[objectIter], (mouseImageX,mouseImageY))
            if leftButtonClicked:
                mapTiles[tileX][tileY] = OBJECTIMAGES[objectIter]
                leftButtonClicked = False
            if rightButtonClicked:
                mapTiles[tileX][tileY] = None
                rightButtonClicked = False
                                
        DISPLAYSURF.blit(mapSurf, mapSurfRect)
        DISPLAYSURF.blit(levelSurf, levelRect)
        pygame.display.update()

        
def leftTopCoordsTile(tilex, tiley):
    '''
    returns left and top pixel coords
    tilex: int
    tiley: int
    return: tuple (int, int)
    '''
    left = tilex * TILESIZE
    top = tiley * TILESIZE
    return (left, top)

    
def getTileAtPixel(x, y):
    '''
    returns tile coordinates of pixel at top left, defaults to (None, None)
    x: int
    y: int
    return: tuple (tilex, tiley)
    '''
    # assert(1==2) # need to tie Rect to mapSurf instead of window
    for tilex in range(BOARDWIDTH):
        for tiley in range(BOARDHEIGHT):
            left, top = leftTopCoordsTile(tilex, tiley)
            tile_rect = pygame.Rect(left, top, TILESIZE, TILESIZE)
            if tile_rect.collidepoint(x, y):
                return (tilex, tiley)
    return (None, None)
    
    
def drawHighlightTile(tilex, tiley, mapSurf):
    '''
    tilex: int
    tiley: int
    '''
    left, top = leftTopCoordsTile(tilex, tiley)
    pygame.draw.rect(mapSurf, HIGHLIGHTCOLOR,
                    (left, top, TILESIZE, TILESIZE), 4)

                    
def convertToTiles(levelMap):
    tiles = [[None] * BOARDHEIGHT for i in range(BOARDWIDTH)]
    for y in range(len(levelMap)):
        for x in range(len(levelMap[0])):
            if levelMap[y][x] == ' ':
                tiles[x][y] = None
            else:
                tiles[x][y] = levelMap[y][x]
    return tiles

                    
def readLevelsFile(filename):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)
    
    # read file and store in a list
    mapFileRead = open(filename, 'r')
    content = mapFileRead.readlines() + ['\r\n']
    mapFileRead.close()

    levelMaps = []
    levelMap = []    
    for lineNum in range(len(content)):
       # process each line that was in the level file
        line = content[lineNum].rstrip('\r\n')
        if line != '':
            levelMap.append(line)
        elif line == '' and len(levelMap) > 0:
            levelMaps.append(levelMap)
            levelMap = []
    return levelMaps


def saveToFile(filename, mapTiles, levelNum):
    '''If levelNum == 0 then add level to end of file
    '''
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)
    
    # clean up mapTiles
    newMap = copy.deepcopy(mapTiles)
    for x in newMap[:]:
        if set(OBJECTIMAGES).intersection(x) == set([]):
            logging.debug(newMap)
            newMap.remove(x)
    tempMap = copy.deepcopy(newMap)
    if newMap == []:
        return "Nothing to save"    
        
    objectFound = False
    for row in range(len(newMap[0])):
        for x in range(len(newMap)):
            if newMap[x][row] in OBJECTIMAGES:
                objectFound = True
                break
        if objectFound:
            break
        else:
            for i in range(len(newMap)):
                del tempMap[i][0]
                
    # write list to file
    char = ''
    isEmptyLine = True
    newLevel = []
    line = ''
    for row in range(len(tempMap[0])):
        for x in range(len(tempMap)):
            if tempMap[x][row] == None:
                char = ' '
            else:
                char = tempMap[x][row]
                isEmptyLine = False
            line += char
        if not isEmptyLine:
            newLevel.append(line)
            line = ''
            isEmptyLine = True
    # read file and store in a list
    levelMaps = readLevelsFile(filename)
            
    # write levels to file
    mapFileWrite = open(filename, 'w')
    savedLvlNum = levelNum
    for i, level in enumerate(levelMaps):
        if levelNum == 0:
            savedLvlNum = i + 2
        if levelNum - 1 == i:
            # write newLevel to file, overwrite previous map
            for line in newLevel:
                mapFileWrite.write(line)
                mapFileWrite.write('\n')
            mapFileWrite.write('\n')
        else:
            # write level to file
            for line in level:
                mapFileWrite.write(line)
                mapFileWrite.write('\n')
            mapFileWrite.write('\n')
    if levelNum == 0:
        if levelMaps == []:
            savedLvlNum = 1
        # write newLevel to end of file
        for line in newLevel:
            mapFileWrite.write(line)
            mapFileWrite.write('\n')
    mapFileWrite.close()
    return "Successfullly saved map", savedLvlNum

    
def updateSaveFile(filename, levels):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % (filename)

    mapFileWrite = open(filename, 'w')
    for level in levels:
        for line in level:
            mapFileWrite.write(line)
            mapFileWrite.write('\n')
        mapFileWrite.write('\n')
    return "Successfully updated save file"
            

if __name__=='__main__':
    main()

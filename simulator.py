#!/usr/bin/env python
# @Author: Synix
# @Date:   2014-09-25 09:16:40
# @Last Modified by:   Synix
# @Last Modified time: 2014-10-04 15:21:47

#/usr/bin/env python
"""
This simple example is used for the line-by-line tutorial
that comes with pygame. It is based on a 'popular' web banner.
Note there are comments here, but for the full explanation, 
follow along in the tutorial.
"""


#Import Modules
import os, pygame
from pygame.locals import *
from random import randint
from things import Plane

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'


#functions to create our resources
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', fullname
        raise SystemExit, message
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    fullname = os.path.join('data', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error, message:
        print 'Cannot load sound:', fullname
        raise SystemExit, message
    return sound


#classes for our game objects
class PlaneSprite(pygame.sprite.Sprite):
    """moves a clenched fist on the screen, following the mouse"""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect = load_image('plane.png', -1)
        self.plane = Plane(randint(0, 800), randint(0, 600), randint(1e3, 6e3))
        self.plane.setCourse(randint(0, 800), randint(0, 600), randint(1e3, 6e3), 450.)

    def update(self):
        "move the fist based on the mouse position"
        newPos = self.plane.flyAway()
        self.rect.midtop = (newPos.x, newPos.y)

def main():
    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""
#Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Airspace Simulator')
    pygame.mouse.set_visible(0)

#Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((150, 150, 250))

# #Put Text On The Background, Centered
#     if pygame.font:
#         font = pygame.font.Font(None, 36)
#         text = font.render("Pummel The Chimp, And Win $$$", 1, (10, 10, 10))
#         textpos = text.get_rect(centerx=background.get_width()/2)
#         background.blit(text, textpos)

#Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()

#Prepare Game Objects
    clock = pygame.time.Clock()
    planes = (PlaneSprite() for i in range(10))
    allsprites = pygame.sprite.RenderPlain(planes)

#Main Loop
    while 1:
        clock.tick(60)

    #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return

        allsprites.update()

    #Draw Everything
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        pygame.display.flip()

#Game Over


#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
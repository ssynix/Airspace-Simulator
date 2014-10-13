#!/usr/bin/env python
# @Author: Synix
# @Date:   2014-09-25 09:16:40
# @Last Modified by:   Synix
# @Last Modified time: 2014-10-12 20:46:40

#/usr/bin/env python

#Import Modules
from __future__ import division
import math
import os
import pygame

from itertools import product
from plane import Plane
from pygame.locals import *
from random import randint

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'
if not pygame.image.get_extended():
    raise SystemExit, "Sorry, extended image module required"

#------------ CONSTANTS ------------------#

PLANE_SIZE = 50
MIN_ALTITUDE, MAX_ALTITUDE = 300, 600
DISPLAY_WIDTH, DISPLAY_HEIGHT = 800, 600
COLLISION_DIST_SQ = (PLANE_SIZE/2) ** 2
ALERT_DIST_SQ = 5 * COLLISION_DIST_SQ
NUMBER_OF_PLANES = 15
SPEED = 400  # Number of frames it takes for each plane to reach its destination
FRAMERATE = 40

#------------ CONSTANTS ------------------#


#functions to create our resources
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error, message:
        print 'Cannot load image:', fullname
        raise SystemExit, message
    image = image.convert_alpha()
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
        self.image, self.rect = load_image('plane_low.png', -1)
        self.plane = Plane(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE))
        self.plane.setCourse(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE), SPEED)

        # Setting the position and saving it before transformations
        self.rect.center = self.plane.int2Dpos()
        center = self.rect.center

        # Scale down the icon
        scale = PLANE_SIZE / self.rect.width

        # Calculate heading and rotate the icon accordingly
        if self.plane.speed.x == 0:
            heading = 0
        else:
            heading = math.degrees(math.atan(-self.plane.speed.y/self.plane.speed.x))
        if self.plane.speed.x < 0:
            heading += 180
        self.image = pygame.transform.rotozoom(self.image, heading, scale)

        # Restoring the position after transformations
        self.rect = self.image.get_rect()
        self.rect.center = center


    def update(self):
        "move the fist based on the mouse position"
        self.plane.flyAway()
        self.rect.center = self.plane.int2Dpos()

        # Change the plane's color according to its height
        heightToColor = int(((self.plane.position.z - MIN_ALTITUDE) / (MAX_ALTITUDE - MIN_ALTITUDE)) * 255)
        if 0 <= heightToColor <= 255:
            heightColor = pygame.Surface(self.rect.size)
            heightColor.fill((heightToColor, heightToColor, heightToColor))
            self.image.blit(heightColor, (0, 0), None, BLEND_MIN)


def main():
#Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    pygame.display.set_caption('Airspace Simulator')

#Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((55, 50, 150))

#Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()

#Prepare Game Objects
    clock = pygame.time.Clock()
    planes = [PlaneSprite() for i in range(NUMBER_OF_PLANES)]
    allsprites = pygame.sprite.RenderPlain(planes)
    collisions = 0

#Main Loop
    while 1:
        clock.tick(FRAMERATE)

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

        def flash(sprite, status):
            if status == 'ALERT':
                color = Color('yellow')
                radius = int(math.sqrt(ALERT_DIST_SQ))
            elif status == 'COLLISION':
                color = Color('red')
                radius = int(math.sqrt(COLLISION_DIST_SQ))

            pygame.draw.circle(screen, color, sprite.plane.int2Dpos(), radius, 1)

        for (p1, p2) in product(allsprites, repeat=2):
            if 0 < p1.plane.squareDistance(p2.plane) < COLLISION_DIST_SQ:
                flash(p1, 'COLLISION')
                flash(p2, 'COLLISION')
                collisions += 1
            if 0 < p1.plane.squareDistance(p2.plane) < ALERT_DIST_SQ:
                flash(p1, 'ALERT')
                flash(p2, 'ALERT')
                p1.plane.radarInput.append(p2.plane)
                p2.plane.radarInput.append(p1.plane)


        # pygame.time.delay(250)

        pygame.display.flip()
    #Game Over


#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
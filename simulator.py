#!/usr/bin/env python
# @Author: Synix
# @Date:   2014-09-25 09:16:40
# @Last Modified by:   Shayan Sayahi
# @Last Modified time: 2015-02-11 21:24:54

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

PLANE_SIZE = Plane.PLANE_SIZE
COLLISION_DIST_SQ = Plane.COLLISION_DIST_SQ
ALERT_DIST_SQ = 9 * COLLISION_DIST_SQ
MIN_ALTITUDE, MAX_ALTITUDE = 300, 600
DISPLAY_WIDTH, DISPLAY_HEIGHT = 800, 600
NUMBER_OF_PLANES = 18
SPEED = 200  # Number of frames it takes for each plane to reach its destination
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
    def __init__(self, plane):
        pygame.sprite.Sprite.__init__(self) #call Sprite initializer
        self.image, self.rect = load_image('plane_low.png', -1)
        self.plane = plane

        self.originalImage = self.image


    def update(self):
        self.image = self.originalImage
        self.rect = self.image.get_rect()

        # Setting the position and saving it before transformations
        self.plane.flyAway()
        self.rect.center = self.plane.int2Dpos()
        center = self.rect.center

        # Scale down the icon
        scale = PLANE_SIZE / self.rect.width

        # Calculate heading and rotate the icon accordingly
        if self.plane.velocity.x == 0:
            heading = 0
        else:
            heading = math.degrees(math.atan(-self.plane.velocity.y/self.plane.velocity.x))
        if self.plane.velocity.x < 0:
            heading += 180
        self.image = pygame.transform.rotozoom(self.image, heading, scale)

        # Restoring the position after transformations
        self.rect = self.image.get_rect()
        self.rect.center = center

        white = pygame.Surface(self.rect.size)
        white.fill(Color('white'))
        self.image.blit(white, (0, 0), None, BLEND_MAX)

        # Change the plane's color according to its height
        heightToColor = int(((self.plane.position.z - MIN_ALTITUDE) / (MAX_ALTITUDE - MIN_ALTITUDE)) * 255)
        if heightToColor > 255:
            heightToColor = 255
        if heightToColor < 0:
            heightToColor = 0
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
    # planes = []
    # plane = Plane(100, 100, 400)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)
    # plane = Plane(600, 600, 500)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)
    # plane = Plane(700, 340, 390)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)
    # planes = [PlaneSprite(p) for p in planes]

    sprites = []
    for i in range(NUMBER_OF_PLANES):
        plane = Plane(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE))
        # plane.setCourse(randint(496, 500), 400, 600, SPEED)
        plane.setCourse(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE), SPEED)
        sprites.append(PlaneSprite(plane))
    allsprites = pygame.sprite.RenderPlain(sprites)

    collisionCount = 0
    ongoingCollisions = []

#Main Loop
    paused = False
    frame = 0
    while 1:
        clock.tick(FRAMERATE)
        frame += 1

        #Handle Input Events
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                return
            elif event.type == KEYDOWN and event.key == K_SPACE:
                if not paused:
                    print 'Total collisions =', collisionCount
                paused = not paused
        if paused:
            pygame.time.wait(100)  # Continue pausing until keypress
            # import pdb; pdb.set_trace()
            continue

        for sprite in allsprites:
            sprite.plane.processRadar()
        allsprites.update()

        #Draw Everything
        screen.blit(background, (0, 0))
        allsprites.draw(screen)
        # for (x, y, z) in (sprite.plane.destination for sprite in allsprites):
        #     pygame.draw.circle(screen, Color('black'), (x, y), 2, 2)

        def flash(sprite, status):
            if status == 'ALERT':
                color = Color('yellow')
                radius = int(math.sqrt(ALERT_DIST_SQ)/2)
            elif status == 'COLLISION':
                color = Color('red')
                radius = int(math.sqrt(COLLISION_DIST_SQ)/2)
            pygame.draw.circle(screen, color, sprite.plane.int2Dpos(), radius, 1)

        # Sending radar input to planes and detecting collisions
        for (s1, s2) in product(allsprites, repeat=2):
            if s1.plane.id < s2.plane.id:
                if 0 < s1.plane.squareDistance(s2.plane) < COLLISION_DIST_SQ:
                    flash(s1, 'COLLISION')
                    flash(s2, 'COLLISION')

                    if (s1.plane.id, s2.plane.id) not in ongoingCollisions:
                        collisionCount += 1
                        ongoingCollisions.append((s1.plane.id, s2.plane.id))
                elif (s1.plane.id, s2.plane.id) in ongoingCollisions:
                    ongoingCollisions.remove((s1.plane.id, s2.plane.id))

                if 0 < s1.plane.squareDistance(s2.plane) < ALERT_DIST_SQ:
                    flash(s1, 'ALERT')
                    flash(s2, 'ALERT')
                    s1.plane.radarInput.insert(0, ('Plane detected', s2.plane))
                    s2.plane.radarInput.insert(0, ('Plane detected', s1.plane))

        # Planes have reached their destination
        if frame == SPEED:
            distanceLost = (1 - math.sqrt((p.destination - p.position) ** 2 / (p.destination - p.origin) ** 2)
                                for p in (s.plane for s in allsprites))
            for distance in distanceLost:
                print '{:.1%}'.format(distance)
            print 'Total collisions =', collisionCount
            paused = True


        pygame.display.flip()
    #Game Over


#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
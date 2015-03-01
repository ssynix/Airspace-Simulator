#!/usr/bin/env python
# @Author: Synix
# @Date:   2014-09-25 09:16:40
# @Last Modified by:   Synix
# @Last Modified time: 2015-03-01 16:44:02

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
SEPARATION_DIST_SQ = Plane.SEPARATION_DIST_SQ
ALERT_DIST_SQ = 4 * COLLISION_DIST_SQ
MIN_ALTITUDE, MAX_ALTITUDE = 300, 600
DISPLAY_WIDTH, DISPLAY_HEIGHT = 800, 600
NUMBER_OF_PLANES = 12
SPEED = 200  # Number of frames it takes for each plane to reach its destination
FRAMERATE = 40
#counting losses of separation (one plane entering another's yellow zone), conflicts (start negotiating), change height, constraints
# means, stdeviation, losses of separation, efficiency, describe parameters (number of planes, utilities, etc) -> table of results -> interpret results (did it show the trend I was looking for) ( t-test, whether the observed difference in means is significantly different, from a pool t test the variance in the data comes from the difference of the populations, variances are additive
# accuracy of a t test, variance of delta = sum of the variance of populations divided by sqrt(n)
#kinda like self-contained sections, 1-2 page summaries of each experiment
# at least 20-30 trials per experiment, more if t-test returns unsignificant
#look at asterisk in bio paper, significance
# we hypothesize that efficiency and whatnot increases this much in multiway compared to pairwise
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

        # Plane id text
        fontsize = int(PLANE_SIZE / 2)
        font = pygame.font.Font(None, fontsize)
        textColor = 10
        text = font.render(str(self.plane.id), True, (textColor, textColor, textColor))
        self.image.blit(text, (0, 0))


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
    planes = []

    # Head on collision
    # plane = Plane(0, 300, 400)
    # plane.setCourse(800, 300, 400, SPEED)
    # planes.append(plane)
    # plane = Plane(800, 300, 400)
    # plane.setCourse(00, 300, 400, SPEED)
    # planes.append(plane)

    # 3 plane collision
    # plane = Plane(100, 100, 400)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)
    # plane = Plane(600, 600, 500)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)
    # plane = Plane(700, 340, 390)
    # plane.setCourse(400, 400, 600, SPEED)
    # planes.append(plane)

    # Corner Case
    # plane = Plane(5,332,597); plane.setCourse(229,230,513,SPEED); planes.append(plane);plane = Plane(189,408,429); plane.setCourse(425,551,593,SPEED); planes.append(plane);plane = Plane(382,499,408); plane.setCourse(758,149,586,SPEED); planes.append(plane);plane = Plane(206,63,376); plane.setCourse(249,294,310,SPEED); planes.append(plane);plane = Plane(210,202,560); plane.setCourse(568,274,528,SPEED); planes.append(plane);plane = Plane(377,556,565); plane.setCourse(137,239,378,SPEED); planes.append(plane);plane = Plane(685,65,519); plane.setCourse(200,130,379,SPEED); planes.append(plane);plane = Plane(789,271,347); plane.setCourse(458,58,415,SPEED); planes.append(plane);plane = Plane(615,403,315); plane.setCourse(429,268,327,SPEED); planes.append(plane);plane = Plane(683,545,570); plane.setCourse(120,315,566,SPEED); planes.append(plane);plane = Plane(62,5,578); plane.setCourse(461,259,433,SPEED); planes.append(plane);plane = Plane(394,128,546); plane.setCourse(216,347,346,SPEED); planes.append(plane);

    while True:
        planes = []
        Plane.ID = 0
        for i in range(NUMBER_OF_PLANES):
            plane = Plane(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE))
            # plane.setCourse(randint(496, 500), 400, 600, SPEED)
            plane.setCourse(randint(0, DISPLAY_WIDTH), randint(0, DISPLAY_HEIGHT), randint(MIN_ALTITUDE, MAX_ALTITUDE), SPEED)
            planes.append(plane)
        if all(p1.squareDistance(p2) > ALERT_DIST_SQ for (p1, p2) in product(planes, repeat=2) if p1.id < p2.id):
            break
    allsprites = pygame.sprite.RenderPlain(PlaneSprite(p) for p in planes)

    collisionCount = 0
    ongoingCollisions = []
    separationCount = 0
    ongoingSeparations = []

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

        for p in (sprite.plane for sprite in allsprites):
            pygame.draw.line(screen, Color('yellow'), p.origin.int2D(), p.destination.int2D(), 1)

        def flash(sprite, status):
            if status == 'ALERT':
                color = Color('blue')
                radius = int(math.sqrt(ALERT_DIST_SQ)/2)
            elif status == 'COLLISION':
                color = Color('red')
                radius = int(math.sqrt(COLLISION_DIST_SQ)/2)
            elif status == 'SEPARATION':
                color = Color('yellow')
                radius = int(math.sqrt(SEPARATION_DIST_SQ)/2)
            pygame.draw.circle(screen, color, sprite.plane.int2Dpos(), radius, 1)

        # Sending radar input to planes and detecting collisions
        for (s1, s2) in product(allsprites, repeat=2):
            if s1.plane.id < s2.plane.id:
                if 0 < s1.plane.squareDistance(s2.plane) < COLLISION_DIST_SQ:
                    import pdb; pdb.set_trace()
                    flash(s1, 'COLLISION')
                    flash(s2, 'COLLISION')

                    if (s1.plane.id, s2.plane.id) not in ongoingCollisions:
                        collisionCount += 1
                        ongoingCollisions.append((s1.plane.id, s2.plane.id))
                elif (s1.plane.id, s2.plane.id) in ongoingCollisions:
                    ongoingCollisions.remove((s1.plane.id, s2.plane.id))

                if 0 < s1.plane.squareDistance(s2.plane) < SEPARATION_DIST_SQ:
                    import pdb; pdb.set_trace()
                    flash(s1, 'SEPARATION')
                    flash(s2, 'SEPARATION')

                    if (s1.plane.id, s2.plane.id) not in ongoingSeparations:
                        separationCount += 1
                        ongoingSeparations.append((s1.plane.id, s2.plane.id))
                elif (s1.plane.id, s2.plane.id) in ongoingSeparations:
                    ongoingSeparations.remove((s1.plane.id, s2.plane.id))

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
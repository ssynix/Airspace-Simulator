#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Synix
# @Date:   014-10-01 05:52:51
# @Last Modified by:   Shayan Sayahi
# @Last Modified time: 2015-02-10 07:39:50

from __future__ import division
from itertools import product
from random import randint
import math
import numpy


class Vector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __neg__(self):
        return Vector(-self.x, -self.y, -self.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __truediv__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector(self.x / other, self.y / other, self.z / other)
        elif isinstance(other, Vector):
            return Vector(self.x / other.x, self.y / other.y, self.z / other.z)

    def __mul__(self, other):
        # if numpy.isreal(other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector(self.x * other, self.y * other, self.z * other)
        elif isinstance(other, Vector): # Dot product
            return sum((self.x * other.x, self.y * other.y, self.z * other.z))

    def __pow__(self, scalar): # Dot product in itself
        return sum((self.x ** scalar, self.y ** scalar, self.z ** scalar))

    def squareDistance(self, other):
        return (other - self) ** 2

    def __repr__(self):
        return "<Vector ({:.2f}, {:.2f}, {:.2f})>".format(*self)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


class VelocityInterval:
    # A velocity vector maintained from 'begin' frames from now till 'end'
    # as a result of a commitment with plane id
    def __init__(self, velocity, begin, end, id):
        self.velocity, self.begin, self.end, self.id = velocity, int(begin), int(end), id

    def __repr__(self):
        return '<Velocity=%s, begin=%s, end=%s, id=%s>' % (self.velocity, self.begin, self.end, self.id)


class Plane:
    #---------Static Members--------#
    ID = 0
    PLANE_SIZE = 40
    COLLISION_DIST_SQ = PLANE_SIZE ** 2

    #-------------------------------#

    def __init__(self, x, y, altitude):
        self.position = Vector(x, y, altitude)
        self.radarInput = []
        self.commitments = {}  # commitments[plane] = {'Time Left':, 'Begin':, 'End':}
        self.velocityIntervals = []
        # self.utilityFunction = None
        self.utilities = {}    # Used to keep track of alternate trajectories sent to another plane
        self.multiwayParties = []
        self.id = Plane.ID
        Plane.ID += 1

    def utilityFunction(self, alternate):
        return (alternate * self.velocity) * (randint(1, 100)/100000 + 1) 
        # A small noise added to the utility to avoid having trajectories with the exact same utility (could complicate things)

    def setCourse(self, x, y, altitude, time):
        self.origin = self.position
        self.destination = Vector(x, y, altitude)
        self.distanceTraveledSq = 0
        self.velocity = (self.destination - self.position) / time
        self.speedSquared = self.velocity ** 2
        self.velocityIntervals = []
        self.velocityIntervals.append(VelocityInterval(self.velocity, 0, 1e6, self.id))

    def generateAlternates(self):
        # Change heading while mainting constant speed
        result = []
        anglesZ = [-30, 30, 15, -15, 45, -45, 75, -75, 0]  # Rotation around the Z axis
        for t in map(math.radians, anglesZ):
            rotationMatrix = numpy.array(
                [[math.cos(t),  -math.sin(t),   0],
                [math.sin(t),   math.cos(t),    0],
                [0,             0,              1]])
            rotated = numpy.dot(rotationMatrix, zip(self.velocity)).reshape(1, 3)
            result.append(Vector(rotated[0][0], rotated[0][1], rotated[0][2]))
            # TODO 
        return result


    def processRadar(self):
        # Keep track of commitments
        for commitment, info in self.commitments.iteritems():
            if info['Time Left'] == 0:
                del self.commitments[commitment]
            self.commitments[commitment]['Time Left'] -= 1

        # Process radar input to detect/avoid collisions
        while self.radarInput:
            # Using pop and insert(0, ) to simulate a queue (yes... it's not OPTIMAL, doesn't matter)
            input = self.radarInput.pop()
            if input[0] == 'Plane detected':
                other = input[1]
                if other in self.commitments:
                    continue  # Don't do anything else if there's already a commitment with this plane

                # Math and Physics...
                delta_position = other.position - self.position
                delta_velocity = other.velocity - self.velocity

                # Coefficients of the square_distance/time quadratic equation
                a = delta_velocity ** 2
                b = delta_position * delta_velocity * 2
                c = delta_position ** 2 - Plane.COLLISION_DIST_SQ
                collisionTimes = numpy.roots([a, b, c])

                # Checking that roots exist and are not imaginary, collision happens between two real roots
                if collisionTimes.size and all(numpy.isreal(collisionTimes)):
                    begin, end = min(collisionTimes), max(collisionTimes)
                    if end < 0:  # Collision has happened in the past, no action required
                        break
                    if begin < 0:  # Currently colliding, any actions must begin from now
                        begin = 0

                    self.commitments[other] = {}
                    self.commitments[other]['Time Left'] = 2 * end
                    self.commitments[other]['Begin'] = begin
                    self.commitments[other]['End'] = end
                    self.utilities[other.id] = [(alt, self.utilityFunction(alt)) for alt in self.generateAlternates()]
                    other.radarInput.insert(0, ('Alternate Trajectories', self, self.utilities[other.id]))

            elif input[0] == 'Alternate Trajectories':
                other = input[1]
                otherUtilities = input[2]
                maxNashProduct = 0
                maxNashDeal = None
                for (plan1, plan2) in product(self.utilities[other.id], otherUtilities):
                    myDealVelocity = plan1[0]
                    otherDealVelocity = plan2[0]
                    # Math and Physics... # TODO MAKE DRY
                    delta_position = other.position - self.position
                    delta_velocity = otherDealVelocity - myDealVelocity

                    # Coefficients of the square_distance/time quadratic equation
                    a = delta_velocity ** 2
                    b = delta_position * delta_velocity * 2
                    c = delta_position ** 2 - Plane.COLLISION_DIST_SQ
                    collisionTimes = numpy.roots([a, b, c])
                    if collisionTimes.size and all(numpy.isreal(collisionTimes)):
                        continue  # Discard a deal in which collision happens

                    nashProduct = plan1[1] * plan2[1]
                    if nashProduct > maxNashProduct:
                        maxNashProduct = nashProduct
                        maxNashDeal = (plan1, plan2)

                begin = self.commitments[other]['Begin']
                end   = self.commitments[other]['End']
                if maxNashDeal:
                    diff = maxNashDeal[0][0] - self.velocity
                    self.velocityIntervals.append(VelocityInterval(diff, 0, end, other.id))
                    self.velocityIntervals.append(VelocityInterval(-diff, end, 2*end, other.id))

            elif input[0] == 'Multiway':



    def flyAway(self):
        # Calculate total velocity
        self.velocity = Vector(0, 0, 0)
        for interval in self.velocityIntervals:
            if interval.begin <= 0:
                self.velocity += interval.velocity
            interval.begin -= 1
            interval.end -= 1
            if interval.end == 0:
                self.velocityIntervals.remove(interval)

        # Maintaining constant speed
        if self.velocity ** 2 != 0:
            self.velocity *= math.sqrt(self.speedSquared / self.velocity ** 2)

        # Flying forward
        self.position += self.velocity
        self.distanceTraveledSq += self.velocity ** 2


    def squareDistance(self, other):
        return self.position.squareDistance(other.position)

    def int2Dpos(self):
        return int(self.position.x), int(self.position.y)

    def __repr__(self):
        return '<Plane {id=%s, position=%s, velocity=%s}>' % (self.id, self.position, self.velocity)


# utility functions; limitations on altitude, speed, heading; speed: 1.5-2.5 knots, 10k-50k feet height, MCP, 
# empirically measure two things, frequency of loss of separation (compared to uncoordinated), efficiency (fuel loss, increased travel time)
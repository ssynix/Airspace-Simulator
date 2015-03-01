#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Synix
# @Date:   014-10-01 05:52:51
# @Last Modified by:   Synix
# @Last Modified time: 2015-03-01 16:34:53

from __future__ import division
from functools import reduce
from itertools import product, combinations
from operator import mul
from sets import Set
import math
import numpy
import random


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

    def __pow__(self, scalar):  # Dot product in itself
        return sum((self.x ** scalar, self.y ** scalar, self.z ** scalar))

    def squareDistance(self, other):
        return (other - self) ** 2

    def norm(self):
        return math.sqrt(self ** 2)

    def copy(self):
        return Vector(self.x, self.y, self.z)

    def int2D(self):
        return int(round(self.x)), int(round(self.y))

    def normalized(self):
        return self / self.norm()

    def angle(self, other):
        return math.acos(self * other / (self.norm() * other.norm()))

    def __repr__(self):
        return "<Vector ({:.2f}, {:.2f}, {:.2f})>".format(*self)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


class VelocityInterval:
    # A velocity vector maintained from 'begin' frames from now till 'end'
    # as a result of a commitment with plane id
    def __init__(self, velocity, begin, end, id=None):
        self.velocity, self.begin, self.end, self.id = velocity, int(round(begin)), int(round(end)), id

    def __repr__(self):
        return '<Velocity=%s, begin=%s, end=%s, id=%s>' % (self.velocity, self.begin, self.end, self.id)


class Plane:
    #---------Static Members--------#
    ID = 0
    PLANE_SIZE = 40
    COLLISION_DIST_SQ = PLANE_SIZE ** 2
    SEPARATION_DIST_SQ = 4 * COLLISION_DIST_SQ

    #-------------------------------#

    def __init__(self, x, y, altitude):
        self.position = Vector(x, y, altitude)
        self.radarInput = []
        self.commitment = {'time': 0, 'offcourse': 0}
        self.velocityIntervals = []
        # self.utilityFunction = None
        self.multiwayParties = Set()
        self.collisionsEnd = Set()
        self.multiwayUtilities = {}
        self.id = Plane.ID
        Plane.ID += 1

    def utilityFunction(self, alternate):
        return (alternate * self.velocity) * (random.uniform(.9999, 1.0001))
        # A small noise added to the utility to avoid having trajectories with the exact same utility (could complicate things)

    def setCourse(self, x, y, altitude, time):
        self.origin = self.position
        self.destination = Vector(x, y, altitude)
        self.distanceTraveledSq = 0
        self.velocity = (self.destination - self.position) / time
        self.speed = self.velocity.norm()
        self.velocityIntervals = []
        self.velocityIntervals.append(VelocityInterval(self.velocity, 0, 1e6, self.id))

    def generateAlternatives(self):
        # Change heading while mainting constant speed
        result = []
        heading = [-35, 35]  # Rotation around the Z axis
        anglesZ = [20, -20]
        # heading = [-30, 30, 15, -15, 45, -45, 75, -75, 0]  # Rotation around the Z axis

        for t in map(math.radians, heading):
            rotationMatrix = numpy.array(
                [[math.cos(t),  -math.sin(t),   0],
                [math.sin(t),   math.cos(t),    0],
                [0,             0,              1]])
            rotated = numpy.dot(rotationMatrix, zip(self.velocity)).reshape(1, 3)
            result.append(Vector(*rotated[0]))

        for t in map(math.radians, anglesZ):
            sinTheta = self.velocity.z / self.speed
            cosTheta = math.sqrt(1 - sinTheta ** 2)
            t += math.asin(sinTheta)
            zFactor = math.sin(t) / sinTheta
            xyFactor = math.sqrt(-(self.velocity.z * zFactor) ** 2 + self.velocity ** 2) / (self.speed * cosTheta)
            rotationMatrix = numpy.array(
                [[xyFactor,  0,    0],
                [0,   xyFactor,    0],
                [0,   0,     zFactor]])
            rotated = numpy.dot(rotationMatrix, zip(self.velocity)).reshape(1, 3)
            result.append(Vector(*rotated[0]))
            # TODO 
        return result

    def findCollisionTimes(self, other, delta_velocity=None):
        # Math and Physics...
        delta_position = other.position - self.position
        if not delta_velocity:
            delta_velocity = other.velocity - self.velocity

        # Coefficients of the square_distance/time quadratic equation
        a = delta_velocity ** 2
        b = delta_position * delta_velocity * 2
        c = delta_position ** 2 - Plane.SEPARATION_DIST_SQ
        d = b*b - 4*a*c

        if d < 0:
            return None
        times = [(-b + math.sqrt(d))/(2*a), (-b - math.sqrt(d))/(2*a)]
        if max(times) > 0:
            return times
        return None

    def receive(self, tuple):
        self.radarInput.insert(0, tuple)

    def processRadar(self):
        self.commitment['time'] -= 1
        if self.commitment['time'] == 0:
            self.multiwayParties = Set()

        # Process radar input in a loop (FIFO)
        while self.radarInput:
            # Using pop and insert(0, ) to simulate a queue (yes... it's not OPTIMAL, doesn't matter)
            input = self.radarInput.pop()
            if input[0] == 'Plane detected':
                other = input[1]
                if other in self.multiwayParties:
                    continue  # Don't do anything else if there's already a commitment with this plane

                collisionTimes = self.findCollisionTimes(other)
                if collisionTimes:
                    end = max(collisionTimes)

                    self.multiwayParties.add(self)
                    self.collisionsEnd.add(end)
                    other.radarInput.insert(0, ('Multiway', self.multiwayParties.copy(), self.multiwayUtilities.copy(), self.collisionsEnd.copy()))

            elif input[0] == 'Multiway':
                otherParties = input[1]
                otherUtilities = input[2]
                otherCollisionTimes = input[3]

                # print 'boo' + str(self.id) # DEBUG
                newParties = otherParties - self.multiwayParties
                self.multiwayParties.update(otherParties)
                self.multiwayUtilities.update(otherUtilities)
                self.collisionsEnd.update(otherCollisionTimes)

                if newParties or self not in self.multiwayUtilities.keys():
                    self.multiwayUtilities[self] = [(alt, self.utilityFunction(alt)) for alt in self.generateAlternatives()]
                    [plane.radarInput.insert(0, ('Multiway', self.multiwayParties.copy(), self.multiwayUtilities.copy(), self.collisionsEnd.copy()))
                        for plane in self.multiwayParties if plane != self]

                if self.multiwayParties == Set(self.multiwayUtilities.keys()):
                    #  (p1, [(v, u)1, (v, u)2, ...]), (p2, [(v, u)3, (v, u)4, ...], ...) -->
                    #  [ (p1, (v,u)1), (p1, vu2), ...], [(p2, vu3), (p2, vu4), ...]
                    planeTrajectories = [map(lambda x: (p,) + (x,), vulist) for (p, vulist) in self.multiwayUtilities.iteritems()]
                    maxNashProduct = 0
                    maxNashDeal = None

                    for deal in product(*planeTrajectories):
                    # deal = ( (plane, plan), ... )
                    # plan = [ (Vector, utility), ... ]

                        goodDeal = True
                        for (u1, u2) in combinations(deal, 2):
                            plane1, plan1 = u1
                            plane2, plan2 = u2
                            collisionTimes = plane1.findCollisionTimes(plane2, plan2[0] - plan1[0])
                            if collisionTimes:
                                goodDeal = False
                                break
                        if not goodDeal:
                            continue

                        nashProduct = reduce(mul, (x[1][1] for x in deal))  # x[1] == plan, plan[1] == utility
                        if nashProduct > maxNashProduct:
                            maxNashProduct = nashProduct
                            maxNashDeal = deal

                    if maxNashDeal:
                        # print maxNashDeal, self.velocity # DEBUG
                        myDealVelocity = next(x[1][0] for x in maxNashDeal if x[0] == self)
                        origVelocity = (vi.velocity for vi in self.velocityIntervals if vi.id == self.id).next()
                        self.velocityIntervals = []

                        end = max(self.collisionsEnd)
                        self.commitment['time'] = round(end)
                        self.velocityIntervals.append(VelocityInterval(myDealVelocity, 0, end))

                        # Find the total distance that the plane has strayed from its original path (sum of all deviations + newly reached deal)
                        # Then calculate the time it takes to correct its course
                        # Imagine the offcourse vector, the original course (origVelocity), and the correction vector (diff) make a triangle, then
                        # the side corresponding to origVelocity is twice the length of offcourse's projection on origVelocity

                        offcourse = self.commitment['offcourse'] + myDealVelocity * end
                        backTime = offcourse.norm() / self.speed
                        diff = origVelocity * (origVelocity * offcourse / origVelocity ** 2) * 2 - offcourse
                        diff = diff.normalized() * self.speed
                        self.velocityIntervals.append(VelocityInterval(diff, end, end + backTime, -1))
                        self.velocityIntervals.append(VelocityInterval(origVelocity, end + backTime, 1e6, self.id))
                    else:
                        # One disadvantage of our approach is that if there is an unresolvable conflict between 2 out of many planes
                        # in a negotiation, none of them will reach a deal as a result of that conflict
                        self.commitment['time'] = self.speed
                        print "No deal found for ", self

                    self.multiwayUtilities = {}
                    self.collisionsEnd = Set()


    def flyAway(self):
        # Calculate total velocity
        self.velocity = Vector(0, 0, 0)
        for interval in self.velocityIntervals:
            if interval.begin <= 0:
                self.velocity += interval.velocity
            interval.begin -= 1
            interval.end -= 1
        self.velocityIntervals = [vi for vi in self.velocityIntervals if vi.end > 0]

        # if self.id == 0: #  DEBUG
        #     print self.velocityIntervals

        # Maintaining constant speed
        if self.velocity ** 2 != 0:
            self.velocity *= self.speed / self.velocity.norm()

        # Flying forward
        self.position += self.velocity
        self.distanceTraveledSq += self.velocity ** 2

        if self.commitment['time'] > 0 or any(vi.id == -1 for vi in self.velocityIntervals):
            self.commitment['offcourse'] += self.velocity
        else:
            self.commitment['offcourse'] = Vector(0, 0, 0)

    def squareDistance(self, other):
        return self.position.squareDistance(other.position)

    def int2Dpos(self):
        return self.position.int2D()

    def __repr__(self):
        return '<Plane {id=%s}>' % (self.id)
        # return '<Plane {id=%s, position=%s, velocity=%s}>' % (self.id, self.position, self.velocity)


# utility functions; limitations on altitude, speed, heading; speed: 1.5-2.5 knots, 10k-50k feet height, MCP, 
# empirically measure two things, frequency of loss of separation (compared to uncoordinated), efficiency (fuel loss, increased travel time)
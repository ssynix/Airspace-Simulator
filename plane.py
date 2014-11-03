#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Synix
# @Date:   014-10-01 05:52:51
# @Last Modified by:   Synix
# @Last Modified time: 2014-11-03 14:03:52

from __future__ import division
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
        self.commitments = {}
        self.velocityIntervals = []
        self.id = Plane.ID
        Plane.ID += 1

    def setCourse(self, x, y, altitude, time):
        self.origin = self.position
        self.destination = Vector(x, y, altitude)
        self.distanceTraveledSq = 0
        self.velocity = (self.destination - self.position) / time
        self.speedSquared = self.velocity ** 2
        self.velocityIntervals = []
        self.velocityIntervals.append(VelocityInterval(self.velocity, 0, 1e6, self.id))

    def processRadar(self):
        # Keep track of commitments
        for commitment, time in self.commitments.iteritems():
            if time == 0:
                del self.commitments[commitment]
            self.commitments[commitment] -= 1

        # Process radar input to detect/avoid collisions
        while self.radarInput:
            other = self.radarInput.pop()

            if other.id in self.commitments:
                continue  # For now don't do anything else if there's already a commitment

            # Math and Physics...
            delta_position = other.position - self.position
            delta_velocity = other.velocity - self.velocity

            # Coefficients of the square_distance/time quadratic equation
            a = delta_velocity ** 2
            b = delta_position * delta_velocity * 2
            c = delta_position ** 2 - Plane.COLLISION_DIST_SQ
            collisionTimes = numpy.roots([a, b, c])

            # Checking that roots exist and are not imaginary, collision happens inbetween two real roots
            if collisionTimes.size and all(numpy.isreal(collisionTimes)):
                begin, end = min(collisionTimes), max(collisionTimes)
                if end < 0:  # Collision has happened in the past, no action required
                    break
                if begin < 0:  # Currently colliding, any actions must begin from now
                    begin = 0

                away = Vector(*numpy.cross(list(self.velocity), list(other.velocity)))
                self.velocityIntervals.append(VelocityInterval(away, 0, end, other.id))
                self.velocityIntervals.append(VelocityInterval(-away, end, 2 * end, other.id))
                self.commitments[other.id] = 2 * end


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
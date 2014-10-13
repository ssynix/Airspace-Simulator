#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Synix
# @Date:   014-10-01 05:52:51
# @Last Modified by:   Synix
# @Last Modified time: 2014-10-12 17:47:39


class Vector:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def __div__(self, scalar):
        scalar = float(scalar)
        return Vector(self.x / scalar, self.y / scalar, self.z / scalar)

    def __pow__(self, scalar):
        return Vector(self.x ** scalar, self.y ** scalar, self.z ** scalar)

    def __repr__(self):
        return "<Vector (%s, %s, %s)>" % (self.x, self.y, self.z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


class Plane:
    ID = 0

    def __init__(self, x, y, altitude):
        self.position = Vector(x, y, altitude)
        self.radarInput = []
        self.id = Plane.ID
        Plane.ID += 1

    def setCourse(self, x, y, altitude, time):
        self.destination = Vector(x, y, altitude)
        self.speed = (self.destination - self.position) / time

    def flyAway(self):
        self.position += self.speed


    def squareDistance(self, other):
        return sum((other.position - self.position) ** 2)

    def int2Dpos(self):
        return int(self.position.x), int(self.position.y)

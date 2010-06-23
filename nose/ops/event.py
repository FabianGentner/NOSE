# -*- coding: utf-8 -*-

# Copyright (c) 2010 Institute for High-Frequency Technology, Technical
# University of Braunschweig
#
# This file is part of NOSE.
#
# NOSE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NOSE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NOSE. If not, see <http://www.gnu.org/licenses/>.


class Event(object):
    """
    The base class for all event classes in this module.
    Implements :meth:`__str__` and :meth:`__eq__`.
    """
    def __str__(self):
        """
        Prints the event as a string.
        """
        result = '%s event with attributes:' % self.__class__.__name__
        for item in self.__dict__.items():
            result += '\n    %s: %s' % item
        return result


    def __eq__(self, other):
        """Checks two events for equality."""
        return (other != None
            and self.__class__ == other.__class__
            and self.__dict__ == other.__dict__)




class SystemPropertiesChanged(Event):

    def __init__(self, system, name):
        self._system = system

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` whose properties have
        changed.
        """
        return self._system

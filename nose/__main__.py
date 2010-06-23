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

import gui.main
import gui.mediator
import ops.system


def main():
    """
    Starts the application.
    """
    mediator = gui.mediator.Mediator()
    # TODO: Initial calibration data should be loaded from a file.
    system = ops.system.ProductionSystem(mediator)
    mainWindowHandler = gui.main.MainWindowHandler(mediator, system)
    mainWindowHandler.start()


if __name__ == '__main__':
    main()

:mod:`gui.charting.axis` --- Handles the charts' axes
=====================================================

.. automodule:: gui.charting.axis

The :class:`Axis` Abstract Base Class
-------------------------------------
.. autoclass:: Axis()
.. autoattribute:: Axis.maxValue
.. autoattribute:: Axis.dimensionLabelText
.. automethod:: Axis.draw
.. automethod:: Axis.isInBounds

The :class:`Abscissa` Class
---------------------------
.. autoclass:: Abscissa
.. automethod:: Abscissa.xFromValue
.. automethod:: Abscissa.valueFromX

The :class:`Ordinate` Class
---------------------------
.. autoclass:: Ordinate
.. automethod:: Ordinate.yFromValue
.. automethod:: Ordinate.valueFromY

The :class:`SecondaryOrdinate` Class
------------------------------------
.. autoclass:: SecondaryOrdinate

Constants
---------
The following constants are provided:

Ticks
"""""
.. autodata:: MAJOR_TICK_LENGTH
.. autodata:: MINOR_TICK_LENGTH
.. autodata:: MIN_TICK_DISTANCE

Tick Labels
"""""""""""
.. autodata:: ABSCISSA_MIN_TICK_LABEL_DISTANCE
.. autodata:: ORDINATE_MIN_TICK_LABEL_DISTANCE
.. autodata:: ABSCISSA_TO_LABEL_SPACING
.. autodata:: ORDINATE_TO_LABEL_SPACING

Dimension Labels
""""""""""""""""
.. autodata:: ABSCISSA_DIMENSION_LABEL_POSITION
.. autodata:: ORDINATE_DIMENSION_LABEL_POSITION
.. autodata:: EXTRA_FRACTION_BAR_LENGTH
.. autodata:: FRACTION_BAR_SPACING

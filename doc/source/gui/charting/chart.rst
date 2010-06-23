:mod:`gui.charting.chart` --- Provides a :class:`gtk.Widget` for simple charts
==============================================================================

.. automodule:: gui.charting.chart

The :class:`Chart` Widget
-------------------------
.. autoclass:: Chart
.. autoattribute:: Chart.chartArea

Axes
""""
.. autoattribute:: Chart.abscissa
.. autoattribute:: Chart.ordinate
.. autoattribute:: Chart.secondaryOrdinate
.. autoattribute:: Chart.showSecondaryOrdinate

Graphs
""""""
.. automethod:: Chart.addGraph
.. automethod:: Chart.addSecondaryGraph
.. automethod:: Chart.clearGraphs

Caption
"""""""
.. autoattribute:: Chart.captionText
.. autoattribute:: Chart.minCaptionLines

Constants
---------
.. autodata:: NO_DATA_TEXT
.. autodata:: BORDER

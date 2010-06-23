:mod:`ops.calibration.data` --- Encapsulates data collected during calibration
==============================================================================

.. automodule:: ops.calibration.data


The :class:`CalibrationData` Class
----------------------------------

.. autoclass:: CalibrationData()

General Attributes
""""""""""""""""""
.. autoattribute:: CalibrationData.system
.. autoattribute:: CalibrationData.fileName

Measurements
"""""""""""""
.. automethod:: CalibrationData.addMeasurement
.. automethod:: CalibrationData.removeMeasurement
.. autoattribute:: CalibrationData.measurements
.. autoattribute:: CalibrationData.heatingCurrents
.. autoattribute:: CalibrationData.temperatureSensorVoltages
.. autoattribute:: CalibrationData.temperatures
.. autoattribute:: CalibrationData.hasMeasurements

Estimation Functions
""""""""""""""""""""
.. autoattribute:: CalibrationData.isComplete
.. automethod:: CalibrationData.getCurrentFromTargetTemperature
.. automethod:: CalibrationData.getFinalTemperatureFromCurrent
.. automethod:: CalibrationData.getTemperatureFromVoltage

Fitting
"""""""
.. autoattribute:: CalibrationData.polynomialDegree
.. autoattribute:: CalibrationData.minMeasurementsForEstimation


Persistence Functions
---------------------

:class:`CalibrationData` objects are saved as XML documents, using the
extension *cal*. The files are structured according to the following XML
Schema:

.. code-block:: xml

    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="calibration-data">
        <xs:complexType>
          <xs:sequence minOccurs="0" maxOccurs="unbounded">
            <xs:element name="measurement">
              <xs:complexType>
                <xs:sequence>
                  <xs:element name="current" type="xs:double" />
                  <xs:element name="voltage" type="xs:double" />
                  <xs:element name="temperature" type="xs:double" />
                </xs:sequence>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:schema>

The docment is not formally validated when it is parsed, however. Some errors,
such as extraneous elements, will slip through.

.. autofunction:: toXML
.. autofunction:: fromXML


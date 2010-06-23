Glossary
========

.. glossary::

    calibration
        To calibrate the production system, a number of functions have to be
        found that can be used to estimate the :term:`heating temperature`
        that corresponds to a given :term:`temperature sensor voltage`, and
        the :term:`heating current` that results in the heating temperature
        reaching, but not exceeding, a given *target temperature*.

        These *estimation functions* are found during the *calibration
        procedure*, which consists of a number of *heating stages* that
        use different heating currents. At the end of a stage, when the
        temperature sensor voltage has become reasonably stable, the user
        is asked to take a *temperature measurement*, which is recorded
        along with the heating current used and the temperature sensor
        voltage at the time of the measurement. After a reasonable number
        of heating stages, which may take several hours to complete, the
        estimation functions are fitted to these data.

    ..  Some of this text is duplicated in :mod:`ops.calibration.manager`.

    calibration procedure
        The operation that is performed to calibrate the production system.
        See :term:`calibration`.

    calibration stage
        TODO

    client
        The clients of a class or function are the classes or functions that
        use the functionality it provides. A sapient entity that uses the
        application is a *user*, not a client.

    device
        The FCI-7011 fiber coupler production system controlled by the
        application. Used when that term :term:`production system`
        could be misunderstood as referring to an instance of
        :class:`ops.system.ProductionSystem`.

    estimation function
        One of the functions that need to be fitted for the production system
        to be calibrated. See :term:`calibration`.

    heater
        The part of the production system used to heat the fiber. The heater
        can be moved forewards and backwards, and can be operated with a range
        of :term:`heating currents <heating current>`. It's :term:`heating
        temperature` is measured by the :term:`temperature sensor`.

    heating current
        The current, always expressed in mA, that is used to operate the
        production system's :term:`heater`. In most cases, heating the system
        to a given :term:`target temperature` will be more convenient than
        explicitly setting a heating current.

    heating stage
        TODO

    heating temperature
        The temperature, always expressed in °C, that the production system's
        :term:`heater` is heating with. The system does not directly report
        its heating temperature, however. Instead, its :term:`temperature
        sensor` reports its voltage, which can be linked to an estimated
        temperature if the system is :term:`calibrated <calibration>`.

        Under some circumstances, the temperature sensor voltage -- and
        consequently the reported heating temperature -- may not be an accurate
        reflection of the actual heating temperature. See :term:`temperature
        sensor`.

        If the system is calibrated, it is also possible to heat the system
        to a given temperature. See :term:`target temperature`.

    heating unit
        The :term:`heater`.

    production system
        The FCI-7011 fiber coupler production system controlled by the
        application, or an instance of :class:`ops.system.ProductionSystem`.
        In contexts where it might be ambiguous which one is meant, the term
        :term:`device` is used to refer to the physical production system,
        and the term *production system instance* is used to refer to an
        instance of the class.

    safe mode
        In order to prevent damage to the production system, the application
        monitors its :term:`heating temperature` and :term:`temperature sensor
        voltage`. If either exceeds its safe limits, the system is switched
        into its safe mode, where its :term:`heating current` is lowered to
        a value that is known to be safe. The current may then be changed
        again, at which point the system leaves its safe mode.

    system
        Short for :term:`production system`.

    target temperature
        A temprature, always expressed in °C, the production system's
        :term:`heater` is supposed to reach, but not exceed. In order to set
        a target temperature, the system needs to be :term:`calibrated
        <calibration>`.

    temperature measurement
        A measurement of the :term:`heating temperature` that has been taken
        by the user. A number of temperature measurements are necessary to
        :term:`calibrate <calibration>` the production system.

    temperature sensor
        A sensor that measures the temperature of production system's
        :term:`heater`. The application receives its measurements in the
        form of the *temperature sensor voltage*, however, and in order
        to determine which heating temperature a given voltage corresponds
        to, the system needs to be :term:`calibrated <calibration>`.

        If the heater is not in its foremost position, the reported voltage
        will not be an accurate reflection of the heater’s temperature. Also,
        the temperature sensor can be moved aside by the user for easier
        access to the production system. If it is, the temperature sensor
        voltage will be unrelated to the actual heating temperature.

    temperature sensor voltage
        The voltage, always expressed in V, the application receives from
        the production system's :term:`temperature sensor`. Used to estimate
        the :term:`heating temperature` if the system is :term:`calibrated
        <calibration>`.

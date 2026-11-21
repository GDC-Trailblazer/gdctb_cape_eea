.. _reference:

*************
API Reference
*************

Housekeeping packets
====================

Read a binary APID 265 housekeeping file into an Astropy ``TimeSeries``::

    from gdctb_cape_eea.io import read_raw_hk

    hk = read_raw_hk("housekeeping.bin")
    print(hk.time, hk["T_FEE"])

Times use the same conversion as the L1 CDF pipeline. Packet columns retain
their original names and contain raw, uncalibrated values; fill fields are
excluded. The housekeeping processing path uses this reader and rejects files
containing other APIDs. ``l0_hk_data_to_cdf`` accepts either the resulting
``TimeSeries`` or a dictionary from ``parse_hk_packets``.

.. automodapi:: gdctb_cape_eea
.. automodapi:: gdctb_cape_eea.calibration.calibration
.. automodapi:: gdctb_cape_eea.io.file_tools
.. automodapi:: gdctb_cape_eea.stepper.StepperTable
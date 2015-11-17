FRAMEWORK ARCHITECTURE
----------------------

COMPONENTS

    ACTIVE ITEMS 
        equipment.py            base class. Only derived class must be used
        eqpt1850tss320.py       describe a 1850TSS320 equipment and some variant
        instrumentONT.py        describe a ONT Instrument family
        instrumentIXIA.py       describe a IXIA Instrument     - tbd
        instrumentSPIRENT.py    describe a IXIA Instrument     - tbd
        instrumentSM3300.py     describe a SM3300 Instrument   - tbd

    EQUIPMENT PLUGINS
        plugin_cli.py           1850TSS320 CLI interface
        plugin_tl1.py           1850TSS320 TL1 interface
        plugin_snmp.py          1850TSS320 SNMP interface      - tbd
        plugin_dgb.py           1850TSS320 Debug interface     - tbd

    EQUIPMENT FACILITIES
        facility1850.py         utilities
        access1850.py           accessing equipment via SSH or Serial console
        swp1850tss320.py        describe a TSS1850 SWP

    KATE INTERFACE MODULES
        kenviron.py             K@TE Execution Environment for a Test script
        kpreset.py              describe a Test Presettings
        database.py             DB access API

    REPORTING
        kunit.py                management of XML reporting
        klogger.py              management of logs              - tbd
        ktracer.py              management of trace             - tbd

    DEMO
        testcase.py
        testcase.py.prs



GENERAL DESCRIPTION

A Test script (testcase.py) foreseens a configuration file (testcase.py.prs) with current presets
for a running session. The Presettings file is a JSON based text file, filled by K@TE Application
or manually from expert user.

The K@TE Application supplies a test script template for a specific Test Topology. On test script
a preamble section declare all active items variables foreseens for the Topoloty and the correct
initialization of KEnvironment variable.
Each Active Item will be instantiated with a text label (the label used on XML reporting to
identify each result element) and an instance to KEnvironment variable

The KEnvironment instance contains all informations regardings current test session as:
    - a Presettings variable, for accessing to presets file
    - a KUnit variable, for accessing to XML reporting
    - a Logger variable, for log management (tbd)
    - a Tracer variable, for trace management (tbd)
    - a list of paths for running environment (logs, test results, event collection, etc)



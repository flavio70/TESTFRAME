#!/usr/bin/env python
'''
TestCase template for K@TE test developers

[DESCRIPTION]
    Put your test decription here
[DESCRIPTION]
[TOPOLOGY] 1 [TOPOLOGY]
[DEPENDENCY]
    Insert Test dependencies
[DEPENDENCY]
[LAB] Insert the lab referneces i.e. SW,SVT [LAB]
[TPS]
    insert here the Test mapping
[TPS]
[RUNSECTIONS]
    Insert here the sections developed in this test i.e.
    DUTSet,testSet,testBody,testClean,DutClean,all
[RUNSECTIONS]
[AUTHOR] ippolf [AUTHOR]

'''

from katelibs.testcase          import TestCase
from katelibs.eqpt1850tss320    import Eqpt1850TSS320
from katelibs.instrumentONT     import InstrumentONT
#from katelibs.instrumentIXIA     import InstrumentIXIA
#from katelibs.instrumentSPIRENT  import InstrumentSPIRENT
from katelibs.swp1850tss320     import SWP1850TSS


class Test(TestCase):
    '''
    this class implements the current test case behaviour by using
    the five methods (runSections):
        DUTSetUp: used for DUT configuration
        testSetup: used for Test Configuration
        testBody: used for main test pourposes
        testCleanUp: used to finalize test and clear the configuration
        DUTCleanUp: used for DUT cleanUp

        all these runSections can be either run or skipped using inline optional input parameters

        --DUTSet     Run the DUTs SetUp
        --testSet    Run the Test SetUp
        --testBody   Run the Test Main Body
        --testClean  Run the Test Clean Up
        --DUTClean   Run the DUTs Clean Up

        all runSections will be executed if run Test without input parameters
    '''


    def dut_setup(self):
        '''
        DUT Setup section Implementation
        insert DUT SetUp code for your test below
        '''
        THE_SWP = SWP1850TSS()
        # temporaneo
        THE_SWP.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

        #NE1.flc_ip_config()

        NE1.flc_load_swp(THE_SWP)

        #NE1.flc_scratch_db()
        #NE1.flc_reboot()
        #NE1.flc_ip_config()
        #NE1.flc_wait_in_service()


        #NE1.tl1.do("ACT-USER::admin:::Root1850;")
        #NE1.tl1.do("ED-PID::admin:::Root1850,Alcatel1,Alcatel1;")
        #NE1.tl1.do("SET-PRMTR-NE::::::REGION=ETSI,PROVMODE=MANEQ-AUTOFC;")
        #NE1.tl1.do("RTRV-PRMTR-NE;")
        #NE1.tl1.do("SET-ATTR-SECUDFLT::::::MAXSESSION=6;")
        #NE1.tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=UNVRSL320,SHELFNUM=1,SHELFROLE=MAIN;")
        #NE1.tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=160H,SHELFNUM=1,SHELFROLE=MAIN;")


    def test_setup(self):
        '''
        test Setup Section implementation
        insert general SetUp code for your test below
        '''
        #self.kenvironment.krepo.start_tps_block("EM", "1-2-3")
        NE1.tl1.do("ACT-USER::admin:::Alcatel1;")
        NE1.cli.connect()


    def test_body(self):
        '''
        test Body Section implementation
        insert Main body code for your test below
        '''
        self.trc_inf(" 1. Condizione iniziale")
        NE1.cli.do("linkagg show")

        # lag      AdminKey    LAG User Label                     LAG Size Admin State
        # ======== =========== ================================== ======== ===============
        #
        # .. message: not found Entry

        self.trc_inf(" 2. Creazione di una LAG (EXPECTED SUCCESS)")
        NE1.cli.do("linkagg activate lag1 size 2 adminkey  1 ets lagname LAG_1", policy="COMPLD", timeout=20)
        #
        # .. message: successful completed command
        #

        self.trc_inf(" 3. SHOW delle LAG create")
        NE1.cli.do("linkagg show")
        #
        # lag      AdminKey    LAG User Label                     LAG Size Admin State
        # ======== =========== ================================== ======== ===============
        # 1        1           'LAG_1'                            2        enable

        self.trc_inf(" 4. Show della LAG1 ")
        NE1.cli.do("linkagg show lag1")
        # 
        # Link Aggregation Info of lag1
        # -----------------------------
        # LAG Number: lag1
        # LAG User Label: 'LAG_1'
        # LAG Size: 2
        # ...

        self.trc_inf(" 5. EDIT LAG con valore del campo size fuori range (expected Deny da parte della CLI)")
        self.trc_inf("    NB: i deny dati direttamente dalla CLI non hanno sempre output univoco,")
        self.trc_inf("    cmq solitamente contengono 'Error' oppure 'unsuccessful'")
        NE1.cli.do("linkagg config lag1 size 20", policy="COMPLD", timeout=20)
        #                                ^
        # Error: Out of range. Valid range is: 1 - 16

        self.trc_inf(" 6. EDIT LAG con valore ammissibile  del campo size (expected SUCCESS)")
        NE1.cli.do("linkagg config lag1 size 10", policy="COMPLD", timeout=20)
        #                                ^
        # .. message: successful completed command

        self.trc_inf(" 7. EDIT parametro LACP della LAG (expected Deny da parte della CLI)")
        NE1.cli.do("linkagg config lag1 lacp disable", policy="COMPLD", timeout=20)
        # 
        # .. message: enabled Lag; refused change of param lacp
        # 
        # .. message: unsuccessful completed command

        self.trc_inf(" 8. EDIT Dello stato amministrativo: Disable, del parametro LACP e ancora dello")
        self.trc_inf("    stato amministrativo Enable (EXPECTED SUCCESS)")
        NE1.cli.do("linkagg config lag1 adminstate disable", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command
        # 
        NE1.cli.do("linkagg config lag1 lacp disable", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command
        # 
        NE1.cli.do("linkagg config lag1 adminstate enable", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command
        # 

        self.trc_inf(" 11. Show delle VPLS  (expected nessuna)")
        NE1.cli.do("vpls show")
        # 
        # LabelKey     vpls VpnId                       Status
        # ============ ================================ ===============
        # 
        # .. message: not found Entry

        self.trc_inf(" 12. Creazione VPLS e bind della LAG (expected SUCCESS)")
        NE1.cli.do("vpls activate  VPLAG portset lag1", policy="COMPLD", timeout=20)
        # 
        # .. message: successful completed command

        self.trc_inf(" 13. Show delle VPLS")
        NE1.cli.do("vpls show")
        # 
        # LabelKey     vpls VpnId                       Status
        # ============ ================================ ===============
        # @1           'VPLAG'                          active

        self.trc_inf(" 14. Show della VPLS VPLAG")
        NE1.cli.do("vpls show VPLAG")
        # 
        # VPLS Info
        # ---------
        # vpls VpnId: 'VPLAG'
        # vpls Name: ''
        # vpls Descr: ''
        # ...

        self.trc_inf(" 15. Creazione di una xconnessione NNI-UNI tra la Vpls e la LAG")
        NE1.cli.do("pbflowoutunidir activate test_VPLS_LAG  port lag1 vpls VPLAG outtraffictype be", policy="COMPLD", timeout=30)
        # 
        # .. message: successful completed command

        self.trc_inf(" 16. Show dei Traffic Descriptor ")
        NE1.cli.do("trafficdescriptor show")
        # 
        # LabelKey UserLabel              Status Type  cir      pir      cbs      pbs
        # ======== ====================== ====== ===== ======== ======== ======== ========
        # @1       'nullBeTD'             active be    0        0        0        0

        self.trc_inf(" 17. Cancellazione del TrafficDescriptor  (expected DENY da parte dell'AGENT perche' in uso)")
        self.trc_inf("     N.B.: i Deny dell'agent provocano sempre il messaggio 'error: db writing error'")
        NE1.cli.do("trafficdescriptor delete  nullBeTD", policy="COMPLD", timeout=20)
        # 
        # >> error: db writing error for Status=destroy of 1
        # 
        # .. message: unsuccessful completed command

        self.trc_inf(" 18. Cancellazione della VPLS (expected DENY da parte dell'AGENT per la presenza")
        self.trc_inf("     della xconnessione)")
        NE1.cli.do("vpls delete VPLAG", policy="COMPLD", timeout=10)
        # 
        # >> error: db writing error for vplsConfigStaticEgressPorts=
        #    [00] repeats 512 times of 1
        # 
        # .. message: unsuccessful completed command

        self.trc_inf(" 19. Cancellazione della xconnessione (expected Success)")
        NE1.cli.do("pbflowoutunidir delete test_VPLS_LAG", policy="COMPLD", timeout=20)
        # 
        # .. message: successful completed command

        self.trc_inf(" 20. Cancellazione del TrafficDescriptor (expected Success)")
        NE1.cli.do("trafficdescriptor delete  nullBeTD", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command

        self.trc_inf(" 21. Cancellazione dela VPLS (expected Success)")
        NE1.cli.do("vpls delete VPLAG", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command

        self.trc_inf(" 22. Cancellazione della Lag (Expected Success)")
        NE1.cli.do("linkagg delete lag1", policy="COMPLD", timeout=10)
        # 
        # .. message: successful completed command

        self.trc_inf(" 23. Show delle LAG, delle VPLS, dei TrafficDescriptor e delle")
        self.trc_inf("     Xconnessioni NNI-UNI (expected: vuoto)")
        NE1.cli.do("linkagg show")
        # 
        # lag      AdminKey    LAG User Label                     LAG Size Admin State
        # ======== =========== ================================== ======== ===============
        # 
        # .. message: not found Entry

        NE1.cli.do("vpls show")
        # 
        # LabelKey     vpls VpnId                       Status
        # ============ ================================ ===============
        # 
        # .. message: not found Entry

        NE1.cli.do("trafficdescriptor show")
        # 
        # LabelKey UserLabel              Status Type  cir      pir      cbs      pbs
        # ======== ====================== ====== ===== ======== ======== ======== ========
        # 
        # .. message: not found Entry

        NE1.cli.do("pbflowoutunidir show")
        # 
        # 
        # .. message: not found Cross Connection




        #NE1.cli.do("interface show", policy="COMPLD", condition=".. message: not found interface\n", timeout=10)

        #NE1.cli.do_until("interface show", condition=".. message: not found interface\n", timeout=10)


    def test_cleanup(self):
        '''
        test Cleanup Section implementation
        insert CleanUp code for your test below
        '''


    def dut_cleanup(self):
        '''
        DUT CleanUp Section implementation
        insert DUT CleanUp code for your test below
        '''
        print('@DUT CleanUP')
        #self.kenvironment.krepo.stop_tps_block("EM", "1-2-3")


#Please don't change the code below#
if __name__ == "__main__":
    #initializing the Test object instance, do not remove
    CTEST = Test(__file__)

    #initializing all local variable and constants used by Test object
    NE1 = Eqpt1850TSS320('NE1', CTEST.kenvironment)
    #ONT1 = instrumentONT('ONT1', CTEST.kenvironment)
    #ONT2 = instrumentONT('ONT2', CTEST.kenvironment)

    # Run Test main flow
    # Please don't touch this code
    CTEST.run()

    #ONT2.clean_up()
    #ONT1.clean_up()
    NE1.clean_up()

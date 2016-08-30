#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  instrumentIXIA.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  18/02/2016
#       :  01/07/2016: starting library expansion for LAG creation 
#       :  20/07/2016: added VLAN/INNER VLAN/MPLS 
#       :  01/08/2016: added TX/RX traffic counters retrieve 
#       :  03/08/2016: added VLAN/MPLS on the fly changes support
#
#
# DETAILS: Python management module for IXIA test equipments
#
# MODULE:  instrumentIXIA.py
#
#
###############################################################################
"""

import os
import sys
import time
import string
import getpass
import inspect
import telnetlib
import datetime
import socket

from katelibs.equipment import Equipment
#from katelibs.kenviron import KEnvironment
from katelibs.kunit import Kunit
from katelibs.database import *
from katelibs.IxNetwork import *

class InstrumentIXIA(Equipment):
    def __init__(self, label, kenv):
        """ label   : equipment name used on Report file
            kenv    : instance of KEnvironment (initialized by K@TE FRAMEWORK)
        """
        # Enviroment
        self.__kenv                 = kenv             # Kate Environment
        self.__krepo                = kenv.krepo       # result report (Kunit class instance)
        self.__prs                  = kenv.kprs        # Presets for running environment
        # Bridge Connection
        #self.___IXNworkServerAddress      = "135.221.116.175"  # ixnetwork server address v8.01
        self.___IXNworkServerAddress       = "151.98.141.200"   # New ixnetwork server address v8.01 (since June 2016)
        self.___IXNworkServerPort          = 8009               # ixnetwork server port
        self.___IXNworkServerVersion       = '8.00'             # ixnetwork server port
        #Data model (DM) main hooks
        self.__remapIds  = True
        self.__IXN  = None
        self.__ROOT = None
        self.__NULL = None
        self.__calledMethodStatus   = dict()           #  used to track all method called and last execution result
        self.__vPortList            = dict()
        self.__vPortMediaType       = dict()
        self.__vPortEnableFlowCTRL  = dict()
        self.__vPortAutoNegotiate   = dict()
        self.__vPortAutoNegotiateSpeed  = dict()
        self.__vPortSpeed           = dict()
        self.__vPortLoopback        = dict()
        self.__vPortEndPointSet     = dict()
        self.__alreadyAddedVPort    = []
        self.__alreadyBoundVPort    = []
        self.__vPortHanlerLACPLink  = dict()
        self.__flowName2streamIndexMap = dict()        
        self.__globalTrafficItem    = None
        self.__globalEgressTracking = None             # IMHO setup for traffic parameters (quick flow default setups)  
        
        self.__globalStatisticView  = None             # added for custom statistics view (Valeria Sanvito)   
        self.__globalLayer23ProtoPortFilter  = None    # added for custom statistics view (Valeria Sanvito)  
        
        self.__lastCallSuccess      = False
        self.__totalStreamNumber    = 0
        self.__vPortToStreamMap     = []
        
        ## !!! Don't delete the next lines !!!
        super().__init__(label, self.__prs.get_id(label))
        self.__get_instrument_info_from_db(self.__prs.get_id(label)) # inizializza i dati di IP, tipo di Strumento ecc... dal DB


    #
    #   USEFUL FUNC & TOOLS
    #
    def __ret_func(self, TFRetcode=True, MsgLevel="none", localMessage="Put here the string to self.__lc_msg"  ):       ### krepo noy added ###
        methodLocalName = self.__lc_caller_method_name()
        if MsgLevel == "error":self.__trc_err(localMessage)
        elif MsgLevel == "none":pass
        else:self.__trc_inf(localMessage)
        if TFRetcode == True:self.__method_success(methodLocalName, None, localMessage)
        else:self.__method_failure(methodLocalName, None, "", localMessage)
        return TFRetcode, localMessage


    def __lc_current_method_name(self, embedKrepoInit=False):
        methodName = inspect.stack()[1][3]   # <-- daddy method name  : who calls __lc_current_method_name
        self.__lc_msg ("\n[{}] method Call ... Krepo[{}]".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:self.__krepo.start_time()
        return methodName


    def __lc_caller_method_name(self, embedKrepoInit=False):
        methodName = inspect.stack()[2][3]   # <-- two levels of call
        self.__lc_msg ("\n[{}] method caller ... Krepo[{}]".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:self.__krepo.start_time()
        return methodName


    #
    #   BRIDGE CONNECTION MANAGEMENT
    #
    def connect_ixnetwork(self):       ### krepo added ###
        """ 
            Procedure:
                connect_ixnetwork(self) - Hint: first call to use to access to Ixia Chassis

            Purpose:
                create a bridge connection: it must be called one time only @ test/dut setup

            Return tuple:
                ("True|False" , "answer_string"  )
                True.............connection success
                False............connection failed
                answer_string....message for humans, to better understand
                                 what happened in the processing flow
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        if self.__IXN != None:
            return self.__ret_func(False,"error", "BridgeHandler [{}] already allocated. Disconnect before!".format(self.__IXN))
        self.__IXN = IxNet()
        try:
            answerBridge = self.__IXN.connect(self.___IXNworkServerAddress,'-port', self.___IXNworkServerPort,'-version', self.___IXNworkServerVersion)
        except Exception as excMsg:
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connection failed: check ixNetwork server[{}] port[{}] [{}]".format(self.___IXNworkServerAddress,self.___IXNworkServerPort,excMsg))
        if answerBridge != "::ixNet::OK":
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connect() answer not expected:[{}] instead of [::ixNet::OK]".format(answerBridge))
        result1 = self.__IXN.execute('newConfig')
        self.__lc_msg("newConfig result [{}]".format(result1))
        self.__ROOT = self.__IXN.getRoot()
        self.__NULL = self.__IXN.getNull()
        return self.__ret_func(True,"success", "[{}] [{}] - self.__ROOT now [{}]".format(methodLocalName,answerBridge,self.__ROOT) )



    def add_single_vport(self, vPortId, 
                         customName=None,
                         receiveMode="capture",
                         mediaType="fiber",
                         enabledFlowControl=True, 
                         autoNegotiate=True, 
                         speedAuto=['all'],  # allowed values: ['all'] or (one combination of) the following ['speed10fd', 'speed10hd', 'speed100fd', 'speed100hd', 'speed1000'] 
                         speed="speed1000",  # allowed values: speed10fd, speed10hd, speed100fd, speed100hd, speed1000 
                         loopback=False ):    
        """ 
            Procedure:
                add_single_vport 
            
            Purpose:
                add a port to the port list with the specified L1 parameters
            
            Parameters: 
                vPortId................ vport id specified as TUPLE ('<IP Address Chassis>',<card number> ,<port number>), 
                                        e.g. ('151.98.130.42', 2, 1)   
                customName............. Default: None
                                        Used to specify Port names different from the default "Ethernet - 001", 
                                        "Ethernet - 002" (,...)  assigned names
                                        Specify a custom name as a string between "" (quotes):
                                        E.g. #1  customName="Porta test 1" 
                                        E.g. #2  customName="Test Fumagalli" 
                receiveMode............ Default: capture if no parameter is specified (this value is a need to enable Vlan Tagged Frames Counters
                                        Allowed values: 
                                          "capture" (Required by V. Sanvito )
                                          "captureAndMeasure"  
                                        E.g. #1: receiveMode="capture"
                                        E.g. #2: receiveMode="captureAndMeasure"
                mediaType.............. Default: Fiber 
                                        Physical transport tecnology selection: "fiber" or "copper" port module 
                enabledFlowControl..... Default: True. 
                                        True (or False) to enable (or disable) Flow Control.   
                autoNegotiate.......... Default: True
                                        True (or False) to enable (or disable) Auto Negotiation.  
                speedAuto.............. Default: ['all'] and all speeds are used, if "speedAuto" is not specified.
                                        ONLY IF AUTONEGOTIATE IS TRUE: 
                                        it specifies the speed 10,100,1000 and mode (Half/Full Duplex) 
                                        to use in autonegotiation.
                                        Allowed values:
                                        to restrict the set of the speed/mode to use may be specified in
                                        a list (use the [] parentesis ) that is a subset of 
                                        the following  complete list: 
                                        ['speed10fd', 'speed10hd', 'speed100fd', 'speed100hd', 'speed1000'] 
                                        E.g. #1: speedAuto=['speed10fd', 'speed10hd']
                                        E.g. #2: speedAuto=['speed100fd', 'speed100hd', 'speed1000']                                        
                speed.................. Default is "speed1000"  if "speed" is not specified.
                                        ONLY IF AUTONEGOTIATE IS FALSE: 
                                        it specifies the port speed and mode.
                                        Allowed values:
                                        one of the following strings, passed as strings between "" (quotes):
                                        "speed10fd", "speed10hd", "speed100fd", "speed100hd" or "speed1000" 
                                        E.g. #1: speed="speed10fd"
                                        E.g. #2: speed="speed1000"
                loopback............... Default: False. 
                                        True (or False) to enable (or disable)  port internal loopback. 
            
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............connection success
                False............connection failed
                answer_string....message for humans, to better understand
                                 what happened in the processing flow
        """
        methodLocalName = self.__lc_current_method_name()
        if vPortId in self.__alreadyAddedVPort:
           return  False, "ERROR: [{}] vPort [{}] already added: unable to add it again.".format(methodLocalName,vPortId)
        localVport   = self.__IXN.add(self.__ROOT, 'vport')
        self.__IXN.commit()
        localVport = self.__IXN.remapIds(localVport)[0]
        # Media type fiber/copper    
        if mediaType == "fiber" or mediaType == "FIBER" :
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-media','fiber')
        else:
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-media','copper')
        # Loopback
        if loopback == True:
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-loopback','true')
        else:    
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-loopback','false')
        # Flow Control
        if enabledFlowControl == True:
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-enabledFlowControl','true')
        else:    
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-enabledFlowControl','false')
        # Autonegotiation
        if autoNegotiate == True:
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-autoNegotiate','true')
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-speedAuto',speedAuto)
        else:    
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-autoNegotiate','false')
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-speed',speed)
        # customName
        if customName != None:
            self.__IXN.setAttribute(localVport ,'-name', customName)
        # receiveMode 
        if receiveMode != "captureAndMeasure":
            self.__IXN.setAttribute(localVport ,'-rxMode', 'capture')
        # Add new created vport parameters to internal dictionaries    
        self.__vPortList[vPortId]               = localVport
        self.__vPortMediaType[vPortId]          = mediaType 
        self.__vPortEnableFlowCTRL[vPortId]     = enabledFlowControl  
        self.__vPortAutoNegotiate[vPortId]      = autoNegotiate 
        self.__vPortAutoNegotiateSpeed[vPortId] = speedAuto 
        self.__vPortSpeed[vPortId]              = speed     
        self.__vPortLoopback[vPortId]           = loopback 
        """
        # Additional configs raised in in the add L2-3 Quick Flow Group setup process
        self.__IXN.setMultiAttribute(localVport+'/protocolStack/options', 
            '-routerSolicitationDelay', '1', 
            '-routerSolicitationInterval', '4', 
            '-routerSolicitations', '3', 
            '-retransTime', '1000', 
            '-mcast_solicit', '3', 
            '-dadTransmits', '1', 
            '-dadEnabled', 'true', 
            '-ignoreMldQueries', 'false', 
            '-ipv4RetransTime', '3000', 
            '-ipv4McastSolicit', '4')



        self.__IXN.setMultiAttribute(localVport+'/capture', 
                        '-controlCaptureTrigger', '', 
                        '-controlCaptureFilter', '', 
                        '-controlBufferBehaviour', 'bufferLiveNonCircular', 
                        '-dataReceiveTimestamp', 'chassisUtcTime', 
                        '-controlSliceSize', '0', 
                        '-beforeTriggerFilter', 'captureBeforeTriggerNone', 
                        '-triggerPosition', '1', 
                        '-continuousFilters', 'captureContinuousFilter', 
                        '-hardwareEnabled', 'false', 
                        '-sliceSize', '0', 
                        '-afterTriggerFilter', 'captureAfterTriggerFilter', 
                        '-controlInterfaceType', 'anyInterface', 
                        '-softwareEnabled', 'false', 
                        '-captureMode', 'captureTriggerMode', 
                        '-controlBufferSize', '30')

        self.__IXN.setMultiAttribute(localVport+'/capture/filterPallette', 
                        '-DAMask1', '00 00 00 00 00 00', 
                        '-DAMask2', '00 00 00 00 00 00', 
                        '-patternOffset1', '0', 
                        '-patternMask1', '00', 
                        '-patternMask2', '00', 
                        '-patternOffsetType2', 'filterPalletteOffsetStartOfFrame', 
                        '-pattern1', '00', 
                        '-SAMask2', '00 00 00 00 00 00', 
                        '-SAMask1', '00 00 00 00 00 00', 
                        '-SA1', '00 00 00 00 00 00', 
                        '-patternOffsetType1', 'filterPalletteOffsetStartOfFrame', 
                        '-SA2', '00 00 00 00 00 00', 
                        '-DA2', '00 00 00 00 00 00', 
                        '-pattern2', '00', 
                        '-DA1', '00 00 00 00 00 00', 
                        '-patternOffset2', '0')

        self.__IXN.setMultiAttribute(localVport+'/capture/filter', 
                        '-captureFilterFrameSizeFrom', '64', 
                        '-captureFilterDA', 'anyAddr', 
                        '-captureFilterExpressionString', '', 
                        '-captureFilterError', 'errAnyFrame', 
                        '-captureFilterFrameSizeEnable', 'false', 
                        '-captureFilterSA', 'anyAddr', 
                        '-captureFilterPattern', 'anyPattern', 
                        '-captureFilterEnable', 'false', 
                        '-captureFilterFrameSizeTo', '1518')

        self.__IXN.setMultiAttribute(localVport+'/capture/trigger', 
                        '-captureTriggerError', 'errAnyFrame', 
                        '-captureTriggerFrameSizeEnable', 'false', 
                        '-captureTriggerFrameSizeFrom', '12', 
                        '-captureTriggerEnable', 'false', 
                        '-captureTriggerDA', 'anyAddr', 
                        '-captureTriggerExpressionString', '', 
                        '-captureTriggerPattern', 'anyPattern', 
                        '-captureTriggerSA', 'anyAddr', 
                        '-captureTriggerFrameSizeTo', '12')

        """
        self.__alreadyAddedVPort.append(vPortId)
        #return self.__ret_func(True,"success", "[{}] Added vPort [{}]".format(methodLocalName,vPortId) )
        self.__IXN.commit()
        self.__lc_msg("[{}] Added vPort [{}]".format(methodLocalName,vPortId))
        #self.__lc_msg("vPortId] [{}]".format(vPortId))        
        #self.__lc_msg("self.__vPortList[vPortId][{}]".format(self.__vPortList[vPortId]))
        #self.__lc_msg("self.__vPortMediaType[vPortId][{}]".format(self.__vPortMediaType[vPortId]))
        #self.__lc_msg("self.__vPortEnableFlowCTRL[vPortId][{}]".format(self.__vPortEnableFlowCTRL[vPortId]))
        #self.__lc_msg("self.__vPortAutoNegotiate[vPortId][{}]".format(self.__vPortAutoNegotiate[vPortId]))
        #self.__lc_msg("self.__vPortAutoNegotiateSpeed[vPortId][{}]".format(self.__vPortAutoNegotiateSpeed[vPortId]))
        #self.__lc_msg("self.__vPortSpeed[vPortId][{}]".format(self.__vPortSpeed[vPortId]))
        #self.__lc_msg("self.__vPortLoopback[vPortId][{}]".format(self.__vPortLoopback[vPortId]))
        #self.__lc_msg("<<< === DICT add_single_vport ===")
        #self.__lc_msg("self.__alreadyAddedVPort NOW:[{}] ".format(self.__alreadyAddedVPort))
        return  True, "[{}] Added vPort [{}]".format(methodLocalName,vPortId)



    def bind_new_vports(self):
        """
            Procedure:
                bind_new_vports 

            Purpose:
                Execute the logic-to-physical ports connections
                for all the ports created (add_single_vport) after
                the last bind_new_vports() call.

            Parameters: 
                none

            Return tuple:
                ("True|False" , "answer_string"  )
                True.............connection success
                False............connection failed
                answer_string....message for humans, to better understand
                                 what happened in the processing flow

            Additional Information:  
                this procedure executes this task on all the vPorts already created but not bound 
                to their related physical port, in order to allow port creation "on the fly" 
                in future (not only at test beginning (Sergio Missineo req.)
                The list of all the ports, their configuration and their bind state is internally 
                maintained and managed by the InstrumentIXIA class, and for all the ports, 
                their ID=('<ip addr chassis>', <card>, <port>)  is the key to access to all these info
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        #self.__lc_msg("[{}] vportlist [{}]".format(methodLocalName,vportlist))
        localVportList = []
        vportlist      = []        
        somethingToDo=False
        #self.__lc_msg("[{}] self.__alreadyBoundVPort [{}]".format(methodLocalName,self.__alreadyBoundVPort))
        #self.__lc_msg("[{}] self.__alreadyAddedVPort [{}]".format(methodLocalName,self.__alreadyAddedVPort))
        
        
        
        for localVportId in self.__alreadyAddedVPort:
            if  localVportId not in self.__alreadyBoundVPort:
                localVportList.append(self.__vPortList[localVportId])
                vportlist.append(localVportId)
                self.__alreadyBoundVPort.append(localVportId)
                #self.__lc_msg("localVportList [{}]".format(localVportList))
                self.__lc_msg("Bind port [{}]".format(localVportId)) 
                somethingToDo=True
                #self.__lc_msg("[{}] self.__alreadyBoundVPort [{}]".format(methodLocalName,self.__alreadyBoundVPort))
                #self.__lc_msg("[{}] self.__alreadyAddedVPort [{}]".format(methodLocalName,self.__alreadyAddedVPort))
            else:
                self.__lc_msg("Port [{}] already bound".format(localVportId))
        if somethingToDo == True:
            self.__lc_msg("[{}] Assigning port in progress...(in timeout case, please check if the chassis is reacheable/switched-on) ".format(methodLocalName))
            #self.__lc_msg("[{}] already bound".format(localVportId))
            assignPorts = self.__IXN.execute('assignPorts', vportlist, [], localVportList, True)
            self.__lc_msg("assignPorts [{}] After".format(assignPorts))
            return self.__ret_func(True,"success", "[{}] Added vPorts [{}]".format(methodLocalName,vportlist))
        else:
            self.__lc_msg("assignPorts [{}]".format(assignPorts))
            return self.__ret_func(False,"error", "[{}] no vPorts to add".format(methodLocalName))

 

    def enable_disable_lacp_protocol(self, vPortId,  
                                     enable=True,
                                     actorKey=1,
                                     actorPortNumber=1,
                                     actorPortPriority=1,
                                     actorSystemId='00:00:00:00:00:01',
                                     actorSystemPriority=1,
                                     administrativeKey=1,
                                     linkEnabled=True,
                                     autoPickPortMac=True,
                                     portMac= '00:00:00:00:00:01'):    
        """ 
            Procedure:
                enable_disable_lacp_protocol 

            Purpose:
                Enable or disable LACP protocol for the specified vPortId port

            Usage:
                To disable the LACP protocol for a specified port (called vport in the internal IXIA logical rapresentation)
                simply specify:
                    enable=False
                in as parameter the procedure call.
                To enable the LACP protocol, call the procedure passing the necessary parameters that you need to change
                respect to the defaults internally specified

            Parameters:
                vPortId................ vport id specified as TUPLE ('<IP Address Chassis>',<card number> ,<port number>), 
                                        e.g. ('151.98.130.42', 2, 1)   
                enable................. True(default)/False to Enable/Disable the LACP protocol for the port
                actorKey............... Default=1 
                                        Specify a custom number  to change it:
                                        E.g. #1  actorKey=2 
                                        E.g. #2  actorKey=1 
                actorPortNumber........ Default=1, specify actorPortNumber=<number> to change it 
                                        Specify a custom number  to change it:
                                        E.g. #1  actorPortNumber=2 
                                        E.g. #2  actorPortNumber=3 
                actorPortPriority...... Default=1, specify actorPortPriority=<number> to change it  
                                        Specify a custom number  to change it:
                                        E.g. #1  actorPortPriority=2 
                                        E.g. #2  actorPortPriority=3 
                actorSystemId.......... Default="00:00:00:00:00:01"
                                        Specify a custom actorSystemId as a string between "" (quotes):
                                        E.g. #1  actorSystemId="00:00:ab:00:00:01" 
                                        E.g. #2  actorSystemId="00:00:cd:00:00:01"                
                actorSystemPriority.... Default=1 
                                        Specify a custom number actorSystemPriority=<number>   to change it:
                                        E.g. #1  actorSystemPriority=2 
                                        E.g. #2  actorSystemPriority=3 
                administrativeKey...... Default=1 
                                        Specify a custom number administrativeKey=<number>   to change it:
                                        E.g. #1  administrativeKey=2 
                                        E.g. #2  administrativeKey=3 
                linkEnabled............ True (default) or False if specified with linkEnabled=False
                autoPickPortMac.........Default: True
                                        When specified as False, the port mac is set using the 
                                        portMac custom value. 
                portMac................ Default="00:00:00:00:00:01"  
                                        Specify a custom port mac address as a string between "" (quotes):
                                        BE CARE: to enable this parameter, the you need to specify autoPickPortMac=False too.
                                        E.g. #1  portMac="00:00:ab:00:00:01", autoPickPortMac=False  (Needed:  autoPickPortMac=False !!!)
                                        E.g. #2  portMac="00:00:cd:00:00:01", autoPickPortMac=False  (Needed:  autoPickPortMac=False !!!)

                Return tuple:
                    ("True|False" , "answer_string"  )
                    True.............connection success
                    False............connection failed
                    answer_string....message for humans, to better understand
                                     what happened in the processing flow
        """
        methodLocalName = self.__lc_current_method_name()
        if vPortId == None:
           return  False, "ERROR: [{}] vPortId [{}] not specified".format(methodLocalName,vPortId)
        if vPortId not in self.__alreadyAddedVPort: 
           return  False, "ERROR: [{}] vPortId [{}] not initialized (have you executed bind_new_vports() ?)".format(methodLocalName,vPortId)
        if enable == False: # disable LACP protocol
            self.__IXN.setMultiAttribute(self.__vPortList[vPortId]+'/protocols/lacp','-enablePreservePartnerInfo', 'false', '-enabled', 'false')
            self.__IXN.commit()
            self.__lc_msg("[{}] Disabled LACP for vPort [{}]".format(methodLocalName,vPortId))
            if vPortId  in self.__vPortHanlerLACPLink.keys():
                del self.__vPortHanlerLACPLink[vPortId]
            else:
                self.__lc_msg("[{}] LACP already disabled for vPort [{}]".format(methodLocalName,vPortId))
            return  True, "[{}] Disabled LACP for vPort [{}]".format(methodLocalName,vPortId)
        else:
            self.__lc_msg("[{}] Enabled LACP for vPort [{}]".format(methodLocalName,vPortId))
            self.__IXN.setMultiAttribute(self.__vPortList[vPortId]+'/protocols/lacp', '-enablePreservePartnerInfo', 'false', '-enabled', 'true')
            self.__IXN.commit()
        """    
        if vPortId in self.__vPortHanlerLACPLink: 
            self.__lc_msg( "ERROR: LACP for vPort [{}] ALREADY ENABLED".format(methodLocalName,vPortId))
            return  False, "[{}] Disabled LACP for vPort [{}]".format(methodLocalName,vPortId)
        """
        #self.__vPortHanlerLACPLink[vPortId] =  self.__IXN.add(self.__vPortList[vPortId]+'/protocols/lacp', 'link')
        localLACPLink =  self.__IXN.add(self.__vPortList[vPortId]+'/protocols/lacp', 'link')
        """
        #self.__IXN.setMultiAttribute(self.__vPortHanlerLACPLink[vPortId], 
                        #'-actorKey',  actorKey, 
                        #'-actorPortNumber', actorPortNumber, 
                        #'-actorPortPriority', actorPortPriority,
                        #'-actorSystemId', actorSystemId,
                        #'-actorSystemPriority', actorSystemPriority,      
                        #'-administrativeKey', administrativeKey,    
                        #'-aggregationFlagState', 'auto', 
                        #'-autoPickPortMac', autoPickPortMac, 
                        #'-collectingFlag', True, 
                        #'-collectorMaxDelay', 0, 
                        #'-distributingFlag', True, 
                        #'-enabled', linkEnabled,      
                        #'-interMarkerPduDelay', 6, 
                        #'-lacpActivity', 'active', 
                        #'-lacpTimeout', 0, 
                        #'-lacpduPeriodicTimeInterval', 0, 
                        #'-markerRequestMode', 'fixed', 
                        #'-markerResponseWaitTime', 5, 
                        #'-portMac', portMac,  
                        #'-sendMarkerRequestOnLagChange', True, 
                        #'-sendPeriodicMarkerRequest', False, 
                        #'-supportRespondingToMarker', True, 
                        #'-syncFlag', 'auto')
        """                
        self.__IXN.setMultiAttribute(localLACPLink, 
                        '-actorKey',  actorKey, 
                        '-actorPortNumber', actorPortNumber, 
                        '-actorPortPriority', actorPortPriority,
                        '-actorSystemId', actorSystemId,
                        '-actorSystemPriority', actorSystemPriority,      
                        '-administrativeKey', administrativeKey,    
                        '-aggregationFlagState', 'auto', 
                        '-autoPickPortMac', autoPickPortMac, 
                        '-collectingFlag', True, 
                        '-collectorMaxDelay', 0, 
                        '-distributingFlag', True, 
                        '-enabled', linkEnabled,      
                        '-interMarkerPduDelay', 6, 
                        '-lacpActivity', 'active', 
                        '-lacpTimeout', 0, 
                        '-lacpduPeriodicTimeInterval', 0, 
                        '-markerRequestMode', 'fixed', 
                        '-markerResponseWaitTime', 5, 
                        '-portMac', portMac,  
                        '-sendMarkerRequestOnLagChange', True, 
                        '-sendPeriodicMarkerRequest', False, 
                        '-supportRespondingToMarker', True, 
                        '-syncFlag', 'auto')
        localLACPLink = self.__IXN.remapIds(localLACPLink)[0]
        self.__vPortHanlerLACPLink[vPortId]= localLACPLink
        
        self.__IXN.commit()
        return  True, "[{}] Added and Enabled LACP for vPort [{}]".format(methodLocalName,vPortId)



    def init_traffic(self, trafficName        = 'Traffic RAW',
                       trafficType            = 'raw',
                       allowSelfDestined      = False,
                       trafficItemType        = 'quick',
                       mergeDestinations      = True,
                       egressEnabled          = False,
                       srcDestMesh            = 'oneToOne',
                       enabled                = True,
                       routeMesh              = 'oneToOne',
                       transmitMode           = 'interleaved',
                       biDirectional          = True,
                       hostsPerNetwork        = 1,
                       useControlPlaneRate    = True,              
                       useControlPlaneFrameSize  = True,                
                       originatorType            =  'endUser', 
                       interAsLdpPreference      = 'two', 
                       ordinalNo                 = '0', 
                       transportLdpPreference    = 'two', 
                       interAsBgpPreference      = 'one', 
                       enableDynamicMplsLabelValues = False, 
                       transportRsvpTePreference    = 'one', 
                       maxNumberOfVpnLabelStack     = '2', 
                       roundRobinPacketOrdering     = False, 
                       numVlansForMulticastReplication = '1', 
                       hasOpenFlow = False):
        """
            init_traffic:
                enable_disable_lacp_protocol 

            Purpose:
                Initializes the root+'/traffic', 'trafficItem' branch in order to permit to create
                the flow for each port 

            Usage:
                Before creating the single port flow you should call this procedure
                only if you need tocustomize one of the parameters in the call

                If you need a standard configuration, with the parameters specified in the function interface
                above, you can omit this procedure call: the first add_flow_to_vport() will call it for you,
                without the need to specify nothing in the call, but using the default parameters.

            Parameters:
                 trafficName         ................ Default: 'Traffic RAW'
                 trafficType	     ................ Default:.'raw'
                 allowSelfDestined   ................ Default: False  
                 trafficItemType     ................ Default: 'quick'  
                 mergeDestinations   ................ Default: True 
                 egressEnabled       ................ Default: False 
                 srcDestMesh	     ................ Default: 'oneToOne'
                 enabled	     ................ Default: True
                 routeMesh	     ................ Default: 'oneToOne'
                 transmitMode	     ................ Default: 'interleaved'
                 biDirectional       ................ Default: False
                 hostsPerNetwork     ................ Default: 1
                 useControlPlaneRate ................ Default: True         
                 useControlPlaneFrameSize............ Default: True        
                 interAsLdpPreference'   ............ Default:'two', 
                 ordinalNo               ............ Default:'0', 
                 transportLdpPreference  ............ Default:'two', 
                 interAsBgpPreference   ............. Default:'one', 
                 enableDynamicMplsLabelValues ....... Default: 'false', 
                 transportRsvpTePreference'.......... Default: 'one', 
                 maxNumberOfVpnLabelStack'........... Default: '2', 
                 roundRobinPacketOrdering'........... Default: 'false', 
                 numVlansForMulticastReplication'.... Default:'1', 
                 hasOpenFlow'........................ Default: 'false'
             Return tuple:
                    ("True|False" , "answer_string"  )
                    True.............init traffic success (or already initialized, anyway ready for the next step) 
                    False............init traffic failed
                    answer_string....message for humans, to better understand
                                     what happened in the processing flow
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] self.__globalTrafficItem  [{}]".format(methodLocalName, self.__globalTrafficItem))        
        if self.__globalTrafficItem != None: 
            localMessage = "[{}] Traffic already initialized".format(methodLocalName)
            self.__lc_msg(localMessage)
            return  True, localMessage
        localMessage = "[{}] Traffic initialization".format(methodLocalName)
        self.__lc_msg(localMessage)
        try:
            # Add TRAFFICITEM Hook
            self.__globalTrafficItem = self.__IXN.add(self.__ROOT + '/traffic', 'trafficItem')
            self.__IXN.setMultiAttribute(self.__globalTrafficItem,
                        '-originatorType', originatorType, 
                        '-hostsPerNetwork', hostsPerNetwork, 
                        '-allowSelfDestined', allowSelfDestined, 
                        '-interAsLdpPreference', interAsLdpPreference, 
                        '-name', trafficName, 
                        '-ordinalNo', ordinalNo, 
                        '-biDirectional', biDirectional, 
                        '-transportLdpPreference', transportLdpPreference, 
                        '-useControlPlaneRate',  useControlPlaneRate, 
                        '-useControlPlaneFrameSize', useControlPlaneFrameSize, 
                        '-mergeDestinations', mergeDestinations, 
                        '-interAsBgpPreference', interAsBgpPreference, 
                        '-enableDynamicMplsLabelValues', enableDynamicMplsLabelValues, 
                        '-trafficItemType', trafficItemType, 
                        '-transportRsvpTePreference', transportRsvpTePreference, 
                        '-egressEnabled', egressEnabled, 
                        '-maxNumberOfVpnLabelStack', maxNumberOfVpnLabelStack, 
                        '-enabled', enabled, 
                        '-roundRobinPacketOrdering', roundRobinPacketOrdering, 
                        '-routeMesh', routeMesh, 
                        '-numVlansForMulticastReplication', numVlansForMulticastReplication, 
                        '-transmitMode', transmitMode, 
                        '-srcDestMesh', srcDestMesh, 
                        '-trafficType', trafficType, 
                        '-hasOpenFlow', hasOpenFlow)
            self.__IXN.commit()
            self.__globalTrafficItem = self.__IXN.remapIds(self.__globalTrafficItem)[0]

            # Add traffic Quickflow Defaults
            self.__globalEgressTracking = self.__IXN.add(self.__globalTrafficItem, 'egressTracking')
            self.__globalEgressTracking = self.__IXN.remapIds(self.__globalEgressTracking)[0]
            self.__IXN.setMultiAttribute(self.__globalEgressTracking, 
                                         '-offset', 'Outer VLAN Priority (3 bits)', 
                                         '-customOffsetBits', '0', 
                                         '-encapsulation', 'Ethernet', 
                                         '-customWidthBits', '0')
            self.__IXN.commit()
            
            """
                                              sourceMacAddressFixed      = "00:00:00:00:00:00",
                                  destinationMacAddressFixed = "00:00:00:00:00:00",
            """ 
            
            
            self.__IXN.setMultiAttribute(self.__globalEgressTracking +'/fieldOffset/stack:"ethernet-1"/field:"ethernet.header.destinationAddress-1"', 
                        '-singleValue', '00:00:00:00:00:00', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['00:00:00:00:00:00'], 
                        '-stepValue', '00:00:00:00:00:00', 
                        '-fixedBits', '00:00:00:00:00:00', 
                        '-fieldValue', '00:00:00:00:00:00', 
                        '-auto', 'true', 
                        '-randomMask', '00:00:00:00:00:00', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '00:00:00:00:00:00', 
                        '-countValue', '1')
            self.__IXN.setMultiAttribute(self.__globalEgressTracking +'/fieldOffset/stack:"ethernet-1"/field:"ethernet.header.sourceAddress-2"', 
                        '-singleValue', '00:00:00:00:00:00', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['00:00:00:00:00:00'], 
                        '-stepValue', '00:00:00:00:00:00', 
                        '-fixedBits', '00:00:00:00:00:00', 
                        '-fieldValue', '00:00:00:00:00:00', 
                        '-auto', 'false', 
                        '-randomMask', '00:00:00:00:00:00', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '00:00:00:00:00:00', 
                        '-countValue', '1')
            self.__IXN.setMultiAttribute(self.__globalEgressTracking +'/fieldOffset/stack:"ethernet-1"/field:"ethernet.header.etherType-3"', 
                        '-singleValue', 'ffff', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0xFFFF'], 
                        '-stepValue', '0xFFFF', 
                        '-fixedBits', '0xFFFF', 
                        '-fieldValue', 'ffff', 
                        '-auto', 'true', 
                        '-randomMask', '0xFFFF', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0xFFFF', 
                        '-countValue', '1')
            self.__IXN.setMultiAttribute(self.__globalEgressTracking +'/fieldOffset/stack:"ethernet-1"/field:"ethernet.header.pfcQueue-4"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', '0', 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')
            self.__IXN.setMultiAttribute(self.__globalEgressTracking +'/fieldOffset/stack:"fcs-2"/field:"ethernet.fcs-1"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', '0', 
                        '-auto', 'true', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')
        except Exception as excMsg:
            localMessage = "[{}] EXCEPTION: Traffic not initialized".format(methodLocalName)
            self.__lc_msg(localMessage)
            self.__globalTrafficItem = None
            self.__globalEgressTracking  = None            
            return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))
        self.__IXN.commit()
        localMessage = "[{}] Traffic initialized now: ready for highLevelStream instances creation".format(methodLocalName)
        self.__lc_msg(localMessage)
        return  True, localMessage
 

    def add_L2_3_Quick_Flow_Group(self, vPortId, 
                                  flowGroupName = None,
                                  fixedSize          = 64,              
                                  incrementFrom      = 64,
                                  randomMin          = 64,
                                  randomMax          = 1518,
                                  frameSizeType      = "fixed",
                                  presetDistribution = "cisco",
                                  incrementStep      = 1,
                                  incrementTo        = 1518,
                                  rateType           = "lineRate",
                                  rateValue          = 10.0000,     
                                  rateUnitsType      = "mbytesPerSec",
                                  payloadType        = "incrementByte", 
                                  payloadPattern     = "BAC0", 
                                  payloadPatternRepeat = True , 
                                  transmissionMode       = "continuous",
                                  transmissionStopAfter  = 1, 
                                  transmissionStartDelay = 0 ,
                                  transmissionStartDelayUnit = "bytes" ,
                                  transmissionMinimumGap = 12,
                                  sourceMacAddressMode       = "singleValue", # "increment" | "decrement" | "random"
                                  sourceMacAddressFixed      = "00:00:00:00:00:00",
                                  sourceMacAddressStart      = "00:00:00:00:00:00",
                                  sourceMacAddressStep       = "00:00:00:00:00:00",
                                  sourceMacAddressCount      = 1,
                                  destinationMacAddressMode       = "singleValue",  # "increment" | "decrement" | "random"
                                  destinationMacAddressFixed      = "00:00:00:00:00:00",
                                  destinationMacAddressStart      = "00:00:00:00:00:00",
                                  destinationMacAddressStep       = "00:00:00:00:00:00",
                                  destinationMacAddressCount      = 1,
                                  etherType             = None, # specify an Hex value (without the 0x prefix!!!) to force it's insertion in the eth frame (e.g. "8100", "0806"...)
                                  vLanId                = None, # insert a value to add a VLAN protocol
                                  vLanPrio              = 0,
                                  innerVLanId           = None, # insert a value to add an inner VLAN tag inside the "primary" vLan
                                  innerVLanPrio         = 0,
                                  mplsTunnelLabel       = None, # insert a value to add a MPLS protocol
                                  mplsTunnelTTL         = 64,   # insert a value to add a MPLS protocol
                                  mplsTunnelExpBit      = 0,    # insert a value to add a MPLS protocol
                                  mplsPWLabel           = None, # insert a value to add a MPLS protocol
                                  mplsPWTTL             = 64,   # insert a value to add a MPLS protocol
                                  mplsPWExpBit          = 0     # insert a value to add a MPLS protocol
                                  ):                
        """ 
    
            Method:
                add_L2_3_Quick_Flow_Group: lineRateValue                    =  "10,0000" ,  

            Purpose:


            Usage:

            Parameters:
                vPortId....................... vport id specified as TUPLE ('<IP Address Chassis>',<card number> ,<port number>), 
                                               e.g. ('151.98.130.42', 2, 1)   
                === STREAM parameters - Panel Flow Group Editor ===================================================                              
                flowGroupName ................ Default: None (for auto generated flow name)
                                               Specify a custom flowGroupName as a string between "" (quotes):
                                               E.g. #1  flowGroupName="this is my custom flow name" 
                == FRAME SIZE parameters: Panel Flow Group Editor =================================================                             
                fixedSize .................... Default: 64              
                incrementFrom ................ Default: 64          
                randomMin .................... Default: 64
                                               Min Frame Size in Random Type frame size. 
                randomMax .................... Default: 1518            
                                               Max Frame Size in Random Type frame size. 
                frameSizeType ................ Default: "fixed"  
                                               Specify one of the Frame Size between: "fixed", "random", "increment", "auto"
                presetDistribution ........... Default: "cisco"
                incrementStep ................ Default: 1           
                incrementTo .................. Default: 1518 
                                               Unused when frameSizeType = "random" (forced to randomMax value, as workaround)    
                === RATE parameters - Panel Flow Group Editor ======================================================                              
                rateType ..................... Default: "lineRate"
                                               Specify one of the following:
                                               "lineRate"  .......... rateType = "lineRate" specify rateValue value too (default 10.0000)
                                               "packetRate"  ........ rateType = "packetRate" specify rateValue value too   
                                               "layer2BitRate" ...... rateType = "layer2BitRate"specify rateValue value too
                rateValue .................... Defaults: this parameter's defaulds changes to ease the validator work.
                                               If this parameter misses, it will be automatically set with the proper default
                                               value depending on rateType value: 
                                                  rateType= "lineRate"      ->  Default rateValue = 10.0000, 
                                                  rateType= "packetRate"    ->  Default rateValue = 100000.00 
                                                  rateType= "layer2BitRate" ->  Default rateValue = 1000.00 (decimal value, set depending on the rateValue) 
                                               
                                               
                rateUnitsType ................ Default: "mbytesPerSec" specified for the default rateType = "lineRate" setup.
                                               For the rateType = "layer2BitRate", the following strings may be specified, to 
                                               select this parameter as shown in the IxNetwork gui mask:
                                               - "bitsPerSec"  ..... rateUnitsType= "bitsPerSec"    
                                               - "kbitsPerSec" ..... rateUnitsType= "kbitsPerSec" 
                                               - "mbitsPerSec" ..... rateUnitsType= "mbitsPerSec" 
                                               - "bytesPerSec" ..... rateUnitsType= "bytesPerSec" 
                                               - "kbytesPerSec" .... rateUnitsType= "kbytesPerSec"
                                               - "mbytesPerSec" .... rateUnitsType= "mbytesPerSec" (default)
                
                === PAYLOAD parameters - Panel Flow Group Editor ======================================================                              
                payloadType .................. Default: "incrementByte" 
                                               Currently supported payload types:
                                                 payloadType = "incrementByte" 
                                                 payloadType = "random" 
                                                 payloadType = "custom" 
                payloadPattern ............... Default: "BAC0"
                                               Specify the Payload pattens as a string, e.g: payloadPattern="ABBAABBA"
                payloadPatternRepeat ......... Default: True
                                               Allowed values:
                                                 payloadPatternRepeat = True 
                                                 payloadPatternRepeat = False 

                === TRANSMISSION MODE parameters - Panel Flow Group Editor ============================================                              
                transmissionMode ............. Supported values: 
                                               - "continuous" (default)
                                               - "fixedPacketCount
                transmissionStopAfter ........ Default: 1 
                transmissionStartDelay ....... Default: 0 
                transmissionStartDelayUnit.... Default: "bytes", use "nanoseconds" if you need 
                transmissionMinimumGap ....... Default: 12 
  
                === TRANSMISSION MODE parameters - Packet Editor ============================================                              
                etherType .................... Default = None : the etherType/Size field will be modified in automatic way 
                                               Specify a custom Hex value to change it's value.
                                               BE Care: don't specify the 0x prefix, so use 
                                               
                                               E.g. #1: etherType="0806"  (use "0806" instead of "0x0806")
                                               E.g. #2: etherType="8870"  (use "8870" instead of "0x8870")
                                               
                                               EtherType values for some notable protocols (reported here just for quick reference purposes): 
                                               EtherType Protocol
                                               0x0800    Internet Protocol version 4 (IPv4)
                                               0x0806    Address Resolution Protocol (ARP)
                                               0x0842    Wake-on-LAN[7]
                                               0x22F3    IETF TRILL Protocol
                                               0x6003    DECnet Phase IV
                                               0x8035    Reverse Address Resolution Protocol
                                               0x809B    AppleTalk (Ethertalk)
                                               0x80F3    AppleTalk Address Resolution Protocol (AARP)
                                               0x8100    VLAN-tagged frame (IEEE 802.1Q) and Shortest Path Bridging IEEE 802.1aq[8]
                                               0x8137    IPX
                                               0x8204    QNX Qnet
                                               0x86DD    Internet Protocol Version 6 (IPv6)
                                               0x8808    Ethernet flow control
                                               0x8819    CobraNet
                                               0x8847    MPLS unicast
                                               0x8848    MPLS multicast
                                               0x8863    PPPoE Discovery Stage
                                               0x8864    PPPoE Session Stage
                                               0x8870    Jumbo Frames (proposed)[2][3]
                                               0x887B    HomePlug 1.0 MME
                                               0x888E    EAP over LAN (IEEE 802.1X)
                                               0x8892    PROFINET Protocol
                                               0x889A    HyperSCSI (SCSI over Ethernet)
                                               0x88A2    ATA over Ethernet
                                               0x88A4    EtherCAT Protocol
                                               0x88A8    Provider Bridging (IEEE 802.1ad) & Shortest Path Bridging IEEE 802.1aq[9]
                                               0x88AB    Ethernet Powerlink[citation needed]
                                               0x88CC    Link Layer Discovery Protocol (LLDP)
                                               0x88CD    SERCOS III
                                               0x88E1    HomePlug AV MME[citation needed]
                                               0x88E3    Media Redundancy Protocol (IEC62439-2)
                                               0x88E5    MAC security (IEEE 802.1AE)
                                               0x88E7    Provider Backbone Bridges (PBB) (IEEE 802.1ah)
                                               0x88F7    Precision Time Protocol (PTP) over Ethernet (IEEE 1588)
                                               0x88FB    Parallel Redundancy Protocol (PRP)
                                               0x8902    IEEE 802.1ag Connectivity Fault Management (CFM) Protocol/ITU-T Recommendation Y.1731 (OAM)
                                               0x8906    Fibre Channel over Ethernet (FCoE)
                                               0x8914    FCoE Initialization Protocol
                                               0x8915    RDMA over Converged Ethernet (RoCE)
                                               0x891D    TTEthernet Protocol Control Frame (TTE)
                                               0x892F    High-availability Seamless Redundancy (HSR)
                                               0x9000    Ethernet Configuration Testing Protocol[10]

                === VLAN and INNER VLAN configuration =======================================================                              
                vLanId ....................... Default = None: no VLAN protocol added by default
                                               Insert a proper vLanId integer value toto add a VLAN protocol
                vLanPrio ..................... Default = 0: specify a different vLan priority if needed (used only if vLanId is set)
                
                innerVLanId .................. Default = None: no inner VLAN protocol added by default
                                               Insert a proper innerVLanId integer value to add an inner VLAN tag inside the vLan 
                innerVLanPrio ................ Default = 0: specify a different vLan priority if needed (used only if vLanId is set)
                
                === PSEUDOWIRE or TUNNEL + PSEUDOWIRE configuration =========================================                              
                mplsPWLabel .................. Default = None: no MPLS added by default. 
                                               To add a MPLS protocol, specify a numeric value for mplsPWLabel 

                                                    PseudoWire
                                                        | 
                                                        V
                                               +-----+--------+----------------------------------------------+
                                               | ETH |  MPLS  |                                              |
                                               |  II | (pWire)|                                              |
                                               +-----+--------+----------------------------------------------+
                                               
                                               BE CARE : to add MPLS, the vLanId field must be leaved = None (it's default...)
                                               If the vLanId parameter differs from None, the mplsPWLabel will be ignored and 
                                               a VLAN will be created, instead.
                mplsPWTTL .................... Default = 64, modify if needed
                mplsPWExpBit.... ............. Default = 0, modify if needed


                mplsTunnelLabel .............. Default = None: no Tunnel creation 
                                               In a Tunnel + Pseudowire configuration, this parameter must contain the 
                                               mpls tunnel label. 

                                                      Tunnel   PseudoWire
                                                         |         | 
                                                         V         V
                                               +-----+--------+--------+--------------------------------------+
                                               | ETH |  MPLS  |  MPLS  |                                      |
                                               |  II |(tunnel)|(pWire) |                                      |
                                               +-----+--------+--------+--------------------------------------+

                mplsTunnelTTL ................ Default = 64, modify if needed
                mplsTunnelExpBit ............. Default = 0, modify if needed

                sourceMacAddressMode.......... Default  = "singleValue": to specify a single source mac address specified in the parameter sourceMacAddressFixed
                                                                         No need to change this parameter if you want to set a fixed source 
                                                                         mac address, simply specify the src mac in the sourceMacAddressFixed parameter
                                               Increment/Decrement mode: specify sourceMacAddressMode = "increment" or  sourceMacAddressMode = "decrement".
                                               when sourceMacAddressMode is set "increment" or "decrement", the parameters sourceMacAddressStart,
                                               sourceMacAddressStep and sourceMacAddressCount will be used
                                               
                                               To select the mac address increment (or decrement) specify 
                                               E.g. #1: sourceMacAddressMode = "increment"
                                               E.g. #2: sourceMacAddressMode = "decrement"
                
                sourceMacAddressFixed......... Default: "00:00:00:00:00:00",  used *** only **** when sourceMacAddressMode is "singleValue"
                                               Specify it as string if the you need to change the source mac address to a specific value.
                                               E.g.: sourceMacAddressFixed="00:AA:BB:00:00:00"

                sourceMacAddressStart......... Default = "00:00:00:00:00:00", used *** only **** when sourceMacAddressMode is "increment" or "decrement"
                sourceMacAddressStep.......... Default = "00:00:00:00:00:00", used *** only **** when sourceMacAddressMode is "increment" or "decrement"
                sourceMacAddressCount......... Default = 1,                   used *** only **** when sourceMacAddressMode is "increment" or "decrement"

                destinationMacAddressMode..... Default  = "singleValue": to specify a single destination mac address specified in the parameter destinationMacAddressFixed
                                                                         No need to change this parameter if you want to set a fixed destination  
                                                                         mac address, simply specify the dest mac in the destinationMacAddressFixed parameter
                                               Increment/Decrement mode: specify destinationMacAddressMode = "increment" or  destinationMacAddressMode = "decrement".
                                               When destinationMacAddressMode is set "increment" or "decrement", the parameters destinationMacAddressStart,
                                               destinationMacAddressStep and destinationMacAddressCount will be used
                                               To select the mac address increment (or decrement) specify 
                                               E.g. #1: destinationMacAddressMode = "increment"
                                               E.g. #2: destinationMacAddressMode = "decrement"

                destinationMacAddressFixed.... Default: "00:00:00:00:00:00",  used *** only **** when destinationMacAddressMode is "singleValue"
                                               Specify it as string if the you need to change the destination mac address to a specific value.
                                               E.g.: destinationMacAddressFixed="00:AA:BB:00:00:00"
                                               
                destinationMacAddressStart.... Default = "00:00:00:00:00:00", used *** only **** when destinationMacAddressMode is "increment" or "decrement"
                destinationMacAddressStep..... Default = "00:00:00:00:00:00", used *** only **** when destinationMacAddressMode is "increment" or "decrement"
                destinationMacAddressCount.... Default = 1                    used *** only **** when destinationMacAddressMode is "increment" or "decrement"

            Return tuple:
                    ("True|False" , "answer_string"  )
                    True.............init traffic success (or already initialized, anyway ready for the next step) 
                    False............init traffic failedl
                    answer_string....message for humans, to better understand
                                     what happened in the processing flow
        """
        
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] ".format(methodLocalName))        
        # some default value, constant in all cases here processed 
        enforceMinimumInterPacketGap = 0 
        interPacketGapUnitsType      = "nanoseconds"                                  

        # Initial checks
        if vPortId == None:
           return  False, "ERROR: [{}] vPortId [{}] not specified".format(methodLocalName,vPortId)
        if vPortId not in self.__alreadyAddedVPort: 
           return  False, "ERROR: [{}] vPortId [{}] not initialized (have you executed bind_new_vports() ?)".format(methodLocalName,vPortId)
        if vPortId not in self.__vPortList: 
           return  False, "ERROR: [{}] vPortId [{}] not in self.__vPortList (have you created this port?) ".format(methodLocalName,vPortId)

        # Check for traffic initialization: if not done before, default parameters will be applied...        
        if self.__globalTrafficItem == None: 
            localMessage = "[{}] Traffic not yet initialized: calling init_traffic() for you with DEFAULT parameters".format(methodLocalName)
            self.__lc_msg(localMessage)
            self.init_traffic()

        # Recover the first free streamIndex  index
        for streamIndex in range (1,400):
            print("streamIndex[{}]".format(streamIndex))
            if streamIndex in self.__vPortToStreamMap:
                pass
                localMessage = "[{}] Stream [{}] already used".format(methodLocalName, streamIndex)
                self.__lc_msg(localMessage)
            else:
                localMessage = "[{}] New Stream [{}] used".format(methodLocalName, streamIndex)
                self.__lc_msg(localMessage)
                #self.__vPortToStreamMap.append(streamIndex)
                print("streamIndex AFTER[{}]".format(streamIndex))
                break
                
        # HighLevelStream:<Instance> setup               
        # Automatic parameters building 
        if flowGroupName == None:
            flowGroupName = "FlowGroup{:0>3}".format(streamIndex) 
        elif flowGroupName in self.__flowName2streamIndexMap.keys():  
            localMessage = "[{}] L2-3 quickflow [{}] setup error: flowGroupName [{}] already used".format(methodLocalName, streamIndex,flowGroupName)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", localMessage)

        # Create endpoint set and bind it to che related vport/protocol branch    
        localEndpointSet = self.__IXN.add(self.__globalTrafficItem, 'endpointSet')
        localEndpointSet = self.__IXN.remapIds(localEndpointSet)[0]
        self.__IXN.setMultiAttribute(localEndpointSet, 
                        '-multicastDestinations', [], 
                        '-destinations', [], 
                        '-scalableSources', [], 
                        '-multicastReceivers', [], 
                        '-destinationFilter', '', 
                        '-sourceFilter', '', 
                        '-scalableDestinations', [], 
                        '-ngpfFilters', [], 
                        '-trafficGroups', [], 
                        '-sources', [self.__vPortList[vPortId]+'/protocols'], 
                        '-name', '')
        self.__IXN.commit()
           
        self.__vPortToStreamMap.append(streamIndex)
           
        if frameSizeType == "random":
            #localMessage = "[{}] selected frameSizeType  random: applied instrument workaround incrementTo = randomMax".format(methodLocalName, streamIndex)
            #self.__lc_msg(localMessage)
            incrementTo = randomMax
       
        try:
            streamIndex = str(streamIndex)     

            localMessage = "[{}] highLevelStream [{}] config".format(methodLocalName, streamIndex)
            self.__lc_msg(localMessage)

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex, 
                '-destinationMacMode', 'manual', 
                '-crc', 'goodCrc', 
                '-txPortId', self.__vPortList[vPortId],       
                '-preambleFrameSizeMode', 'auto', 
                '-rxPortIds', [], 
                '-suspend', 'false', 
                '-preambleCustomSize', '8', 
                '-name', flowGroupName)

            """
                self.__IXN.setMultiAttribute(self._objRefs[725]+'/highLevelStream:1/transmissionControl', 
                        '-frameCount', '331', 
                        '-minGapBytes', '366', 
                        '-interStreamGap', '0', 
                        '-interBurstGap', '0', 
                        '-type', 'fixedFrameCount', 
                        '-burstPacketCount', '1', 
                        '-startDelay', '332')

            """
            if transmissionMode != "fixedPacketCount" and transmissionMode != "continuous":
                localMessage = "[{}] L2-3 quickflow [{}] setup error: transmissionMode=[{}] not supported".format(methodLocalName, streamIndex,transmissionMode)
                self.__lc_msg(localMessage)
                return self.__ret_func(False,"error", localMessage)
                
            if transmissionMode == "fixedPacketCount":
                transmissionMode ="fixedFrameCount"
           
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/transmissionControl', 
                '-frameCount', transmissionStopAfter, 
                '-minGapBytes',  transmissionMinimumGap, 
                '-interStreamGap', '0', 
                '-interBurstGap', '0', 
                '-interBurstGapUnits', 'nanoseconds', 
                '-type', transmissionMode, 
                '-duration', '1', 
                '-repeatBurst', '1', 
                '-enableInterStreamGap', 'false', 
                '-startDelayUnits', transmissionStartDelayUnit, 
                '-iterationCount', '1', 
                '-burstPacketCount', '1', 
                '-enableInterBurstGap', 'false', 
                '-startDelay', transmissionStartDelay)

            # PAYLOAD setup
            # PayloadRepeat translation
            if payloadType != "incrementByte" and payloadType != "random" and payloadType != "custom":
                localMessage = "[{}] L2-3 quickflow [{}] setup error: payloadType=[{}] not supported".format(methodLocalName, streamIndex,payloadType)
                self.__lc_msg(localMessage)
                return self.__ret_func(False,"error", localMessage)
                    
            if payloadPatternRepeat == True:
                payloadPatternRepeat = 'true'
            else:    
                payloadPatternRepeat = 'false' 
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/framePayload', 
                        '-type', payloadType, 
                        '-customRepeat', payloadPatternRepeat, 
                        '-customPattern', payloadPattern)

            if  rateType == "lineRate":
                #print ("Caso A lineRate")
                localMessage = "[{}] Rate type lineRate".format(methodLocalName)
                self.__lc_msg(localMessage)
                rateValue = str(rateValue).replace(".", ",")  
                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/frameRate', 
                    '-type', "percentLineRate", 
                    '-rate', rateValue, 
                    '-bitRateUnitsType', rateUnitsType, 
                    '-enforceMinimumInterPacketGap', enforceMinimumInterPacketGap, 
                    '-interPacketGapUnitsType', interPacketGapUnitsType)
            elif rateType == "packetRate":
                #print ("Caso B packetRate")
                localMessage = "[{}] Rate type packetRate".format(methodLocalName)
                self.__lc_msg(localMessage)
                if rateValue == 10.0000:
                    rateValue = 100000.00       
                rateValue = str(rateValue).replace(".", ",")  
                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/frameRate', 
                    '-type', "framesPerSecond", 
                    '-rate', rateValue, 
                    '-bitRateUnitsType', rateUnitsType, 
                    '-enforceMinimumInterPacketGap', enforceMinimumInterPacketGap, 
                    '-interPacketGapUnitsType', interPacketGapUnitsType)
                
            elif rateType == "layer2BitRate":   
                #print ("Caso C layer2BitRate")
                localMessage = "[{}] Rate type layer2BitRate".format(methodLocalName)
                self.__lc_msg(localMessage)
                if rateValue == 10.0000:
                    rateValue = 1000.00       
                rateValue = str(rateValue).replace(".", ",")  
                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/frameRate', 
                    '-bitRateUnitsType', rateUnitsType, 
                    '-rate', rateValue, 
                    '-enforceMinimumInterPacketGap', enforceMinimumInterPacketGap, 
                    '-type', "bitsPerSecond" , 
                    '-interPacketGapUnitsType', interPacketGapUnitsType)
            else:     
                localMessage = "[{}] L2-3 quickflow [{}] setup error: invalid rateType=[{}] value".format(methodLocalName, streamIndex,rateType)
                self.__lc_msg(localMessage)
                return self.__ret_func(False,"error", localMessage)
 
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/frameSize', 
                '-weightedPairs', [], 
                '-fixedSize', fixedSize, 
                '-incrementFrom', incrementFrom, 
                '-randomMin', randomMin, 
                '-quadGaussian', [], 
                '-randomMax', randomMax, 
                '-weightedRangePairs', [], 
                '-type', frameSizeType, 
                '-presetDistribution', presetDistribution, 
                '-incrementStep', incrementStep, 
                '-incrementTo', incrementTo)

            localMessage = "[{}] Required custom destinationMacAddressMode [{}]  ".format(methodLocalName, destinationMacAddressMode)
            self.__lc_msg(localMessage)
            if destinationMacAddressMode == "random":  # translate into internal rapresentation
                destinationMacAddressMode = "nonRepeatableRandom"
 
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.destinationAddress-1"', 
                '-singleValue', destinationMacAddressFixed, 
                '-seed', '1', 
                '-optionalEnabled', 'true', 
                '-onTheFlyMask', '0', 
                '-fullMesh', 'false', 
                '-valueList', ['00:00:00:00:00:00'], 
                '-stepValue', destinationMacAddressStep, #'00:00:00:00:00:00', 
                '-fixedBits', '00:00:00:00:00:00', 
                '-fieldValue', destinationMacAddressFixed, 
                '-auto', 'false', 
                '-randomMask', '00:00:00:00:00:00', 
                '-trackingEnabled', 'false', 
                '-valueType', destinationMacAddressMode, # 'singleValue', 'increment' 'decrement' 'random'
                '-activeFieldChoice', 'false', 
                '-startValue',destinationMacAddressStart, # '00:00:00:00:00:00', 
                '-countValue',destinationMacAddressCount ) # '1'

            localMessage = "[{}] Required custom sourceMacAddressMode [{}]  ".format(methodLocalName, sourceMacAddressMode)
            self.__lc_msg(localMessage)
            if sourceMacAddressMode == "random":  # translate into internal rapresentation
                sourceMacAddressMode = "nonRepeatableRandom"

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.sourceAddress-2"', 
                '-singleValue', sourceMacAddressFixed, 
                '-seed', '1', 
                '-optionalEnabled', 'true', 
                '-onTheFlyMask', '0', 
                '-fullMesh', 'false', 
                '-valueList', ['00:00:00:00:00:00'], 
                '-stepValue', sourceMacAddressStep, # '00:00:00:00:00:00', 
                '-fixedBits', '00:00:00:00:00:00', 
                '-fieldValue', sourceMacAddressFixed,  
                '-auto', 'false', 
                '-randomMask', '00:00:00:00:00:00', 
                '-trackingEnabled', 'false', 
                '-valueType',  sourceMacAddressMode,   # 'singleValue', 'increment' 'decrement' 'random'
                '-activeFieldChoice', 'false', 
                '-startValue', sourceMacAddressStart,  #'00:00:00:00:00:00', 
                '-countValue', sourceMacAddressCount)  # '1'
            localAutoEtherType='true' 
            if etherType != None: # specify a custom ethetType/size field
                protocolSpecificTag = etherType
                localAutoEtherType='false' 
                localMessage = "[{}] custom etherType [{}] added".format(methodLocalName,etherType)
                self.__lc_msg(localMessage)
            elif vLanId != None: # add  VLAN protocol 
                protocolSpecificTag = "8100"
                localMessage = "[{}] VLAN protocol added".format(methodLocalName)
                self.__lc_msg(localMessage)
            elif  mplsPWLabel != None: # add  MPLS protocol 
                protocolSpecificTag = "8847"
                localMessage = "[{}] MPLS protocol added".format(methodLocalName)
                self.__lc_msg(localMessage)
            else:      
                # don't add protocols: the internal default value is "FFFF" 
                protocolSpecificTag = "ffff"
                localMessage = "[{}] No protocol added".format(methodLocalName)
                self.__lc_msg(localMessage)

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.etherType-3"', 
                '-singleValue', protocolSpecificTag,  # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                '-seed', '1', 
                '-optionalEnabled', 'true', 
                '-onTheFlyMask', '0', 
                '-fullMesh', 'false', 
                '-valueList', ['0xFFFF'], 
                '-stepValue', '0xFFFF', 
                '-fixedBits', '0xFFFF', 
                '-fieldValue', protocolSpecificTag, # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                '-auto', localAutoEtherType, #'true', 
                '-randomMask', '0xFFFF', 
                '-trackingEnabled', 'false', 
                '-valueType', 'singleValue', 
                '-activeFieldChoice', 'false', 
                '-startValue', '0xFFFF', 
                '-countValue', '1')
            # init dictionary for future on the fly etherType change    
            self.__flowName2streamIndexMap[flowGroupName] = streamIndex
            #print("Current streamIndex-flowGroupName assotiations [{}]".format(self.__flowName2streamIndexMap))
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.pfcQueue-4"', 
                '-singleValue', '0', 
                '-seed', '1', 
                '-optionalEnabled', 'true', 
                '-onTheFlyMask', '0', 
                '-fullMesh', 'false', 
                '-valueList', ['0'], 
                '-stepValue', '0', 
                '-fixedBits', '0', 
                '-fieldValue', '0', 
                '-auto', 'false', 
                '-randomMask', '0', 
                '-trackingEnabled', 'false', 
                '-valueType', 'singleValue', 
                '-activeFieldChoice', 'false', 
                '-startValue', '0', 
                '-countValue', '1')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-2"/field:"ethernet.fcs-1"', 
                '-singleValue', '0', 
                '-seed', '1', 
                '-optionalEnabled', 'true', 
                '-onTheFlyMask', '0', 
                '-fullMesh', 'false', 
                '-valueList', ['0'], 
                '-stepValue', '0', 
                '-fixedBits', '0', 
                '-fieldValue', '0', 
                '-auto', 'true', 
                '-randomMask', '0', 
                '-trackingEnabled', 'false', 
                '-valueType', 'singleValue', 
                '-activeFieldChoice', 'false', 
                '-startValue', '0', 
                '-countValue', '1')


            if vLanId != None: # add  VLAN protocol 
                localMessage = "[{}] VLAN protocol initialization vLanId[{}] vLanPrio [{}] ".format(methodLocalName,vLanId,vLanPrio)
                self.__lc_msg(localMessage)

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.vlanUserPriority-1"', 
                        '-singleValue',vLanPrio, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', vLanPrio, 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.cfi-2"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', '0', 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.vlanID-3"', 
                        '-singleValue', vLanId, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', vLanId, 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                if innerVLanId == None: # no Inner VLAN Tag added 
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.protocolID-4"', 
                                                 '-singleValue', 'ffff', 
                                                 '-seed', '1', 
                                                 '-optionalEnabled', 'true', 
                                                 '-onTheFlyMask', '0', 
                                                 '-fullMesh', 'false', 
                                                 '-valueList', ['0xffff'], 
                                                 '-stepValue', '0xffff', 
                                                 '-fixedBits', '0xffff', 
                                                 '-fieldValue', 'ffff', 
                                                 '-auto', 'true', 
                                                 '-randomMask', '0xffff', 
                                                 '-trackingEnabled', 'false', 
                                                 '-valueType', 'singleValue', 
                                                 '-activeFieldChoice', 'false', 
                                                 '-startValue', '0xffff', 
                                                 '-countValue', '1')
                    
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-3"/field:"ethernet.fcs-1"', 
                                                 '-singleValue', '0', 
                                                 '-seed', '1', 
                                                 '-optionalEnabled', 'true', 
                                                 '-onTheFlyMask', '0', 
                                                 '-fullMesh', 'false', 
                                                 '-valueList', ['0'], 
                                                 '-stepValue', '0', 
                                                 '-fixedBits', '0', 
                                                 '-fieldValue', '0', 
                                                 '-auto', 'true', 
                                                 '-randomMask', '0', 
                                                 '-trackingEnabled', 'false', 
                                                 '-valueType', 'singleValue', 
                                                 '-activeFieldChoice', 'false', 
                                                 '-startValue', '0', 
                                                 '-countValue', '1')
                else:     # add  inner VLAN protocol 
                    localMessage = "[{}] inner VLAN protocol initialization innerVLanId[{}] innerVLanPrio[{}] ".format(methodLocalName,innerVLanId,innerVLanPrio)
                    self.__lc_msg(localMessage)
                    
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.protocolID-4"', 
                                                  '-singleValue', '8100', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0xffff'], 
                                                  '-stepValue', '0xffff', 
                                                  '-fixedBits', '0xffff', 
                                                  '-fieldValue', '8100', 
                                                  '-auto', 'true', 
                                                  '-randomMask', '0xffff', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0xffff', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.vlanUserPriority-1"', 
                                                  '-singleValue', innerVLanPrio, 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', innerVLanPrio, 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.cfi-2"', 
                                                  '-singleValue', '0', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', '0', 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.vlanID-3"', 
                                                  '-singleValue', innerVLanId, 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', innerVLanId, 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.protocolID-4"', 
                                                  '-singleValue', 'ffff', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0xffff'], 
                                                  '-stepValue', '0xffff', 
                                                  '-fixedBits', '0xffff', 
                                                  '-fieldValue', 'ffff', 
                                                  '-auto', 'true', 
                                                  '-randomMask', '0xffff', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0xffff', 
                                                  '-countValue', '1')
 
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-4"/field:"ethernet.fcs-1"', 
                                                  '-singleValue', '0', 
                                                '-seed', '1', 
                                                '-optionalEnabled', 'true', 
                                                '-onTheFlyMask', '0', 
                                                '-fullMesh', 'false', 
                                                '-valueList', ['0'], 
                                                '-stepValue', '0', 
                                                '-fixedBits', '0', 
                                                '-fieldValue', '0', 
                                                '-auto', 'true', 
                                                '-randomMask', '0', 
                                                '-trackingEnabled', 'false', 
                                                '-valueType', 'singleValue', 
                                                '-activeFieldChoice', 'false', 
                                                '-startValue', '0', 
                                                '-countValue', '1')
 

            elif  mplsPWLabel != None: # add  MPLS protocol 
                localMessage = "[{}] MPLS protocol pseudo wire only initialization mplsPWLabel [{}]".format(methodLocalName,mplsPWLabel)
                self.__lc_msg(localMessage)
                if mplsTunnelLabel != None:
                    localMessage = "[{}] MPLS protocol Tunnel+PseudoWire mplsTunnelLabel [{}] mplsPWLabel [{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel)
                    self.__lc_msg(localMessage)
                    #print("[{}] SWAP Before  TUNNEL[{}]      PW[{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel))
                    #print("[{}] SWAP Before  TTL   [{}]     TTL[{}]".format(methodLocalName,mplsTunnelTTL,mplsPWTTL))
                    #print("[{}] SWAP Before  EXPBIT[{}]  EXPBIT[{}]".format(methodLocalName,mplsTunnelExpBit,mplsPWExpBit))
                    # swap PW and TUNNEL parameters
                    mplsTunnelLabel,  mplsPWLabel   = mplsPWLabel,  mplsTunnelLabel
                    mplsTunnelTTL,    mplsPWTTL     = mplsPWTTL,    mplsTunnelTTL 
                    mplsTunnelExpBit, mplsPWExpBit  = mplsPWExpBit, mplsTunnelExpBit
                    
                    #print("[{}] SWAP AFTER  TUNNEL[{}]      PW[{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel))
                    #print("[{}] SWAP AFTER  TTL   [{}]     TTL[{}]".format(methodLocalName,mplsTunnelTTL,mplsPWTTL))
                    #print("[{}] SWAP AFTER  EXPBIT[{}]  EXPBIT[{}]".format(methodLocalName,mplsTunnelExpBit,mplsPWExpBit))
                    bottomOfStack="1"
                else:
                    bottomOfStack="1"

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.value-1"', 
                        '-singleValue', mplsPWLabel, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['16'], 
                        '-stepValue', '16', 
                        '-fixedBits', '16', 
                        '-fieldValue', mplsPWLabel, 
                        '-auto', 'false', 
                        '-randomMask', '16', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '16', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.experimental-2"', 
                        '-singleValue', mplsPWExpBit, # '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', mplsPWExpBit, # '0', 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.bottomOfStack-3"', 
                        '-singleValue', '1', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['1'], 
                        '-stepValue', '1', 
                        '-fixedBits', '1', 
                        '-fieldValue', '1', 
                        '-auto', 'true', 
                        '-randomMask', '1', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '1', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.ttl-4"', 
                        '-singleValue', mplsPWTTL, # '64', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['64'], 
                        '-stepValue', '64', 
                        '-fixedBits', '64', 
                        '-fieldValue', mplsPWTTL, # '64', 
                        '-auto', 'false', 
                        '-randomMask', '64', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '64', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.tracker-5"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0x0'], 
                        '-stepValue', '0x0', 
                        '-fixedBits', '0x0', 
                        '-fieldValue', '0', 
                        '-auto', 'false', 
                        '-randomMask', '0x0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0x0', 
                        '-countValue', '1')


                if mplsTunnelLabel != None:
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.value-1"', 
                                                     '-singleValue', mplsTunnelLabel, 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['16'], 
                                                     '-stepValue', '16', 
                                                     '-fixedBits', '16', 
                                                     '-fieldValue', mplsTunnelLabel, 
                                                     '-auto', 'false', 
                                                     '-randomMask', '16', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '16', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.experimental-2"', 
                                                     '-singleValue', mplsTunnelExpBit, # '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', mplsTunnelExpBit, # '0',  
                                                     '-auto', 'false', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.bottomOfStack-3"', 
                                                     '-singleValue', '1', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['1'], 
                                                     '-stepValue', '1', 
                                                     '-fixedBits', '1', 
                                                     '-fieldValue', '1', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '1', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '1', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.ttl-4"', 
                                                     '-singleValue', mplsTunnelTTL, #'64', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['64'], 
                                                     '-stepValue', '64', 
                                                     '-fixedBits', '64', 
                                                     '-fieldValue', mplsTunnelTTL, #'64',  
                                                     '-auto', 'false', 
                                                     '-randomMask', '64', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '64', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.tracker-5"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0x0'], 
                                                     '-stepValue', '0x0', 
                                                     '-fixedBits', '0x0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'false', 
                                                     '-randomMask', '0x0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0x0', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-4"/field:"ethernet.fcs-1"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')
                else:  # terminate single MPLS Label Structure  
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-3"/field:"ethernet.fcs-1"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')
                        
            else:           # don't add protocols 
                localMessage = "[{}] No further protocol added".format(methodLocalName)
                self.__lc_msg(localMessage)
 
            #"""
            # attualmente propongo a Tony uno skip di questa parte perhce sono bloccato
            # li aggiungiamo in un secondo momento 
            localMessage = "[{}] Vport UDF setup [{}] config".format(methodLocalName, streamIndex)
            self.__lc_msg(localMessage)

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:1', 
                '-enabled', 'false', 
                '-byteOffset', '0', 
                '-type', 'counter', 
                '-chainedFromUdf', 'none')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:1/counter', 
                '-bitOffset', '0', 
                '-count', '1', 
                '-startValue', '0', 
                '-stepValue', '0', 
                '-width', '32', 
                '-direction', 'increment')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:2', 
                '-enabled', 'false', 
                '-byteOffset', '0', 
                '-type', 'counter', 
                '-chainedFromUdf', 'none')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:2/counter', 
                '-bitOffset', '0', 
                '-count', '1', 
                '-startValue', '0', 
                '-stepValue', '0', 
                '-width', '32', 
                '-direction', 'increment')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:3', 
                '-enabled', 'false', 
                '-byteOffset', '0', 
                '-type', 'counter', 
                '-chainedFromUdf', 'none')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:3/counter', 
                '-bitOffset', '0', 
                '-count', '1', 
                '-startValue', '0', 
                '-stepValue', '0', 
                '-width', '32', 
                '-direction', 'increment')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:4', 
                '-enabled', 'false', 
                '-byteOffset', '0', 
                '-type', 'counter', 
                '-chainedFromUdf', 'none')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:4/counter', 
                '-bitOffset', '0', 
                '-count', '1', 
                '-startValue', '0', 
                '-stepValue', '0', 
                '-width', '32', 
                '-direction', 'increment')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:5', 
                '-enabled', 'false', 
                '-byteOffset', '0', 
                '-type', 'counter', 
                '-chainedFromUdf', 'none')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/udf:5/counter', 
                '-bitOffset', '0', 
                '-count', '1', 
                '-startValue', '0', 
                '-stepValue', '0', 
                '-width', '32', 
                '-direction', 'increment')

            self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/tableUdf','-enabled', 'false')
            
            self.__IXN.commit()
            localMessage = "[{}] L2-3 commit performed".format(methodLocalName)
            self.__lc_msg(localMessage)

        except Exception as excMsg:
            localMessage = "[{}] L2-3 quickflow [{}] setup error".format(methodLocalName, streamIndex)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))

        localMessage = "[{}] Traffic initialized now: ready for highLevelStream instances creation".format(methodLocalName)
        self.__lc_msg(localMessage)
        return  True, localMessage



    def modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group(self,  flowGroupName,
                                  sourceMacAddressMode       = None,  #"singleValue", "increment | decrement" to change all the following 4 values
                                  sourceMacAddressFixed      = "00:00:00:00:00:00",
                                  sourceMacAddressStart      = "00:00:00:00:00:00",
                                  sourceMacAddressStep       = "00:00:00:00:00:00",
                                  sourceMacAddressCount      = 1,
                                  destinationMacAddressMode  = None,  #"singleValue", "increment | decrement" to change all the following 4 values
                                  destinationMacAddressFixed = "00:00:00:00:00:00",
                                  destinationMacAddressStart = "00:00:00:00:00:00",
                                  destinationMacAddressStep  = "00:00:00:00:00:00",
                                  destinationMacAddressCount = 1,
                                  etherType                  = None,  # specify an Hex value (without the 0x prefix!!!) to force it's insertion in the eth frame (e.g. "8100", "0806"...)
                                  ):                
        """ 
    
            Method:
                modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group,  

            Purpose:
                modify on the fly the following Frame Ethernet II Header 
                paramenters in type and values (S.M. Request):
                - Ether Type
                - Source Mac address (single value fixed, Increment / Decrement) 
                - Destination Mac address (single value fixed, Increment / Decrement) 

            Usage:

            Parameters:
                vPortId....................... vport id specified as TUPLE ('<IP Address Chassis>',<card number> ,<port number>), 
                                               e.g. ('151.98.130.42', 2, 1)   
                === STREAM parameters - Panel Flow Group Editor ===================================================                              
                flowGroupName ................ Default: None (for auto generated flow name)
                                               Specify a custom flowGroupName as a string between "" (quotes):
                                               E.g. #1  flowGroupName="this is my custom flow name" 
                === TRANSMISSION MODE parameters - Packet Editor ==================================================                              
                etherType .................... Default = None : the etherType/Size field will not be modified  
                                               Specify a custom Hex value to change it's value.
                                               BE Care: don't specify the 0x prefix, so use 

                sourceMacAddressMode.......... Default  = None: no change will be applied to source MAC address 
                                               "singleValue"....................to specify a single source mac address specified in the 
                                                                                parameter sourceMacAddressFixed
                                               "increment" / "decrement"....... specify sourceMacAddressMode = "increment" or  
                                                                                sourceMacAddressMode = "decrement".
                                               Note:                                                                                                                     
                                               when sourceMacAddressMode is set "increment" or "decrement", the parameters sourceMacAddressStart,
                                               sourceMacAddressStep and sourceMacAddressCount will be used
                                               
                                               To select the mac address increment (or decrement) specify 
                                               E.g. #1: sourceMacAddressMode = "increment"
                                               E.g. #2: sourceMacAddressMode = "decrement"
                
                sourceMacAddressFixed......... Default: "00:00:00:00:00:00",  used *** only **** when sourceMacAddressMode is "singleValue"
                                               Specify it as string if the you need to change the source mac address to a specific value.
                                               E.g.: sourceMacAddressFixed="00:AA:BB:00:00:00"

                sourceMacAddressStart......... Default = "00:00:00:00:00:00", used *** only **** when sourceMacAddressMode is "increment" or "decrement"
                sourceMacAddressStep.......... Default = "00:00:00:00:00:00", used *** only **** when sourceMacAddressMode is "increment" or "decrement"
                sourceMacAddressCount......... Default = 1,                   used *** only **** when sourceMacAddressMode is "increment" or "decrement"

                destinationMacAddressMode..... Default  = None:specify a single destination mac address specified in the parameter destinationMacAddressFixed
                                               mac address, simply specify the dest mac in the destinationMacAddressFixed parameter
                                               Increment/Decrement mode: specify destinationMacAddressMode = "increment" or  destinationMacAddressMode = "decrement".
                                               When destinationMacAddressMode is set "increment" or "decrement", the parameters destinationMacAddressStart,
                                               destinationMacAddressStep and destinationMacAddressCount will be used
                                               To select the mac address increment (or decrement) specify 
                                               E.g. #1: destinationMacAddressMode = "increment"
                                               E.g. #2: destinationMacAddressMode = "decrement"


                destinationMacAddressMode......Default  = None: no change will be applied to source MAC address 
                                               "singleValue"....................to specify a single source mac address specified in the 
                                                                                parameter destinationMacAddressFixed
                                               "increment" / "decrement"....... specify destinationMacAddressMode = "increment" or  
                                                                                sourceMacAddressMode = "decrement".
                                               Note:                                                                                                                     
                                               when destinationMacAddressMode is set "increment" or "decrement", destinationMacAddressStart,
                                               destinationMacAddressStep and destinationMacAddressCount will be used
                                               
                                               To select the mac address increment (or decrement) specify 
                                               E.g. #1: destinationMacAddressMode = "increment"
                                               E.g. #2: destinationMacAddressMode = "decrement"


                                               

                destinationMacAddressFixed.... Default: "00:00:00:00:00:00",  used *** only **** when destinationMacAddressMode is "singleValue"
                                               Specify it as string if the you need to change the destination mac address to a specific value.
                                               E.g.: destinationMacAddressFixed="00:AA:BB:00:00:00"
                                               
                destinationMacAddressStart.... Default = "00:00:00:00:00:00", used *** only **** when destinationMacAddressMode is "increment" or "decrement"
                destinationMacAddressStep..... Default = "00:00:00:00:00:00", used *** only **** when destinationMacAddressMode is "increment" or "decrement"
                destinationMacAddressCount.... Default = 1                    used *** only **** when destinationMacAddressMode is "increment" or "decrement"
                                               
                                               
            Return tuple:
                    ("True|False" , "answer_string"  )
                    True.............init traffic success (or already initialized, anyway ready for the next step) 
                    False............init traffic failed
                    answer_string....message for humans, to better understand
                                     what happened in the processing flow
        """
        
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] ".format(methodLocalName))        
        
        # Parameter validation
        if flowGroupName == None:
            localMessage = "[{}] flowGroupName [{}] not valid".format(methodLocalName, flowGroupName)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", localMessage)
        if flowGroupName not in self.__flowName2streamIndexMap.keys():
            localMessage = "[{}] flowGroupName [{}] not present in the streamIndex map: call add_L2_3_Quick_Flow_Group before.".format(methodLocalName, flowGroupName)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", localMessage)
        streamIndex = self.__flowName2streamIndexMap[flowGroupName]  
        localMessage = "[{}] Stream index [{}] found for flowGroupName [{}]".format(methodLocalName, streamIndex, flowGroupName )
        self.__lc_msg(localMessage)
        
        try:
            #================================================================================================
            # ether type management =========================================================================
            #================================================================================================
            if etherType != None: 
                localAutoEtherType='false' 
                localMessage = "[{}] custom etherType [{}] added".format(methodLocalName,etherType)
                self.__lc_msg(localMessage)

                #self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.etherType-3"', 
                    #'-singleValue', etherType,  # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                    #'-onTheFlyMask', 'ffff',   # ffff needed for on the fly etherType change
                    #'-fieldValue', etherType, # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                    #'-auto', 'false')
                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.etherType-3"', 
                    '-singleValue', etherType,  # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                    '-fieldValue', etherType, # Default: 'ffff',  sostituire '8100' per VLAN, '8847' per MPLS
                    '-auto', 'false')
            #================================================================================================    
            # destination MAC management ====================================================================
            #================================================================================================
            if destinationMacAddressMode != None:
                localMessage = "[{}] Required custom destinationMacAddressMode [{}]  ".format(methodLocalName, destinationMacAddressMode)
                self.__lc_msg(localMessage)

                if destinationMacAddressMode == "increment" or destinationMacAddressMode == "decrement":  
                    localMessage = "[{}] INCR/DECR destination MAC management [{}]  ".format(methodLocalName, destinationMacAddressMode)
                    self.__lc_msg(localMessage)
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.destinationAddress-1"', 
                                                 '-stepValue', destinationMacAddressStep, #'00:00:00:00:00:00', 
                                                 '-auto', 'false', 
                                                 '-valueType', destinationMacAddressMode, # 'singleValue', 'increment' 'decrement'
                                                 '-startValue',destinationMacAddressStart, # '00:00:00:00:00:00', 
                                                 '-countValue',destinationMacAddressCount ) # '1'
                else: 
                    localMessage = "[{}] FIXED/Random destination MAC management [{}]  ".format(methodLocalName, destinationMacAddressMode)
                    self.__lc_msg(localMessage)
                    if destinationMacAddressMode == "random":  # translate into internal rapresentation
                        destinationMacAddressMode = "nonRepeatableRandom"
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.destinationAddress-1"', 
                                                 '-singleValue', destinationMacAddressFixed, 
                                                 '-fieldValue', destinationMacAddressFixed, 
                                                 '-auto', 'false', 
                                                 '-valueType', destinationMacAddressMode) # '1'
 

            #================================================================================================    
            # source MAC management =========================================================================
            #================================================================================================    
            if sourceMacAddressMode != None:
                localMessage = "[{}] Required custom sourceMacAddressMode [{}]  ".format(methodLocalName, sourceMacAddressMode)
                self.__lc_msg(localMessage)

                if sourceMacAddressMode == "increment" or sourceMacAddressMode == "decrement":  
                    localMessage = "[{}] INCR/DECR source MAC management [{}]  ".format(methodLocalName, sourceMacAddressMode)
                    self.__lc_msg(localMessage)
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.sourceAddress-2"', 
                                                 '-singleValue', sourceMacAddressFixed, 
                                                 '-stepValue', sourceMacAddressStep, # '00:00:00:00:00:00', 
                                                 '-auto', 'false', 
                                                 '-valueType',  sourceMacAddressMode,   #   'increment' 'decrement'
                                                 '-startValue', sourceMacAddressStart,  #'00:00:00:00:00:00', 
                                                 '-countValue', sourceMacAddressCount)  # '1'
                else:  # fixed
                    localMessage = "[{}] FIXED/Random source MAC management [{}]  ".format(methodLocalName, sourceMacAddressMode)
                    if sourceMacAddressMode == "random":  # translate into internal rapresentation
                        sourceMacAddressMode = "nonRepeatableRandom"
                    self.__lc_msg(localMessage)
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"ethernet-1"/field:"ethernet.header.sourceAddress-2"', 
                                                 '-singleValue', sourceMacAddressFixed, 
                                                 '-fieldValue', sourceMacAddressFixed,  
                                                 '-auto', 'false', 
                                                 '-valueType',  sourceMacAddressMode )  # sourceMacAddressMode  
                    
                    
            self.__IXN.commit()
            localMessage = "[{}] L2-3 commit performed".format(methodLocalName)
            self.__lc_msg(localMessage)
        except Exception as excMsg:
            localMessage = "[{}] L2-3 Eth Header [{}] setup error".format(methodLocalName, streamIndex)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))

        localMessage = "[{}] L2-3 Eth Header Modifications Done".format(methodLocalName)
        self.__lc_msg(localMessage)
        return  True, localMessage
 


    def modify_MPLS_VLAN_L2_3_Quick_Flow_Group(self,  flowGroupName,
                                               vLanId                = None, # insert a value to add a VLAN protocol
                                               vLanPrio              = 0,
                                               innerVLanId           = None, # insert a value to add an inner VLAN tag inside the "primary" vLan
                                               innerVLanPrio         = 0,
                                               mplsTunnelLabel       = None, # insert a value to add a MPLS protocol
                                               mplsTunnelTTL         = 64,   # insert a value to add a MPLS protocol
                                               mplsTunnelExpBit      = 0,    # insert a value to add a MPLS protocol
                                               mplsPWLabel           = None, # insert a value to add a MPLS protocol
                                               mplsPWTTL             = 64,   # insert a value to add a MPLS protocol
                                               mplsPWExpBit          = 0     # insert a value to add a MPLS protocol
                                               ):                
        """ 
            Method:
                modify_MPLS_VLAN_L2_3_Quick_Flow_Group,  

            Purpose:
                modify on the fly the FlowGroup stack:

                There are two groups of parameters that must be changed in exclusive way:
                if VLAN parameters are specified, the MPLS changes will be skipped.
                If you plan to switch from MPLS to VLAN and vice versa, please modify 
                the etherType calling alseo the modify_Frame_Ethernet_Header_L2_3_Quick_Flow_Group() 
            Usage:
                modify_MPLS_VLAN_L2_3_Quick_Flow_Group(flowGroupName="", < VLAN parameters | MPLS parameters > )
            Parameters:
                flowGroupName................. flow group name is used as group identifier
                === VLAN and INNER VLAN configuration =======================================================                              
                vLanId ....................... Default = None: no VLAN tag modification by default
                                               Insert a proper vLanId integer value to modify the VLAN tag
                vLanPrio ..................... Default = 0: specify a different vLan priority if needed (used only if vLanId is set)
                innerVLanId .................. Default = None: no inner VLAN tag added by default
                                               Insert a proper innerVLanId integer value to add an inner VLAN tag inside the vLan (used only if vLanId is set)
                innerVLanPrio ................ Default = 0: specify a different vLan priority if needed (used only if vLanId is set)
                
                === PSEUDOWIRE or TUNNEL + PSEUDOWIRE configuration =========================================                              
                mplsPWLabel .................. Default = None: no MPLS modification by default. 
                                               To add a MPLS protocol, specify a numeric value for mplsPWLabel (BE CARE: vLanId MUST be left "None")
                                               BE CARE : to add MPLS, the vLanId field must be leaved = None (it's default...)
                                               If the vLanId parameter differs from None, the mplsPWLabel will be ignored and 
                                               a VLAN will be created, instead.
                mplsPWTTL .................... Default = 64, modify it if needed
                mplsPWExpBit.... ............. Default = 0, modify it if needed
                mplsTunnelLabel .............. Default = None: no Tunnel creation 
                                               In a Tunnel + Pseudowire configuration, this parameter must contain the 
                                               mpls tunnel label. 
                mplsTunnelTTL ................ Default = 64, modify it if needed
                mplsTunnelExpBit ............. Default = 0, modify it if needed
                                               
            Return tuple:
                    ("True|False" , "answer_string"  )
                    True.............init traffic success (or already initialized, anyway ready for the next step) 
                    False............init traffic failed
                    answer_string....message for humans, to better understand
                                     what happened in the processing flow
        """
        
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] ".format(methodLocalName))        
        
        # Parameter validation
        if flowGroupName == None:
            localMessage = "[{}] flowGroupName [{}] not valid".format(methodLocalName, flowGroupName)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", localMessage)
        if flowGroupName not in self.__flowName2streamIndexMap.keys():
            localMessage = "[{}] flowGroupName [{}] not present in the streamIndex map: call add_L2_3_Quick_Flow_Group before.".format(methodLocalName, flowGroupName)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", localMessage)
        streamIndex = self.__flowName2streamIndexMap[flowGroupName]  
        localMessage = "[{}] Stream index [{}] found for flowGroupName [{}]".format(methodLocalName, streamIndex, flowGroupName )
        self.__lc_msg(localMessage)
        
        try:
            #================================================================================================
            # VLAN and INNER VLAN tags management ===========================================================
            #================================================================================================
            if vLanId != None: # add  VLAN protocol 
                localMessage = "[{}] VLAN protocol initialization vLanId[{}] vLanPrio [{}] ".format(methodLocalName,vLanId,vLanPrio)
                self.__lc_msg(localMessage)

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.vlanUserPriority-1"', 
                        '-singleValue',vLanPrio, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', vLanPrio, 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.cfi-2"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', '0', 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.vlanTag.vlanID-3"', 
                        '-singleValue', vLanId, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', vLanId, 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                if innerVLanId == None: # no Inner VLAN Tag added 
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.protocolID-4"', 
                                                 '-singleValue', 'ffff', 
                                                 '-seed', '1', 
                                                 '-optionalEnabled', 'true', 
                                                 '-onTheFlyMask', '0', 
                                                 '-fullMesh', 'false', 
                                                 '-valueList', ['0xffff'], 
                                                 '-stepValue', '0xffff', 
                                                 '-fixedBits', '0xffff', 
                                                 '-fieldValue', 'ffff', 
                                                 '-auto', 'true', 
                                                 '-randomMask', '0xffff', 
                                                 '-trackingEnabled', 'false', 
                                                 '-valueType', 'singleValue', 
                                                 '-activeFieldChoice', 'false', 
                                                 '-startValue', '0xffff', 
                                                 '-countValue', '1')
                    
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-3"/field:"ethernet.fcs-1"', 
                                                 '-singleValue', '0', 
                                                 '-seed', '1', 
                                                 '-optionalEnabled', 'true', 
                                                 '-onTheFlyMask', '0', 
                                                 '-fullMesh', 'false', 
                                                 '-valueList', ['0'], 
                                                 '-stepValue', '0', 
                                                 '-fixedBits', '0', 
                                                 '-fieldValue', '0', 
                                                 '-auto', 'true', 
                                                 '-randomMask', '0', 
                                                 '-trackingEnabled', 'false', 
                                                 '-valueType', 'singleValue', 
                                                 '-activeFieldChoice', 'false', 
                                                 '-startValue', '0', 
                                                 '-countValue', '1')
                else:     # add  inner VLAN protocol 
                    localMessage = "[{}] inner VLAN protocol initialization innerVLanId[{}] innerVLanPrio[{}] ".format(methodLocalName,innerVLanId,innerVLanPrio)
                    self.__lc_msg(localMessage)
                    
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-2"/field:"vlan.header.protocolID-4"', 
                                                  '-singleValue', '8100', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0xffff'], 
                                                  '-stepValue', '0xffff', 
                                                  '-fixedBits', '0xffff', 
                                                  '-fieldValue', '8100', 
                                                  '-auto', 'true', 
                                                  '-randomMask', '0xffff', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0xffff', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.vlanUserPriority-1"', 
                                                  '-singleValue', innerVLanPrio, 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', innerVLanPrio, 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.cfi-2"', 
                                                  '-singleValue', '0', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', '0', 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.vlanTag.vlanID-3"', 
                                                  '-singleValue', innerVLanId, 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0'], 
                                                  '-stepValue', '0', 
                                                  '-fixedBits', '0', 
                                                  '-fieldValue', innerVLanId, 
                                                  '-auto', 'false', 
                                                  '-randomMask', '0', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0', 
                                                  '-countValue', '1')
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem +'/highLevelStream:'  + streamIndex + '/stack:"vlan-3"/field:"vlan.header.protocolID-4"', 
                                                  '-singleValue', 'ffff', 
                                                  '-seed', '1', 
                                                  '-optionalEnabled', 'true', 
                                                  '-onTheFlyMask', '0', 
                                                  '-fullMesh', 'false', 
                                                  '-valueList', ['0xffff'], 
                                                  '-stepValue', '0xffff', 
                                                  '-fixedBits', '0xffff', 
                                                  '-fieldValue', 'ffff', 
                                                  '-auto', 'true', 
                                                  '-randomMask', '0xffff', 
                                                  '-trackingEnabled', 'false', 
                                                  '-valueType', 'singleValue', 
                                                  '-activeFieldChoice', 'false', 
                                                  '-startValue', '0xffff', 
                                                  '-countValue', '1')
 
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-4"/field:"ethernet.fcs-1"', 
                                                  '-singleValue', '0', 
                                                '-seed', '1', 
                                                '-optionalEnabled', 'true', 
                                                '-onTheFlyMask', '0', 
                                                '-fullMesh', 'false', 
                                                '-valueList', ['0'], 
                                                '-stepValue', '0', 
                                                '-fixedBits', '0', 
                                                '-fieldValue', '0', 
                                                '-auto', 'true', 
                                                '-randomMask', '0', 
                                                '-trackingEnabled', 'false', 
                                                '-valueType', 'singleValue', 
                                                '-activeFieldChoice', 'false', 
                                                '-startValue', '0', 
                                                '-countValue', '1')
                self.__IXN.commit()
                localMessage = "[{}] Flow Group [{}] modified with VLAN parameters vLanId[{}] vLanPrio[{}]  innerVLanId[{}] innerVLanPrio[{}]".format(methodLocalName, flowGroupName, vLanId  , vLanPrio, innerVLanId,innerVLanPrio)
                self.__lc_msg(localMessage)
                return  True, localMessage
            ##================================================================================================
            # MPLS PSEUDOWIRE and TUNNEL+PSEUDOWIRE management ===============================================
            #=================================================================================================
            elif mplsPWLabel != None: # add  MPLS protocol 
                localMessage = "[{}] MPLS protocol pseudo wire only initialization mplsPWLabel [{}]".format(methodLocalName,mplsPWLabel)
                self.__lc_msg(localMessage)
                if mplsTunnelLabel != None:
                    localMessage = "[{}] MPLS protocol Tunnel+PseudoWire mplsTunnelLabel [{}] mplsPWLabel [{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel)
                    self.__lc_msg(localMessage)
                    #print("[{}] SWAP Before  TUNNEL[{}]      PW[{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel))
                    #print("[{}] SWAP Before  TTL   [{}]     TTL[{}]".format(methodLocalName,mplsTunnelTTL,mplsPWTTL))
                    #print("[{}] SWAP Before  EXPBIT[{}]  EXPBIT[{}]".format(methodLocalName,mplsTunnelExpBit,mplsPWExpBit))
                    # swap PW and TUNNEL parameters
                    mplsTunnelLabel,  mplsPWLabel   = mplsPWLabel,  mplsTunnelLabel
                    mplsTunnelTTL,    mplsPWTTL     = mplsPWTTL,    mplsTunnelTTL 
                    mplsTunnelExpBit, mplsPWExpBit  = mplsPWExpBit, mplsTunnelExpBit
                    
                    #print("[{}] SWAP AFTER  TUNNEL[{}]      PW[{}]".format(methodLocalName,mplsTunnelLabel,mplsPWLabel))
                    #print("[{}] SWAP AFTER  TTL   [{}]     TTL[{}]".format(methodLocalName,mplsTunnelTTL,mplsPWTTL))
                    #print("[{}] SWAP AFTER  EXPBIT[{}]  EXPBIT[{}]".format(methodLocalName,mplsTunnelExpBit,mplsPWExpBit))
                    bottomOfStack="1"
                else:
                    bottomOfStack="1"

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.value-1"', 
                        '-singleValue', mplsPWLabel, 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['16'], 
                        '-stepValue', '16', 
                        '-fixedBits', '16', 
                        '-fieldValue', mplsPWLabel, 
                        '-auto', 'false', 
                        '-randomMask', '16', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '16', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.experimental-2"', 
                        '-singleValue', mplsPWExpBit, # '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0'], 
                        '-stepValue', '0', 
                        '-fixedBits', '0', 
                        '-fieldValue', mplsPWExpBit, # '0', 
                        '-auto', 'false', 
                        '-randomMask', '0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.bottomOfStack-3"', 
                        '-singleValue', '1', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['1'], 
                        '-stepValue', '1', 
                        '-fixedBits', '1', 
                        '-fieldValue', '1', 
                        '-auto', 'true', 
                        '-randomMask', '1', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '1', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.ttl-4"', 
                        '-singleValue', mplsPWTTL, # '64', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['64'], 
                        '-stepValue', '64', 
                        '-fixedBits', '64', 
                        '-fieldValue', mplsPWTTL, # '64', 
                        '-auto', 'false', 
                        '-randomMask', '64', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '64', 
                        '-countValue', '1')

                self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-2"/field:"mpls.label.tracker-5"', 
                        '-singleValue', '0', 
                        '-seed', '1', 
                        '-optionalEnabled', 'true', 
                        '-onTheFlyMask', '0', 
                        '-fullMesh', 'false', 
                        '-valueList', ['0x0'], 
                        '-stepValue', '0x0', 
                        '-fixedBits', '0x0', 
                        '-fieldValue', '0', 
                        '-auto', 'false', 
                        '-randomMask', '0x0', 
                        '-trackingEnabled', 'false', 
                        '-valueType', 'singleValue', 
                        '-activeFieldChoice', 'false', 
                        '-startValue', '0x0', 
                        '-countValue', '1')

                if mplsTunnelLabel != None:
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.value-1"', 
                                                     '-singleValue', mplsTunnelLabel, 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['16'], 
                                                     '-stepValue', '16', 
                                                     '-fixedBits', '16', 
                                                     '-fieldValue', mplsTunnelLabel, 
                                                     '-auto', 'false', 
                                                     '-randomMask', '16', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '16', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.experimental-2"', 
                                                     '-singleValue', mplsTunnelExpBit, # '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', mplsTunnelExpBit, # '0',  
                                                     '-auto', 'false', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.bottomOfStack-3"', 
                                                     '-singleValue', '1', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['1'], 
                                                     '-stepValue', '1', 
                                                     '-fixedBits', '1', 
                                                     '-fieldValue', '1', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '1', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '1', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.ttl-4"', 
                                                     '-singleValue', mplsTunnelTTL, #'64', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['64'], 
                                                     '-stepValue', '64', 
                                                     '-fixedBits', '64', 
                                                     '-fieldValue', mplsTunnelTTL, #'64',  
                                                     '-auto', 'false', 
                                                     '-randomMask', '64', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '64', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"mpls-3"/field:"mpls.label.tracker-5"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0x0'], 
                                                     '-stepValue', '0x0', 
                                                     '-fixedBits', '0x0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'false', 
                                                     '-randomMask', '0x0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0x0', 
                                                     '-countValue', '1')
                        
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-4"/field:"ethernet.fcs-1"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')
                else:  # terminate single MPLS Label Structure  
                    self.__IXN.setMultiAttribute(self.__globalTrafficItem + '/highLevelStream:'  + streamIndex + '/stack:"fcs-3"/field:"ethernet.fcs-1"', 
                                                     '-singleValue', '0', 
                                                     '-seed', '1', 
                                                     '-optionalEnabled', 'true', 
                                                     '-onTheFlyMask', '0', 
                                                     '-fullMesh', 'false', 
                                                     '-valueList', ['0'], 
                                                     '-stepValue', '0', 
                                                     '-fixedBits', '0', 
                                                     '-fieldValue', '0', 
                                                     '-auto', 'true', 
                                                     '-randomMask', '0', 
                                                     '-trackingEnabled', 'false', 
                                                     '-valueType', 'singleValue', 
                                                     '-activeFieldChoice', 'false', 
                                                     '-startValue', '0', 
                                                     '-countValue', '1')

                self.__IXN.commit()
                localMessage = "[{}] Flow Group [{}] modified with MPLS parameters  mplsTunnelLabel[{}] mplsTunnelTTL[{}] mplsTunnelExpBit[{}] mplsPWLabel[{}] mplsPWTTL[{}] mplsPWExpBit[{}]".format(methodLocalName, flowGroupName,mplsTunnelLabel ,mplsTunnelTTL, mplsTunnelExpBit, mplsPWLabel ,mplsPWTTL ,mplsPWExpBit)
                self.__lc_msg(localMessage)
                return  True, localMessage
            #================================================================================================
            # - NOTHING TO DO - =============================================================================
            #================================================================================================
            else: # No VLAN / MPLS modification required 
                pass
        except Exception as excMsg:
            localMessage = "[{}]  Flow Group [{}] Vlan/MPLS parameters modify error".format(methodLocalName, streamIndex)
            self.__lc_msg(localMessage)
            return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))
        localMessage = "[{}] Flow Group [{}]: no Vlan/MPLS parameters modified".format(methodLocalName, flowGroupNamel)
        self.__lc_msg(localMessage)
        return  True, localMessage






    def start_traffic(self,timeToWait=0):
        """
            Method:
                start_traffic 

            Purpose:
                Start the traffic and wait for timeToWait second.

            Usage:
                InstrumentIXIA.start_traffic()
            Parameters:
                timeToWait ......... Default: 0
                                     It specifies the period of time to wait after starting the traffic,
                                     May be used to define the duration of the traffic without the need to 
                                     use time.sleep() externally in the code of your test.
                                     BE CARE!!! : after <timeToWait > second, the traffic will lcontinue,
                                     until you don't stop it with the  stop_traffic() call. 
             Return tuple: 
                 Not meaningful: always True, success / success
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] Start traffic and wait for {}sec".format(methodLocalName, timeToWait))
        self.__IXN.execute('generate', self.__globalTrafficItem)
        self.__IXN.execute('apply', self.__ROOT + '/traffic')
        self.__IXN.execute('start', self.__ROOT + '/traffic')
        self.__lc_msg("[{}] Traffic now started".format(methodLocalName))
        time.sleep(timeToWait)
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )



    def stop_traffic(self,timeToStop=0):
        """
            Method:
                stop_traffic 

            Purpose:
                Stop the traffic after <timeToStop> second.

            Usage:
                InstrumentIXIA.start_traffic()
            Parameters:
                timeToStop ......... Default: 0
                                     It specifies the period of time to wait before stopping the traffic,
                                     May be used to define the duration of the traffic without the need to 
                                     use time.sleep() externally in the code of your test.
                                     BE CARE!!! : after <timeToStop > second, the traffic will be stopped.
             Return tuple: 
                 Not meaningful: always True, success / success
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] Traffic will be stopped in {}sec".format(methodLocalName,timeToStop))
        time.sleep(timeToStop)
        self.__IXN.execute('stop', self.__ROOT + '/traffic')
        self.__lc_msg("[{}] Traffic now stopped".format(methodLocalName))
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )



    def start_all_protocols(self,timeToWait=20):
        """
            Method:
                start_all_protocols 

            Purpose:
                Initializize all protocols.

            Usage:
                InstrumentIXIA.start_all_protocols()
                
            Parameters:
                timeToWait ......... Default: 20
                                     It starts all protocols, and must be created at the beginning of the test body.
                                     The timeToWait period is used to allow the correct protocols initializations             
             Return tuple: 
                 Not meaningful: always True, success / success
        """
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        self.__lc_msg("[{}] Start protocols and wait for {}sec".format(methodLocalName, timeToWait))
        self.__IXN.execute('startAllProtocols')
        time.sleep(timeToWait)
        self.__lc_msg("[{}] Protocols now started".format( timeToWait))
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )





    def init_custom_statistic_view(self):
        """
            Method: 
                init_custom_statistic_view 

            Purpose:
                Initializes the custom statistic view in order to allow the retrieve of
                all the required conters
                
            Usage:
                Call this method BEFORE the traffic starts, in order to initialize the collection 
                of the counters, creating a custom view "kateview" on the IxNetwork

                This method creates a brand-new set of counters to retrieve the following statistics:
                Statistic Name              Value                             
                [Stat Name]               = [151.98.130.42/Card01/Port01] 
                [Link State]              = [Link Up] 
                [Line Speed]              = [1000 Mbps] 
                [Frames Tx.]              = [1862124] 
                [Valid Frames Rx.]        = [1334623] 
                [Bytes Tx.]               = [2140992330] 
                [Bytes Rx.]               = [2140992330] 
                [Oversize]                = [527501] 
                [Vlan Tagged Frames]      = [1338786] 
                [Bits Sent]               = [17127938640] 
                [Bits Received]           = [17127938640] 
                [Frames Tx. Rate]         = [100000]    **   
                [Oversize Rate]           = [28057]     ** 
                [Vlan Tagged Frames Rate] = [71943]     ** 
                [Bits Sent Rate]          = [918944382] ** 
                [Bits Received Rate]      = [918944382] ** 
                    
                 ** to retrieve "Rate" counters, the traffic must be still running   

            Parameters:
                 <none>
        
            Return tuple:
                ("True|False" , "answer_string"  )
                True.............connection success
                False............connection failed
                answer_string....message for humans, to better understand
                                 what happened in the processing flow
        """
        methodLocalName = self.__lc_current_method_name()
        localPortNameList = []
        statisticViewItemsList = []
        try:
            self.__globalStatisticView = self.__IXN.add(self.__ROOT +'/statistics', 'view')
            self.__IXN.setMultiAttribute(self.__globalStatisticView, 
                                         '-pageTimeout', '25000', 
                                         '-csvFileName', 'kateview.csv', 
                                         '-enableCsvLogging', 'false', 
                                         '-type', 'layer23ProtocolPort', 
                                         '-treeViewNodeName', 'Views\\Custom Views', 
                                         '-caption', 'kateview', 
                                         '-timeSeries', 'false', 
                                         '-visible', 'true', 
                                         '-autoUpdate', 'true')
            self.__IXN.commit()
            self.__globalStatisticView = self.__IXN.remapIds(self.__globalStatisticView)[0]
        except Exception as excMsg:
            localMessage = "[{}] *** Exception #1 [{}] *** ".format(methodLocalName,excMsg )
            self.__lc_msg(localMessage)
            return  False, localMessage 
        portIndex=1
        for localVPort in self.__IXN.getList(self.__ROOT, 'vport'):
            localName = self.__IXN.getAttribute(localVPort ,'-name')
            localPortNameList.append(localName)
            tempItemName= "{}/availablePortFilter:\"{}:{}\"".format(self.__globalStatisticView ,portIndex,localName)
            statisticViewItemsList.append(tempItemName)
            portIndex += 1

        #localMessage = "[{}] AFTER   statisticViewItemsList [ {} ]".format(methodLocalName, statisticViewItemsList )
        #self.__lc_msg(localMessage)
            
        try:    
            self.__globalLayer23ProtoPortFilter = self.__IXN.add(self.__globalStatisticView, 'layer23ProtocolPortFilter')
            self.__IXN.commit()
            self.__globalLayer23ProtoPortFilter = self.__IXN.remapIds(self.__globalLayer23ProtoPortFilter)[0]
            self.__IXN.setMultiAttribute(self.__globalLayer23ProtoPortFilter, '-portFilterIds', statisticViewItemsList)
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port Name"', '-caption', 'Port Name', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Link State"', '-caption', 'Link State', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Line Speed"', '-caption', 'Line Speed', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Duplex Mode"', '-caption', 'Duplex Mode', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Frames Tx."', '-caption', 'Frames Tx.', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Valid Frames Rx."', '-caption', 'Valid Frames Rx.', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bytes Tx."', '-caption', 'Bytes Tx.', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bytes Rx."', '-caption', 'Bytes Rx.', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Fragments"', '-caption', 'Fragments', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Undersize"', '-caption', 'Undersize', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Oversize"', '-caption', 'Oversize', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CRC Errors"', '-caption', 'CRC Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Vlan Tagged Frames"', '-caption', 'Vlan Tagged Frames', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Flow Control Frames"', '-caption', 'Flow Control Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Alignment Errors"', '-caption', 'Alignment Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Dribble Errors"', '-caption', 'Dribble Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Collisions"', '-caption', 'Collisions', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Late Collisions"', '-caption', 'Late Collisions', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Collision Frames"', '-caption', 'Collision Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Excessive Collision Frames"', '-caption', 'Excessive Collision Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat 1"', '-caption', 'User Defined Stat 1', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat 2"', '-caption', 'User Defined Stat 2', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Capture Trigger (UDS 3)"', '-caption', 'Capture Trigger (UDS 3)', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Capture Filter (UDS 4)"', '-caption', 'Capture Filter (UDS 4)', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Control Frames Tx"', '-caption', 'Control Frames Tx', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Control Frames Rx"', '-caption', 'Control Frames Rx', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Arp Reply"', '-caption', 'Transmit Arp Reply', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Arp Request"', '-caption', 'Transmit Arp Request', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Ping Reply"', '-caption', 'Transmit Ping Reply', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Ping Request"', '-caption', 'Transmit Ping Request', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Arp Reply"', '-caption', 'Receive Arp Reply', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Arp Request"', '-caption', 'Receive Arp Request', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Ping Reply"', '-caption', 'Receive Ping Reply', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Ping Request"', '-caption', 'Receive Ping Request', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Protocol Server Vlan Dropped Frames"', '-caption', 'Protocol Server Vlan Dropped Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Duration(Cleared on Start Tx)"', '-caption', 'Transmit Duration(Cleared on Start Tx)', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bytes Sent / Transmit Duration"', '-caption', 'Bytes Sent / Transmit Duration', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bits Sent"', '-caption', 'Bits Sent', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bits Received"', '-caption', 'Bits Received', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Scheduled Transmit Duration"', '-caption', 'Scheduled Transmit Duration', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Frames Tx. Rate"', '-caption', 'Frames Tx. Rate', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Valid Frames Rx. Rate"', '-caption', 'Valid Frames Rx. Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bytes Tx. Rate"', '-caption', 'Bytes Tx. Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Tx. Rate (bps)"', '-caption', 'Tx. Rate (bps)', '-scaleFactor', '8', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Tx. Rate (Kbps)"', '-caption', 'Tx. Rate (Kbps)', '-scaleFactor', '0,008', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Tx. Rate (Mbps)"', '-caption', 'Tx. Rate (Mbps)', '-scaleFactor', '0,000008', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bytes Rx. Rate"', '-caption', 'Bytes Rx. Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx. Rate (bps)"', '-caption', 'Rx. Rate (bps)', '-scaleFactor', '8', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx. Rate (Kbps)"', '-caption', 'Rx. Rate (Kbps)', '-scaleFactor', '0,008', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx. Rate (Mbps)"', '-caption', 'Rx. Rate (Mbps)', '-scaleFactor', '0,000008', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Fragments Rate"', '-caption', 'Fragments Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Undersize Rate"', '-caption', 'Undersize Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Oversize Rate"', '-caption', 'Oversize Rate', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CRC Errors Rate"', '-caption', 'CRC Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Vlan Tagged Frames Rate"', '-caption', 'Vlan Tagged Frames Rate', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Flow Control Frames Rate"', '-caption', 'Flow Control Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Alignment Errors Rate"', '-caption', 'Alignment Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Dribble Errors Rate"', '-caption', 'Dribble Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Collisions Rate"', '-caption', 'Collisions Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Late Collisions Rate"', '-caption', 'Late Collisions Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Collision Frames Rate"', '-caption', 'Collision Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Excessive Collision Frames Rate"', '-caption', 'Excessive Collision Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat 1 Rate"', '-caption', 'User Defined Stat 1 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat 2 Rate"', '-caption', 'User Defined Stat 2 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Capture Trigger (UDS 3) Rate"', '-caption', 'Capture Trigger (UDS 3) Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Capture Filter (UDS 4) Rate"', '-caption', 'Capture Filter (UDS 4) Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bits Sent Rate"', '-caption', 'Bits Sent Rate', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Bits Received Rate"', '-caption', 'Bits Received Rate', '-scaleFactor', '1', '-enabled', 'true', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Oversize and CRC Errors"', '-caption', 'Oversize and CRC Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Data Integrity Frames Rx."', '-caption', 'Data Integrity Frames Rx.', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Data Integrity Errors"', '-caption', 'Data Integrity Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Sequence Frames"', '-caption', 'Sequence Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Sequence Errors"', '-caption', 'Sequence Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Scheduled Frames Tx."', '-caption', 'Scheduled Frames Tx.', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Asynchronous Frames Sent"', '-caption', 'Asynchronous Frames Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port CPU Frames Sent"', '-caption', 'Port CPU Frames Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port CPU Status"', '-caption', 'Port CPU Status', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port CPU DoD Status"', '-caption', 'Port CPU DoD Status', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Neighbor Solicitation"', '-caption', 'Transmit Neighbor Solicitation', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Transmit Neighbor Advertisements"', '-caption', 'Transmit Neighbor Advertisements', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Neighbor Solicitation"', '-caption', 'Receive Neighbor Solicitation', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Receive Neighbor Advertisements"', '-caption', 'Receive Neighbor Advertisements', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Oversize and CRC Errors Rate"', '-caption', 'Oversize and CRC Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Data Integrity Frames Rate"', '-caption', 'Data Integrity Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Data Integrity Errors Rate"', '-caption', 'Data Integrity Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Sequence Frames Rate"', '-caption', 'Sequence Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Sequence Errors Rate"', '-caption', 'Sequence Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Scheduled Frames Tx. Rate"', '-caption', 'Scheduled Frames Tx. Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Asynchronous Frames Sent Rate"', '-caption', 'Asynchronous Frames Sent Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port CPU Frames Sent Rate"', '-caption', 'Port CPU Frames Sent Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"RAM Disk Utilization"', '-caption', 'RAM Disk Utilization', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Total Memory"', '-caption', 'Total Memory', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Free Memory"', '-caption', 'Free Memory', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Load Avg (1 Minute)"', '-caption', 'CPU Load Avg (1 Minute)', '-scaleFactor', '0,01', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Load Avg (5 Minutes)"', '-caption', 'CPU Load Avg (5 Minutes)', '-scaleFactor', '0,01', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Load Avg (15 Minutes)"', '-caption', 'CPU Load Avg (15 Minutes)', '-scaleFactor', '0,01', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Idle"', '-caption', 'CPU Idle', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"%CPU Load"', '-caption', '%CPU Load', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Discovered Messages Sent"', '-caption', 'DHCPv4 Discovered Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Offers Received"', '-caption', 'DHCPv4 Offers Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Requests Sent"', '-caption', 'DHCPv4 Requests Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 ACKs Received"', '-caption', 'DHCPv4 ACKs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 NACKs Received"', '-caption', 'DHCPv4 NACKs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Releases Sent"', '-caption', 'DHCPv4 Releases Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Enabled Interfaces"', '-caption', 'DHCPv4 Enabled Interfaces', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"DHCPv4 Addresses Learned"', '-caption', 'DHCPv4 Addresses Learned', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Central Chip Temperature(C)"', '-caption', 'Central Chip Temperature(C)', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Port Chip Temperature(C)"', '-caption', 'Port Chip Temperature(C)', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size less than 64"', '-caption', 'CPU Rx Frame Size less than 64', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 64 to 127"', '-caption', 'CPU Rx Frame Size 64 to 127', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 128 to 255"', '-caption', 'CPU Rx Frame Size 128 to 255', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 256 to 511"', '-caption', 'CPU Rx Frame Size 256 to 511', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 512 to 1023"', '-caption', 'CPU Rx Frame Size 512 to 1023', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 1024 to 2047"', '-caption', 'CPU Rx Frame Size 1024 to 2047', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 2048 to 4095"', '-caption', 'CPU Rx Frame Size 2048 to 4095', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Rx Frame Size 4096 and above"', '-caption', 'CPU Rx Frame Size 4096 and above', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size less than 64"', '-caption', 'CPU Tx Frame Size less than 64', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 64 to 127"', '-caption', 'CPU Tx Frame Size 64 to 127', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 128 to 255"', '-caption', 'CPU Tx Frame Size 128 to 255', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 256 to 511"', '-caption', 'CPU Tx Frame Size 256 to 511', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 512 to 1023"', '-caption', 'CPU Tx Frame Size 512 to 1023', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 1024 to 2047"', '-caption', 'CPU Tx Frame Size 1024 to 2047', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 2048 to 4095"', '-caption', 'CPU Tx Frame Size 2048 to 4095', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"CPU Tx Frame Size 4096 and above"', '-caption', 'CPU Tx Frame Size 4096 and above', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"IPv4 Packets Received"', '-caption', 'IPv4 Packets Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"UDP Packets Received"', '-caption', 'UDP Packets Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"TCP Packets Received"', '-caption', 'TCP Packets Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"IPv4 Checksum Errors"', '-caption', 'IPv4 Checksum Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"UDP Checksum Errors"', '-caption', 'UDP Checksum Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"TCP Checksum Errors"', '-caption', 'TCP Checksum Errors', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Information PDUs Sent"', '-caption', 'Ethernet OAM Information PDUs Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Information PDUs Received"', '-caption', 'Ethernet OAM Information PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Event Notification PDUs Received"', '-caption', 'Ethernet OAM Event Notification PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Loopback Control PDUs Received"', '-caption', 'Ethernet OAM Loopback Control PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Organisation PDUs Received"', '-caption', 'Ethernet OAM Organisation PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Variable Request PDUs Received"', '-caption', 'Ethernet OAM Variable Request PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Variable Response Received"', '-caption', 'Ethernet OAM Variable Response Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ethernet OAM Unsupported PDUs Received"', '-caption', 'Ethernet OAM Unsupported PDUs Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Announce Messages Sent"', '-caption', 'Ptp Announce Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Announce Messages Received"', '-caption', 'Ptp Announce Messages Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Sync Messages Sent"', '-caption', 'Ptp Sync Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Sync Messages Received"', '-caption', 'Ptp Sync Messages Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Follow_Up Messages Sent"', '-caption', 'Ptp Follow_Up Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Follow_Up Messages Received"', '-caption', 'Ptp Follow_Up Messages Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Delay_Req Messages Sent"', '-caption', 'Ptp Delay_Req Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Delay_Req Messages Received"', '-caption', 'Ptp Delay_Req Messages Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Delay_Resp Messages Sent"', '-caption', 'Ptp Delay_Resp Messages Sent', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Ptp Delay_Resp Messages Received"', '-caption', 'Ptp Delay_Resp Messages Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Misdirected Packet Count"', '-caption', 'Misdirected Packet Count', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Frames Received"', '-caption', 'Prbs Frames Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Frames With Header Error"', '-caption', 'Prbs Frames With Header Error', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Bits Received"', '-caption', 'Prbs Bits Received', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Errored Bits"', '-caption', 'Prbs Errored Bits', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Ber Ratio"', '-caption', 'Prbs Ber Ratio', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat Byte Count 1"', '-caption', 'User Defined Stat Byte Count 1', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat Byte Count 2"', '-caption', 'User Defined Stat Byte Count 2', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"IPv4 Packets Received Rate"', '-caption', 'IPv4 Packets Received Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"UDP Packets Received Rate"', '-caption', 'UDP Packets Received Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"TCP Packets Received Rate"', '-caption', 'TCP Packets Received Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"IPv4 Checksum Errors Rate"', '-caption', 'IPv4 Checksum Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"UDP Checksum Errors Rate"', '-caption', 'UDP Checksum Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"TCP Checksum Errors Rate"', '-caption', 'TCP Checksum Errors Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Misdirected Packet Count Rate"', '-caption', 'Misdirected Packet Count Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Frames Received Rate"', '-caption', 'Prbs Frames Received Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Frames With Header Error Rate"', '-caption', 'Prbs Frames With Header Error Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Bits Received Rate"', '-caption', 'Prbs Bits Received Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Prbs Errored Bits Rate"', '-caption', 'Prbs Errored Bits Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat Byte Count 1 Rate"', '-caption', 'User Defined Stat Byte Count 1 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"User Defined Stat Byte Count 2 Rate"', '-caption', 'User Defined Stat Byte Count 2 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause Acknowledge"', '-caption', 'Pause Acknowledge', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause End Frames"', '-caption', 'Pause End Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause Overwrite"', '-caption', 'Pause Overwrite', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Shared Stat 1"', '-caption', 'Rx Shared Stat 1', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Shared Stat 2"', '-caption', 'Rx Shared Stat 2', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 0 Frames"', '-caption', 'Rx Pause Priority Group 0 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 1 Frames"', '-caption', 'Rx Pause Priority Group 1 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 2 Frames"', '-caption', 'Rx Pause Priority Group 2 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 3 Frames"', '-caption', 'Rx Pause Priority Group 3 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 4 Frames"', '-caption', 'Rx Pause Priority Group 4 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 5 Frames"', '-caption', 'Rx Pause Priority Group 5 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 6 Frames"', '-caption', 'Rx Pause Priority Group 6 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 7 Frames"', '-caption', 'Rx Pause Priority Group 7 Frames', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause Acknowledge Rate"', '-caption', 'Pause Acknowledge Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause End Frames Rate"', '-caption', 'Pause End Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Pause Overwrite Rate"', '-caption', 'Pause Overwrite Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Shared Stat 1 Rate"', '-caption', 'Rx Shared Stat 1 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Shared Stat 2 Rate"', '-caption', 'Rx Shared Stat 2 Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 0 Frames Rate"', '-caption', 'Rx Pause Priority Group 0 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 1 Frames Rate"', '-caption', 'Rx Pause Priority Group 1 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 2 Frames Rate"', '-caption', 'Rx Pause Priority Group 2 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 3 Frames Rate"', '-caption', 'Rx Pause Priority Group 3 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 4 Frames Rate"', '-caption', 'Rx Pause Priority Group 4 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 5 Frames Rate"', '-caption', 'Rx Pause Priority Group 5 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 6 Frames Rate"', '-caption', 'Rx Pause Priority Group 6 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')  
            self.__IXN.setMultiAttribute(self.__globalStatisticView+'/statistic:"Rx Pause Priority Group 7 Frames Rate"', '-caption', 'Rx Pause Priority Group 7 Frames Rate', '-scaleFactor', '1', '-enabled', 'false', '-aggregationType', 'none')    
            self.__IXN.commit()
            # Deferred attributes for /statistics/view[6] node
            self.__IXN.setMultiAttribute(self.__globalStatisticView, '-enabled', 'true')
            self.__IXN.commit()
        except Exception as excMsg:
            localMessage = "[{}] *** Exception #2 [{}] *** ".format(methodLocalName,excMsg )
            self.__lc_msg(localMessage)
            return  False, localMessage 
        localMessage = "[{}] Custom Statistic View Initialized".format(methodLocalName)
        self.__lc_msg(localMessage)
        return True, localMessage



    def get_port_custom_statistic(self, vPortId):
        '''
            Method: 
                get_port_custom_statistic 

            Purpose:
                Get the kateview's custom statistics for the vportId port

                
            Usage:
                Example:
                Port Id definition:
                  IdPort_1=('151.98.130.42', 1, 1)
                ...
                after traffic start
                ...
                  retCode1=IXIA.get_port_custom_statistic(IdPort_1)
                  port1CountersDict=retCode1[1]   # <-- this code allows to extract the dictionary containing the counters
                  print("DICT port 1 ONLY:[{}]".format(port1CountersDict))  

                In case of (True, ...) answer, the returned dictionary contains the 
                following counters values for the specified port:
                
                Statistic Name              Value                             
                [Stat Name]               = [151.98.130.42/Card01/Port01] 
                [Link State]              = [Link Up] 
                [Line Speed]              = [1000 Mbps] 
                [Frames Tx.]              = [1862124] 
                [Valid Frames Rx.]        = [1334623] 
                [Bytes Tx.]               = [2140992330] 
                [Bytes Rx.]               = [2140992330] 
                [Oversize]                = [527501] 
                [Vlan Tagged Frames]      = [1338786] 
                [Bits Sent]               = [17127938640] 
                [Bits Received]           = [17127938640] 
                [Frames Tx. Rate]         = [100000]    **   
                [Oversize Rate]           = [28057]     ** 
                [Vlan Tagged Frames Rate] = [71943]     ** 
                [Bits Sent Rate]          = [918944382] ** 
                [Bits Received Rate]      = [918944382] ** 
                    
                 ** to retrieve "Rate" counters, the traffic must be still running   

            Parameters:
                 <none>
        
            Return tuple:
                ("True|False" ,CounterDictionary|"answer_string"  )
                True.............connection success: the next item in the tuple is the "CounterDictionary"
                                 When the answer is True, the second field of the returned tuple contains 
                                 the dictionary in which the counters are stored.
                False............connection failed:  the next item in the tuple is an answer string to understand
                                 what happened in the processing flow
                                 When the answer is False, the second field of the returned tuple contains 
                                 a message string.
        '''
        methodLocalName = self.__lc_current_method_name()
        
        # Initial checks
        if vPortId == None:
           return  False, "ERROR: [{}] vPortId [{}] not specified".format(methodLocalName,vPortId)
        if vPortId not in self.__alreadyAddedVPort: 
           return  False, "ERROR: [{}] vPortId [{}] not initialized (have you executed bind_new_vports() ?)".format(methodLocalName,vPortId)
        if vPortId not in self.__vPortList: 
           return  False, "ERROR: [{}] vPortId [{}] not in self.__vPortList (have you created this port?) ".format(methodLocalName,vPortId)

        localMessage = "[{}] vPortId [{}] extraction:".format(methodLocalName, vPortId)
        self.__lc_msg(localMessage)
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)
        
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)
        self.__lc_msg("Statistic to Retrieve [{}]".format(StatisticToRetrieve))
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','kateview')[0]
        except Exception as excMsg:
            retDictionary=dict()
            self.__lc_msg("Exception [{}]".format(excMsg))
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve not in statisticRow:
                continue
            self.__lc_msg("Found statistics for [{}] ".format(StatisticToRetrieve))
            for paramName, paramValue in zip(statsColsName,statisticRow):
                self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionary=dict(zip(statsColsName,statisticRow) )
        return  True,retDictionary



    def get_port_statistic(self, vPortId):
        '''
            Method: 
                get_port_statistic 

            Purpose:
                Get the port statistics for the vportId port

                
            Usage:
                Example:
                Port Id definition:
                  IdPort_1=('151.98.130.42', 1, 1)
                ...
                after traffic start
                ...
                  retCode1=IXIA.get_port_statistic(IdPort_1)
                  port1CountersDict=retCode1[1]   # <-- this code allows to extract the dictionary containing the counters
                  print("DICT port 1 ONLY:[{}]".format(port1CountersDict))  

                In case of (True, ...) answer, the returned dictionary contains the 
                following counters values for the specified port:
                
                Statistic Name              Value                             
                [Stat Name] = [135.221.113.142/Card02/Port03]
                [Port Name] = [Ethernet - 002]
                [Duplex Mode] = [Full]
                [Line Speed] = [1000 Mbps]
                [Link State] = [Link Up]
                [Frames Tx.] = [0]
                [Valid Frames Rx.] = [10000]
                [Frames Tx. Rate] = [0]
                [Valid Frames Rx. Rate] = [0] ** 
                [Data Integrity Frames Rx.] = [10000]
                [Data Integrity Errors] = [0]
                [Bytes Tx.] = [0]
                [Bytes Rx.] = [1280000]
                [Bits Sent] = [0]
                [Bits Received] = [10240000]
                [Bytes Tx. Rate] = [0]
                [Tx. Rate (bps)] = [0] ** 
                [Tx. Rate (Kbps)] = [0] ** 
                [Tx. Rate (Mbps)] = [0] ** 
                [Bytes Rx. Rate] = [0] ** 
                [Rx. Rate (bps)] = [0] ** 
                [Rx. Rate (Kbps)] = [0] ** 
                [Rx. Rate (Mbps)] = [0] ** 
                [Scheduled Frames Tx.] = [0]
                [Scheduled Frames Tx. Rate] = [0] ** 
                [Collisions] = [0]
                [Control Frames Tx] = [0]
                [Control Frames Rx] = [0]
                [Ethernet OAM Information PDUs Sent] = [0]
                [Ethernet OAM Information PDUs Received] = [0]
                [Ethernet OAM Event Notification PDUs Received] = [0]
                [Ethernet OAM Loopback Control PDUs Received] = [0]
                [Ethernet OAM Organisation PDUs Received] = [0]
                [Ethernet OAM Variable Request PDUs Received] = [0]
                [Ethernet OAM Variable Response Received] = [0]
                [Ethernet OAM Unsupported PDUs Received] = [0]
                [Misdirected Packet Count] = [0]
                [CRC Errors] = [0]
                    
                 ** to retrieve "Rate" counters, the traffic must be still running   

            Parameters:
                vPortId of the port to read it's counters
                
            Return tuple:
                ("True|False" ,CounterDictionary|"answer_string"  )
                True.............connection success: the next item in the tuple is the "CounterDictionary"
                                 When the answer is True, the second field of the returned tuple contains 
                                 the dictionary in which the counters are stored.
                False............connection failed:  the next item in the tuple is an answer string to understand
                                 what happened in the processing flow
                                 When the answer is False, the second field of the returned tuple contains 
                                 a message string.

        '''
        #  def ret_port_traffic(self, portNumber, **retValue):
        methodLocalName = self.__lc_current_method_name()
        
        # Initial checks
        if vPortId == None:
           return  False, "ERROR: [{}] vPortId [{}] not specified".format(methodLocalName,vPortId)
        if vPortId not in self.__alreadyAddedVPort: 
           return  False, "ERROR: [{}] vPortId [{}] not initialized (have you executed bind_new_vports() ?)".format(methodLocalName,vPortId)
        if vPortId not in self.__vPortList: 
           return  False, "ERROR: [{}] vPortId [{}] not in self.__vPortList (have you created this port?) ".format(methodLocalName,vPortId)

        localMessage = "[{}] vPortId [{}] extraction:".format(methodLocalName, vPortId)
        self.__lc_msg(localMessage)
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)
        
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)
        self.__lc_msg("Statistic to Retrieve [{}]".format(StatisticToRetrieve))
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port Statistics')[0]
        except Exception as excMsg:
            retDictionary=dict()
            self.__lc_msg("Exception [{}]".format(excMsg))
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve not in statisticRow:
                continue
            self.__lc_msg("Found statistics for [{}] ".format(StatisticToRetrieve))
            for paramName, paramValue in zip(statsColsName,statisticRow):
                self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionary=dict(zip(statsColsName,statisticRow) )
        return  True,retDictionary



    def check_traffic(self):
        '''
            Method: 
                check_traffic 

            Purpose:
                Get other suitable statistics to read data traffic
            Usage:
                InstrumentIXIA.check_traffic()
                
                In case of (True, ...) answer, the returned dictionary contains counters 
 
            Parameters:
                 <none>
        
            Return tuple:
                ("True|False" ,CounterDictionary|"answer_string"  )
                True.............connection success: the next item in the tuple is the "CounterDictionary"
                                 When the answer is True, the second field of the returned tuple contains 
                                 the dictionary in which the counters are stored.
                False............connection failed:  the next item in the tuple is an answer string to understand
                                 what happened in the processing flow
                                 When the answer is False, the second field of the returned tuple contains 
                                 a message string.

        '''
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        views = self.__IXN.getList('/statistics', 'view')
        for listItem in views:
            self.__lc_msg("Statistic entry   [{}]  ".format(listItem))
        portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port Statistics')[0]
        self.__lc_msg("portStats_1 [{}]  ".format(portStats_1))
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        self.__lc_msg("[{}]  ".format(statsColsName))
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            for paramName, paramValue in zip(statsColsName,statisticRow)  :
                self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
                retDictionary=dict(zip(statsColsName,statisticRow) )
        return  True,retDictionary





    def get_port_cpu_statistic(self,  vPortId):
        '''
            Method: 
                get_port_cpu_statistic 

            Purpose:
                Get other suitable statistics to cpu load
            Usage:
                InstrumentIXIA.get_port_cpu_statistic(vPortId)
                
                In case of (True, ...) answer, the returned dictionary contains counters 
                Return True/False for Success/Fail cases
                In case of success the port CPU statistic dictionary is returned.
                To access to the single key-values pair, use the following
                keys on the returned dictonary (sample value are provided as an example):
                
                [< key >  ]                [< value as example >]
                [Stat Name]                 = [135.221.113.142/Card02/Port02]
                [Port Name]                 = [Ethernet - 001]
                [Total Memory(KB)]          = [255016]
                [Free Memory(KB)]           = [159600]
                [% Disk Utilization]        = [46]
                [CPU Load Avg (1 Minute)]   = [0]
                [CPU Load Avg (5 Minutes)]  = [0]
                [CPU Load Avg (15 Minutes)] = [0]
                [%CPU Load]                 = [0]
 
            Parameters:
                vPortId
                
            Return tuple:
                ("True|False" ,CounterDictionary|"answer_string"  )
                True.............connection success: the next item in the tuple is the "CounterDictionary"
                                 When the answer is True, the second field of the returned tuple contains 
                                 the dictionary in which the counters are stored.
                False............connection failed:  the next item in the tuple is an answer string to understand
                                 what happened in the processing flow
                                 When the answer is False, the second field of the returned tuple contains 
                                 a message string.
        '''
        methodLocalName = self.__lc_current_method_name()
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)
        
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)
        self.__lc_msg("[{}]Statistic Port CPU 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port CPU Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve  not in statisticRow:
                continue
            else:
                self.__lc_msg("Found  Port CPU statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew




    #====================================================================================================================
    #====================================================================================================================
    #
    #  * * * * *    OTHER CODE BELOW  (minor uses)  * * * * *   
    #
    #====================================================================================================================
    #====================================================================================================================
 
    def get_flow_statistic(self, trafficName):
        '''
           Return True/False for Success/Fail cases
           In case of success the flow statistic dictionary is returned.
           To access to the single key-values pair, use the following
           keys on the returned dictonary (sample value are provided as an example):

            [< key >  ]   [< value as example >]

            [Tx Port] = [Ethernet - 001]
            [Rx Port] = [Ethernet - 002]
            [Traffic Item] = [Traffico di Test]
            [Tx Frames] = [10000]
            [Rx Frames] = [10000]
            [Frames Delta] = [0]
            [Loss %] = [0]
            [Tx Frame Rate] = [0]
            [Rx Frame Rate] = [0]
            [Tx L1 Rate (bps)] = [0]
            [Rx L1 Rate (bps)] = [0]
            [Rx Bytes] = [1280000]
            [Tx Rate (Bps)] = [0]
            [Rx Rate (Bps)] = [0]
            [Tx Rate (bps)] = [0]
            [Rx Rate (bps)] = [0]
            [Tx Rate (Kbps)] = [0]
            [Rx Rate (Kbps)] = [0]
            [Tx Rate (Mbps)] = [0]
            [Rx Rate (Mbps)] = [0]
            [Store-Forward Avg Latency (ns)] = [0]
            [Store-Forward Min Latency (ns)] = [0]
            [Store-Forward Max Latency (ns)] = [0]
            [First TimeStamp] = [00:00:01.354]
            [Last TimeStamp] = [00:00:01.472]
        '''
        methodLocalName = self.__lc_current_method_name()
        self.__lc_msg("[{}]Statistic Flow 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Flow Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')

        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if trafficName  not in statisticRow and trafficName != "TEST":
                continue
            else:
                self.__lc_msg("Found Flow statistics for [{}] ".format(trafficName))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
                retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew





    def get_traffic_item_statistic(self, trafficName):
        '''
           Return True/False for Success/Fail cases
           In case of success the traffic item statistic dictionary is returned.
           To access to the single key-values pair, use the following
           keys on the returned dictonary (sample value are provided as an example):

            [< key >  ]   [< value as example >]

            [Traffic Item] = [Traffico di Test]
            [Tx Frames] = [10000]
            [Rx Frames] = [10000]
            [Frames Delta] = [0]
            [Loss %] = [0]
            [Tx Frame Rate] = [0]
            [Rx Frame Rate] = [0]
            [Tx L1 Rate (bps)] = [0]
            [Rx L1 Rate (bps)] = [0]
            [Rx Bytes] = [1280000]
            [Tx Rate (Bps)] = [0]
            [Rx Rate (Bps)] = [0]
            [Tx Rate (bps)] = [0]
            [Rx Rate (bps)] = [0]
            [Tx Rate (Kbps)] = [0]
            [Rx Rate (Kbps)] = [0]
            [Tx Rate (Mbps)] = [0]
            [Rx Rate (Mbps)] = [0]
            [Store-Forward Avg Latency (ns)] = [0]
            [Store-Forward Min Latency (ns)] = [0]
            [Store-Forward Max Latency (ns)] = [0]
            [First TimeStamp] = [00:00:00.327]
            [Last TimeStamp] = [00:00:00.445]

        '''
        methodLocalName = self.__lc_current_method_name()
        self.__lc_msg("[{}]Statistic Traffic Item 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Traffic Item Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if trafficName  not in statisticRow and trafficName != "TEST":
                continue
            else:
                self.__lc_msg("Found Traffic Item statistics for [{}] ".format(trafficName))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew


    def get_global_protocol_statistic(self, vPortId):
        '''
           Return True/False for Success/Fail cases
           In case of success the port CPU statistic dictionary is returned.
           To access to the single key-values pair, use the following
           keys on the returned dictonary (sample value are provided as an example):

            [< key >  ]   [< value as example >]

            [Stat Name] = [135.221.113.142/Card02/Port02]
            [Port Name] = [Ethernet - 001]
            [Control Packet Tx.] = [0]
            [Control Packet Rx.] = [0]
            [Ping Reply Tx.] = [0]
            [Ping Request Tx.] = [0]
            [Ping Reply Rx.] = [0]
            [Ping Request Rx.] = [0]
            [Arp Reply Tx.] = [0]
            [Arp Request Tx.] = [0]
            [Arp Request Rx.] = [0]
            [Arp Reply Rx.] = [0]
            [Neighbor Solicitation Tx.] = [0]
            [Neighbor Advertisement Tx.] = [0]
            [Neighbor Solicitation Rx.] = [0]
            [Neighbor Advertisement Rx.] = [0]

        '''
        methodLocalName = self.__lc_current_method_name()
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)
        self.__lc_msg("[{}]Statistic Global Protocol 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Global Protocol Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve  not in statisticRow:
                continue
            else:
                self.__lc_msg("Found Global Protocol statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew



    def get_l2l3_test_summary_statistic(self,  vPortId):
        '''
           Return True/False for Success/Fail cases
           In case of success the port CPU statistic dictionary is returned.
           To access to the single key-values pair, use the following
           keys on the returned dictonary (sample value are provided as an example):

            [< key >  ]   [< value as example >]

            [Stat Name] = [135.221.113.142/Card02/Port02]
            [Port Name] = [Ethernet - 001]
            [Control Packet Tx.] = [0]
            [Control Packet Rx.] = [0]
            [Ping Reply Tx.] = [0]
            [Ping Request Tx.] = [0]
            [Ping Reply Rx.] = [0]
            [Ping Request Rx.] = [0]
            [Arp Reply Tx.] = [0]
            [Arp Request Tx.] = [0]
            [Arp Request Rx.] = [0]
            [Arp Reply Rx.] = [0]
            [Neighbor Solicitation Tx.] = [0]
            [Neighbor Advertisement Tx.] = [0]
            [Neighbor Solicitation Rx.] = [0]
            [Neighbor Advertisement Rx.] = [0]

        '''
        methodLocalName = self.__lc_current_method_name()
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)

        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)
        self.__lc_msg("[{}]Statistic L2-L3 Test Summary 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Global Protocol Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve  not in statisticRow:
                continue
            else:
                self.__lc_msg("Found L2-L3 Test Summary statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew



    def get_data_plane_port_statistic(self, portName):
        '''
           Return True/False for Success/Fail cases
           In case of success the port CPU statistic dictionary is returned.
           To access to the single key-values pair, use the following
           keys on the returned dictonary (sample value are provided as an example):

            [< key >  ]   [< value as example >]

           NDLore: esempi di valori restituiti, concordare eventualmente con
           Valeria Sanvito cosa occorre ricavare da questo metodo.

            [Port] = [Ethernet - 001]
            [Tx Frames] = [10000]
            [Rx Frames] = []
            [Tx Frame Rate] = [0]
            [Rx Frame Rate] = []
            [Tx L1 Load %] = [0]
            [Rx L1 Load %] = []
            [Tx L1 Rate (bps)] = [0]
            [Rx L1 Rate (bps)] = []
            [Rx Bytes] = []
            [Tx Rate (Bps)] = [0]
            [Rx Rate (Bps)] = []
            [Tx Rate (bps)] = [0]
            [Rx Rate (bps)] = []
            [Tx Rate (Kbps)] = [0]
            [Rx Rate (Kbps)] = []
            [Tx Rate (Mbps)] = [0]
            [Rx Rate (Mbps)] = []
            [Store-Forward Avg Latency (ns)] = []
            [Store-Forward Min Latency (ns)] = []
            [Store-Forward Max Latency (ns)] = []
            [First TimeStamp] = [00:00:00.000]
            [Last TimeStamp] = [00:00:00.000]


        '''
        methodLocalName = self.__lc_current_method_name()
        StatisticToRetrieve = portName
        self.__lc_msg("[{}]Statistic Data Plane Port 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Data Plane Port Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        # self.__lc_msg("[{}] ".format(statsColsName) )
        # self.__lc_msg("[{}] ".format(statsRows) )
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            #self.__lc_msg("[{}] [{}]".format(statisticRow,type(statisticRow)))
            #for linea01 in statisticRow:
            #    self.__lc_msg("[{}] [{}]".format(linea01,type(linea01)))
            if StatisticToRetrieve  not in statisticRow:
                continue
            else:
                self.__lc_msg("Found Data Plane Port statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew



    def get_user_defined_statistic(self, portName):
        '''
           * * *  Si Blocca: nessuna definizione di statistiche user...?  * * *
        '''
        methodLocalName = self.__lc_current_method_name()

        StatisticToRetrieve = portName
        self.__lc_msg("[{}]Statistic Data Plane Port 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','User Defined Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        self.__lc_msg("portStats_1[{}] ".format(portStats_1) )
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        self.__lc_msg("[{}] ".format(statsColsName) )
        self.__lc_msg("[{}] ".format(statsRows) )
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            ##self.__lc_msg("[{}] [{}]".format(statisticRow,type(statisticRow)))
            ##for linea01 in statisticRow:
            ##    self.__lc_msg("[{}] [{}]".format(linea01,type(linea01)))

            #if StatisticToRetrieve  not in statisticRow:
                #continue
            #else:
                #self.__lc_msg("Found Data Plane Port statistics for [{}] ".format(StatisticToRetrieve))
                #for paramName, paramValue in zip(statsColsName,statisticRow):
                    #self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
        for paramName, paramValue in zip(statsColsName,statisticRow):
            self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
        retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew



    def get_flow_detective_statistic(self,  vPortId):
        '''

           * * *  Si Blocca: in attesa di traffico???  * * *

        '''
        methodLocalName = self.__lc_current_method_name()
        ipChassis,cardSlot,portNumber = vPortId
        localMessage = "[{}]  ipChassis [{}]  cardSlot[{}]  portNumber[{}]".format(methodLocalName, ipChassis,cardSlot,portNumber)
        self.__lc_msg(localMessage)
        
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber)

        self.__lc_msg("[{}]Statistic Flow Detective 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Flow Detective')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')

        for statisticRow in statsRows:
            statisticRow=statisticRow[0]

            if StatisticToRetrieve  not in statisticRow:
                continue
            else:
                self.__lc_msg("Found Flow Detective statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))

            for paramName, paramValue in zip(statsColsName,statisticRow):
                self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew



    def get_txrx_frame_rate_statistic(self, trafficName):
        '''
           * * *  Si Blocca: in attesa di traffico???  * * *
        '''
        methodLocalName = self.__lc_current_method_name()
        self.__lc_msg("[{}]Statistic Tx-Rx Frame Rate 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Tx-Rx Frame Rate Statistics')[0]
        except Exception as excMsg:
            self.__lc_msg("Exception[{}]  ".format(excMsg))
            return  False,retDictionaryNew
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        self.__lc_msg("[{}]  ".format(   statsColsName))
        self.__lc_msg("[{}]  ".format(   statsRows))


        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            #if trafficName  not in statisticRow:
                #continue
            #else:
                #self.__lc_msg("Found Tx-Rx Frame Rate  statistics for [{}] ".format(trafficName))
            for paramName, paramValue in zip(statsColsName,statisticRow):
                self.__lc_msg("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew


 










    #==================================================================
    # Krepo-related  code
    #==================================================================

    def __get_instrument_info_from_db(self, ID):
        tabEqpt  = TEquipment
        # get Equipment Type ID for selected ID (i.e. 50 (for ONT506))
        #instr_type_id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.id_type
        # get Equipment Type Name for selected ID (i.e. ONT506)
        instr_type_name = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name
        instr_ip = self.__get_net_info(ID)
        self.__chassisIpAddress  = instr_ip
        localMessage = "__get_instrument_info_from_db: instrument type specified : Instrument:[{}] IpAddr[{}]".format(instr_type_name,instr_ip)
        self.__trc_err(localMessage)
        return

    def __trc_dbg(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_debug(msg, level=1)


    def __trc_inf(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_info(msg, level=1)


    def __trc_err(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_error(msg, level=1)


    def __t_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_success(self, title, elapsed_time, out_text)



    def __t_failure(self, title, e_time, out_text, err_text, log_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_failure(self, title, e_time, out_text, err_text, log_text)



    def __t_skipped(self, title, e_time, out_text, err_text, skip_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_skipped(self, title, e_time, out_text, err_text, skip_text)



    def __method_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        #self.__t_success(methodLocalName, None, localMessage)
        self.__lastCallSuccess = True            # Mark current execution as successfully
        self.__calledMethodStatus[title]= "success"  #
        self.__t_success(title, elapsed_time, out_text)  # CG tracking


    def __method_failure(self, title, e_time, out_text, err_text):
        """ INTERNAL USAGE
        """
        #self.__t_failure(methodLocalName, None, "", localMessage)
        self.__lastCallSuccess = False            # Mark current execution as successfully
        self.__calledMethodStatus[title]= "error"  #
        self.__t_failure(title, e_time, out_text, err_text) # CG tracking



    def __method_skipped(self, title, e_time, out_text, err_text):
        """ INTERNAL USAGE
        """
        #self.__t_failure(methodLocalName, None, "", localMessage)
        #self.__lastCallSuccess = False            # Don't mark current execution as successfully
        self.__calledMethodStatus[title]= "skip"  #
        self.__t_skipped(title, e_time, out_text, err_text) # CG tracking


    #
    #  K@TE INTERFACE
    #
    def __get_net_info(self, n):
        tabNet = TNet

        for r in tabNet.objects.all():
            if r.t_equipment_id_equipment:
                if r.t_equipment_id_equipment.id_equipment == n:
                    return r.ip
        return str(None)


    def __lc_msg(self,messageForDebugPurposes):
        # Print debug messages: verbose mode in test only
        #if __name__ == "__main__":
        #    self.__lc_msg ("{:s}".format(messageForDebugPurposes))
        #else:
        #   insert HERE the new logging method (still in progress...)
        print("{:s}".format(messageForDebugPurposes))


#######################################################################
#
#   MODULE TEST - Test sequences used for DB-Integrated testing
#
#######################################################################
if __name__ == "__main__":   #now use this part
    '''
    self.__lc_msg(" ")
    self.__lc_msg("========================================")
    self.__lc_msg("ixiaDriver DB-Integrated testing debug")
    self.__lc_msg("========================================")

    # DA AMBIENTE DI ESECUZIONE:
    currDir,fileName = os.path.split(os.path.realpath(__file__))
    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    self.__lc_msg("{}".format(xmlReport))
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)



    self.__lc_msg("\n\n\n\n\nTESTING SECTION *************************************")
    self.__lc_msg("\n\n*** instrumentIXIA.py testing not implemented here ***")
    self.__lc_msg("\n\n    execute /users/testkate/MYGITREPO/TESTFRAME/FRAMEWORK/examples/TestIXIA.py instead!!! ")
    self.__lc_msg("\n\n")
    input("press enter to continue...")



    self.__lc_msg(" ")
    self.__lc_msg("========================================")
    self.__lc_msg("ixiaDriver DB-Integrated -- END --    ")
    self.__lc_msg("========================================")
    self.__lc_msg(" ")


    r.frame_close()
    '''
    self.__lc_msg("DONE")
    #sys.exit()

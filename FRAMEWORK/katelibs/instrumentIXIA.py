#!/usr/bin/env python
"""
###############################################################################
#
# MODULE:  instrumentIXIA.py
#
# AUTHOR:  L.Cutilli
#
# DATE  :  18/02/2016
#
#
# DETAILS: Python management module for IXIA test equipments
#
# MODULE: instrumentIXIA.py
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
from katelibs.kenviron import KEnvironment
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
        self.__ixNetworkServerAddress      = "135.221.116.175"  # ixnetwork server address v8.01       
        self.__ixNetworkServerPort         = 8009             # ixnetwork server port
        self.__ixNetworkServerVersion      = '8.00'             # ixnetwork server port
        #Data model (DM) main hooks
        self.__remapIds  = True
        self.__IXN  = None
        self.__ROOT = None                       
        self.__calledMethodStatus = dict()           #  used to track all method called and last execution result
        self.__vPortList          = dict()
        self.__globalTrafficItem  = None 
        
        ## !!! Don't delete the following lines !!!
        super().__init__(label, self.__prs.get_id(label))
        self.__get_instrument_info_from_db(self.__prs.get_id(label)) # inizializza i dati di IP, tipo di Strumento ecc... dal DB


    #
    #   USEFUL FUNC & TOOLS
    #
    def __ret_func(self, TFRetcode=True, MsgLevel="none", localMessage="Put here the string to print"  ):       ### krepo noy added ###
        methodLocalName = self.__lc_caller_method_name()      
        if MsgLevel == "error":self.__trc_err(localMessage) 
        elif MsgLevel == "none":pass  
        else:self.__trc_inf(localMessage) 
        if TFRetcode == True:self.__method_success(methodLocalName, None, localMessage)
        else:self.__method_failure(methodLocalName, None, "", localMessage)
        return TFRetcode, localMessage


    def __lc_current_method_name(self, embedKrepoInit=False):
        methodName = inspect.stack()[1][3]   # <-- daddy method name  : who calls __lc_current_method_name
        print ("\n[{}] method Call ... Krepo[{}]".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:self.__krepo.start_time()
        return methodName 


    def __lc_caller_method_name(self, embedKrepoInit=False):
        methodName = inspect.stack()[2][3]   # <-- two levels of call
        print ("\n[{}] method caller ... Krepo[{}]".format(methodName,embedKrepoInit))
        if self.__krepo and embedKrepoInit == True:self.__krepo.start_time()
        return methodName 


    #
    #   BRIDGE CONNECTION MANAGEMENT
    #
    def connect_ixnetwork(self):       ### krepo added ###
        """ connect_ixnetwork(self) - Hint: first call to use
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
            answerBridge = self.__IXN.connect(self.__ixNetworkServerAddress,'-port', self.__ixNetworkServerPort,'-version', self.__ixNetworkServerVersion)  
        except: 
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connection failed: check ixNetwork server {}] port [{}]".format(self.__ixNetworkServerAddress,self.__ixNetworkServerPort))
        if answerBridge != "::ixNet::OK":
            self.__IXN = None
            return self.__ret_func(False,"error", "Bridge connect() answer not expected:[{}] instead of [::ixNet::OK]".format(answerBridge))
        result1 = self.__IXN.execute('newConfig')
        self.__ROOT              = self.__IXN.getRoot()     
        self.__DM_NULL           = self.__IXN.getNull()    
        return self.__ret_func(True,"success", "[{}] [{}] - self.__ROOT now [{}]".format(methodLocalName,answerBridge,self.__ROOT) )



    def add_single_vport(self, vPortId, mediaType="fiber"):       ### krepo added ###
        methodLocalName = self.__lc_current_method_name()
        localVport   = self.__IXN.add(self.__ROOT, 'vport')
        self.__IXN.commit()
        if self.__remapIds:
            localVport = self.__IXN.remapIds(localVport)[0]
        if mediaType == "fiber":
            self.__IXN.setAttribute(localVport + '/l1Config/ethernet','-media','fiber')
        self.__vPortList[vPortId] = localVport
        #return self.__ret_func(True,"success", "[{}] Added vPort [{}]".format(methodLocalName,vPortId) )
        return  True, "[{}] Added vPort [{}]".format(methodLocalName,vPortId) 



    def create_all_vports(self, vportlist, vportsMediaType="fiber"):       ### krepo added ###
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        for localVportId in vportlist:
            print("Vport [{}] creation ".format(localVportId))
            retcode = self.add_single_vport(localVportId, mediaType=vportsMediaType)    
            print("Vport [{}] creation ".format(retcode))
            
        return self.__ret_func(True,"success", "[{}] Added vPorts [{}]".format(methodLocalName,vportlist))



    def bind_all_phy_ports_to_vports(self, vportlist, vportsMediaType="fiber"):       ### krepo added ###
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        localVportList = []
        for localVportId in vportlist:
            localVportList.append(self.__vPortList[localVportId])   
            print("localVportList [{}]".format(localVportList)) 
        assignPorts = self.__IXN.execute('assignPorts', vportlist, [], localVportList, True)
        print("assignPorts [{}]".format(assignPorts))   
        return self.__ret_func(True,"success", "[{}] Added vPorts [{}]".format(methodLocalName,vportlist))



    def create_traffic(self, 
                       vPortIdTx, 
                       vPortIdRx,
                       trafficName            = 'Traffic RAW',
                       trafficType            = 'raw',
                       allowSelfDestined      = False,
                       trafficItemType        = 'l2L3',
                       mergeDestinations      = True,
                       egressEnabled          = False,
                       srcDestMesh            = 'oneToOne',
                       enabled                = True,
                       routeMesh              = 'oneToOne',
                       transmitMode           = 'interleaved',
                       biDirectional          = True,
                       hostsPerNetwork        = 1,
                       endPointName           = 'ep-set1',
                       endPointSourceFilter   = '',
                       endPointDestFilter     = '',
                       frameSizeType          = 'fixed',
                       frameSizeFixedSize     = 128,
                       frameRateType          = 'percentLineRate',
                       frameRateRate          = 10, 
                       TCduration             = 1,
                       TCiterationCount       = 1,
                       TCstartDelayUnits      = 'bytes',
                       TCminGapBytes          = 12,
                       TCframeCount           = 10000,
                       TCtype                 = 'fixedFrameCount',
                       TCinterBurstGapUnits   = 'nanoseconds',
                       TCinterBurstGap        = 0,
                       TCenableInterBurstGap  = False,
                       TCinterStreamGap       = 0,
                       TCrepeatBurst          = 1,
                       TCenableInterStreamGap = False,
                       TCstartDelay           = 0,
                       TCburstPacketCount     = 1,
                       TrackBy                = ['sourceDestValuePair0'],
                       VLanId                 = 0,
                       VLanCFI                = 0,
                       VLanPriority           = 0,
                       VLanSrcMacAddr         = "00:00:00:00:00:00",
                       VLanDestMacAddr        = "00:00:00:00:00:00"
                       ):

        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        try:
            localTxPort = self.__vPortList[vPortIdTx]+'/protocols'
            localRxPort = self.__vPortList[vPortIdRx]+'/protocols'
            self.__globalTrafficItem = self.__IXN.add(self.__ROOT + '/traffic', 'trafficItem')
            self.__IXN.commit()
            if self.__remapIds:
                self.__globalTrafficItem = self.__IXN.remapIds(self.__globalTrafficItem)[0]
                
            self.__IXN.setMultiAttribute(self.__globalTrafficItem,
                                             '-name'              ,trafficName,
                                             '-trafficType'       ,trafficType,
                                             '-allowSelfDestined' ,allowSelfDestined,
                                             '-trafficItemType'   ,trafficItemType,
                                             '-mergeDestinations' ,mergeDestinations,
                                             '-egressEnabled'     ,egressEnabled,
                                             '-srcDestMesh'       ,srcDestMesh,
                                             '-enabled'           ,enabled,
                                             '-routeMesh'         ,routeMesh,
                                             '-transmitMode'      ,transmitMode,
                                             '-biDirectional'     ,biDirectional,
                                             '-hostsPerNetwork'   ,hostsPerNetwork)
            self.__IXN.commit()
            self.__IXN.add(self.__globalTrafficItem       ,'endpointSet',
                           '-sources'             ,localTxPort,
                           '-destinations'        ,localRxPort,
                           '-name'                ,endPointName,
                           '-sourceFilter'        ,endPointSourceFilter,
                           '-destinationFilter'   ,endPointDestFilter)
            self.__IXN.commit()
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + "/configElement:1/frameSize",
                                         '-type'        ,frameSizeType,
                                         '-fixedSize'   ,frameSizeFixedSize)
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + "/configElement:1/frameRate",
                                         '-type'        ,frameRateType,
                                         '-rate'        ,frameRateRate)
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + "/configElement:1/transmissionControl",
                                         '-duration'               ,TCduration,
                                         '-iterationCount'         ,TCiterationCount,
                                         '-startDelayUnits'        ,TCstartDelayUnits,
                                         '-minGapBytes'            ,TCminGapBytes,
                                         '-frameCount'             ,TCframeCount,
                                         '-type'                   ,TCtype,
                                         '-interBurstGapUnits'     ,TCinterBurstGapUnits,
                                         '-interBurstGap'          ,TCinterBurstGap,
                                         '-enableInterBurstGap'    ,TCenableInterBurstGap,
                                         '-interStreamGap'         ,TCinterStreamGap,
                                         '-repeatBurst'            ,TCrepeatBurst,
                                         '-enableInterStreamGap'   ,TCenableInterStreamGap,
                                         '-startDelay'             ,TCstartDelay,
                                         '-burstPacketCount'       ,TCburstPacketCount)
            self.__IXN.setMultiAttribute(self.__globalTrafficItem + "/tracking", '-trackBy', TrackBy)
            self.__IXN.commit()
        except Exception as excMsg:
            self.__IXN = None
            return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))

        
        if VLanId != 0: 
            try:
                print("VLAN CREATION SECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " )
                print("VLAN CREATION SECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " )
                print("VLAN CREATION SECTION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> " )
                
                
                ### Adding a custom VLAN header on top of Ethernet ###
                # First of all, we need to get the configElement handle and add the stack on top of that #
                
                ti1ConfEl = self.__IXN.getList(self.__globalTrafficItem, "configElement")[0]
                print("ti1ConfEl [{}]".format(ti1ConfEl))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                
                # get the Ethernet handle pointer. We will add the vlan header on top of that
                ethernetStack = self.__IXN.getList(ti1ConfEl, "stack")[0]
                print("ethernetStack [{}]".format(ethernetStack))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )                
                # get the VLAN template handle pointer, that we can add on top of Ethernet
                protocolTemplateList = self.__IXN.getList(self.__ROOT + '/traffic', 'protocolTemplate')
                #print("protocolTemplateList [{}]".format(protocolTemplateList))
                print("protocolTemplateList  " )
                for temp in protocolTemplateList:
                    print("[{}]".format(temp))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                protocolTemplateVLAN = [s for s in protocolTemplateList if "vlan" in s][0]
                print("protocolTemplateVLAN [{}]".format(protocolTemplateVLAN))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                self.__IXN.execute('append', ethernetStack, protocolTemplateVLAN)
                
                # now the VLAN header has been appended, we need to modify its VLAN field
                # we need to get the VLAN handle which we added inside the traffic item
                trafficStackList = self.__IXN.getList(ti1ConfEl, "stack")
                print("trafficStackList ")
                for temp in trafficStackList:
                    print("[{}]".format(temp))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                vlanStack = [s for s in trafficStackList if "vlan" in s][0]
                print("vlanStack [{}]".format(vlanStack))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                fieldList = self.__IXN.getList(vlanStack,"field")
                #print("fieldList [{}]".format(fieldList))
                print("fieldList")
                for temp in fieldList:
                    print("[{}]".format(temp))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                vlanIDField = [s for s in fieldList if "vlanID" in s][0]
                print("vlanIDField [{}]".format(vlanIDField))
                self.__IXN.setAttribute(vlanIDField, '-singleValue', VLanId)

                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                vlanPiorityField = [s for s in fieldList if "vlanUserPriority" in s][0]
                print("vlanPiorityField [{}]".format(vlanPiorityField))
                self.__IXN.setAttribute(vlanPiorityField, '-singleValue', VLanPriority)

                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                vlanCfiField = [s for s in fieldList if "cfi" in s][0]
                print("vlanCfiField [{}]".format(vlanCfiField))
                self.__IXN.setAttribute(vlanCfiField, '-singleValue', VLanCFI)
                print("=============   ===================   =============   ==============   =========" )
                print("=============   ===================   =============   ==============   =========" )
                print("=============   ===================   =============   ==============   =========" )


                ethStack = [s for s in trafficStackList if "ethernet" in s][0]
                print("ethStack [{}]".format(ethStack))
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )

                ethFieldList = self.__IXN.getList(ethStack,"field")
                print("ethFieldList")
                for temp in ethFieldList:
                    print("[{}]".format(temp))
                    
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                srcMacField = [s for s in ethFieldList if "sourceAddress" in s][0]
                print("srcMacField [{}]".format(srcMacField))
                self.__IXN.setAttribute(srcMacField, '-singleValue', VLanSrcMacAddr)
                    
                    
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" )
                destMacField = [s for s in ethFieldList if "destinationAddress" in s][0]
                print("destMacField [{}]".format(destMacField))
                self.__IXN.setAttribute(destMacField, '-singleValue', VLanDestMacAddr)
                    
                    




                self.__IXN.commit()
            
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<VLAN CREATION SECTION " )
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<VLAN CREATION SECTION " )
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<VLAN CREATION SECTION " )
            except Exception as excMsg:
                self.__IXN = None
                return self.__ret_func(False,"error", "[{}] exception [{}]".format(methodLocalName,excMsg))
        else:
            print("VLan Creation SKIPPED [{}]")
        
        
        return self.__ret_func(True,"success", "[{}] Created Traffic [{}]-->[{}]".format(methodLocalName,vPortIdTx,vPortIdRx) )



    def start_all_protocols(self,timeToWait=20):
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        print("[{}] Start protocols and wait for {}sec".format(methodLocalName, timeToWait))        
        self.__IXN.execute('startAllProtocols')
        time.sleep(timeToWait)
        print("[{}] Protocols now started".format( timeToWait))
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )
 


    def start_traffic(self,timeToWait=20):
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        print("[{}] Start traffic and wait for {}sec".format(methodLocalName, timeToWait))        
        self.__IXN.execute('generate', self.__globalTrafficItem)
        self.__IXN.execute('apply', self.__ROOT + '/traffic')
        self.__IXN.execute('start', self.__ROOT + '/traffic')
        print("[{}] Traffic now started".format(methodLocalName))             
        time.sleep(timeToWait)
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )



    def stop_traffic(self,timeToStop=0):
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        #print("Stop all traffic ")        
        print("[{}] Traffic will be stopped in {}sec".format(methodLocalName,timeToStop))
        time.sleep(timeToStop)
        #self.__IXN.execute('generate', self.__globalTrafficItem)
        #self.__IXN.execute('apply', self.__ROOT + '/traffic')
        self.__IXN.execute('stop', self.__ROOT + '/traffic')
        print("[{}] Traffic now stopped".format(methodLocalName))       
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )
 
 
 
 
 


    def check_traffic(self):
        methodLocalName = self.__lc_current_method_name(embedKrepoInit=True)
        views = self.__IXN.getList('/statistics', 'view')
        for listItem in views:
            print ("Statistic entry   [{}]  ".format(listItem))
        portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port Statistics')[0]
        print ("portStats_1 [{}]  ".format(portStats_1))
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        print ("[{}]  ".format(statsColsName))
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            for paramName, paramValue in zip(statsColsName,statisticRow)  :
                print("[{}] = [{}] ".format(paramName, paramValue))
        return self.__ret_func(True,"success", "[{}] Success".format(methodLocalName) )

 


    def get_port_statistic(self, ipChassis, cardSlot, portNumber):
        '''
           Return True/False for Success/Fail cases
           In case of success the port traffic dictionary is returned.
           To access to the single key-values pair, use the following 
           keys on the returned dictonary (sample value are provided as an example):
            
            [< key >  ]   [< value as example >]
            
            [Stat Name] = [135.221.113.142/Card02/Port03] 
            [Port Name] = [Ethernet - 002] 
            [Duplex Mode] = [Full] 
            [Line Speed] = [1000 Mbps] 
            [Link State] = [Link Up] 
            [Frames Tx.] = [0] 
            [Valid Frames Rx.] = [10000] 
            [Frames Tx. Rate] = [0] 
            [Valid Frames Rx. Rate] = [0] 
            [Data Integrity Frames Rx.] = [10000] 
            [Data Integrity Errors] = [0] 
            [Bytes Tx.] = [0] 
            [Bytes Rx.] = [1280000] 
            [Bits Sent] = [0] 
            [Bits Received] = [10240000] 
            [Bytes Tx. Rate] = [0] 
            [Tx. Rate (bps)] = [0] 
            [Tx. Rate (Kbps)] = [0] 
            [Tx. Rate (Mbps)] = [0] 
            [Bytes Rx. Rate] = [0] 
            [Rx. Rate (bps)] = [0] 
            [Rx. Rate (Kbps)] = [0] 
            [Rx. Rate (Mbps)] = [0] 
            [Scheduled Frames Tx.] = [0] 
            [Scheduled Frames Tx. Rate] = [0] 
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
        '''
        #  def ret_port_traffic(self, portNumber, **retValue):
        methodLocalName = self.__lc_current_method_name()
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber) 
        print("Statistic 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port Statistics')[0]
        except Exception as excMsg:
            retDictionary=dict()
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if StatisticToRetrieve not in statisticRow: 
                continue
            print("Found statistics for [{}] ".format(StatisticToRetrieve))
            for paramName, paramValue in zip(statsColsName,statisticRow):
                print("[{}] = [{}] ".format(paramName, paramValue))
            retDictionary=dict(zip(statsColsName,statisticRow) )
        return  True,retDictionary



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
        print("[{}]Statistic Flow 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Flow Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if trafficName  not in statisticRow: 
                continue
            else:
                print("Found Flow statistics for [{}] ".format(trafficName))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
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
        print("[{}]Statistic Traffic Item 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Traffic Item Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            if trafficName  not in statisticRow: 
                continue
            else:
                print("Found Traffic Item statistics for [{}] ".format(trafficName))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew




    def get_port_cpu_statistic(self,  ipChassis, cardSlot, portNumber):
        '''
           Return True/False for Success/Fail cases
           In case of success the port CPU statistic dictionary is returned.
           To access to the single key-values pair, use the following 
           keys on the returned dictonary (sample value are provided as an example):
            
            [< key >  ]   [< value as example >]
            
            [Stat Name] = [135.221.113.142/Card02/Port02] 
            [Port Name] = [Ethernet - 001] 
            [Total Memory(KB)] = [255016] 
            [Free Memory(KB)] = [159600] 
            [% Disk Utilization] = [46] 
            [CPU Load Avg (1 Minute)] = [0] 
            [CPU Load Avg (5 Minutes)] = [0] 
            [CPU Load Avg (15 Minutes)] = [0] 
            [%CPU Load] = [0] 
        '''
        methodLocalName = self.__lc_current_method_name()
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber) 

        print("[{}]Statistic Port CPU 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Port CPU Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            
            if StatisticToRetrieve  not in statisticRow: 
                continue
            else:
                print("Found  Port CPU statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew
 

    def get_global_protocol_statistic(self,  ipChassis, cardSlot, portNumber):
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
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber) 

        print("[{}]Statistic Global Protocol 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Global Protocol Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            
            if StatisticToRetrieve  not in statisticRow: 
                continue
            else:
                print("Found Global Protocol statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #print("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew
 
 

    def get_l2l3_test_summary_statistic(self,  ipChassis, cardSlot, portNumber):
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
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber) 

        print("[{}]Statistic L2-L3 Test Summary 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Global Protocol Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            
            if StatisticToRetrieve  not in statisticRow: 
                continue
            else:
                print("Found L2-L3 Test Summary statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #print("[{}] = [{}] ".format(paramName, paramValue))
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

        print("[{}]Statistic Data Plane Port 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Data Plane Port Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        # print("[{}] ".format(statsColsName) )
        # print("[{}] ".format(statsRows) )
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            #print("[{}] [{}]".format(statisticRow,type(statisticRow)))
            #for linea01 in statisticRow:
            #    print("[{}] [{}]".format(linea01,type(linea01)))
                
            if StatisticToRetrieve  not in statisticRow: 
                continue
            else:
                print("Found Data Plane Port statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            
            #for paramName, paramValue in zip(statsColsName,statisticRow):
                #print("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew
   



    def get_user_defined_statistic(self, portName):
        '''

           * * *  Si Blocca: nessuna definizione di statistiche user...?  * * *
            
        '''
        methodLocalName = self.__lc_current_method_name()
        
        StatisticToRetrieve = portName

        print("[{}]Statistic Data Plane Port 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','User Defined Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        print("portStats_1[{}] ".format(portStats_1) )
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        print("[{}] ".format(statsColsName) )
        print("[{}] ".format(statsRows) )
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            ##print("[{}] [{}]".format(statisticRow,type(statisticRow)))
            ##for linea01 in statisticRow:
            ##    print("[{}] [{}]".format(linea01,type(linea01)))
                
            #if StatisticToRetrieve  not in statisticRow: 
                #continue
            #else:
                #print("Found Data Plane Port statistics for [{}] ".format(StatisticToRetrieve))
                #for paramName, paramValue in zip(statsColsName,statisticRow):
                    #print("[{}] = [{}] ".format(paramName, paramValue))
            
        for paramName, paramValue in zip(statsColsName,statisticRow):
                print("[{}] = [{}] ".format(paramName, paramValue))
        retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew
   
 

    def get_flow_detective_statistic(self,  ipChassis, cardSlot, portNumber):
        '''

           * * *  Si Blocca: in attesa di traffico???  * * *
            
        '''
        methodLocalName = self.__lc_current_method_name()
        cardSlot   = "{:02.0f}".format(cardSlot)
        portNumber = "{:02.0f}".format(portNumber)
        StatisticToRetrieve = "{}/Card{}/Port{}".format(ipChassis,cardSlot,portNumber) 

        print("[{}]Statistic Flow Detective 2 Retrieve [{}]".format(methodLocalName,StatisticToRetrieve))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Flow Detective')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
 
        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            
            if StatisticToRetrieve  not in statisticRow: 
                continue
            else:
                print("Found Flow Detective statistics for [{}] ".format(StatisticToRetrieve))
                for paramName, paramValue in zip(statsColsName,statisticRow):
                    print("[{}] = [{}] ".format(paramName, paramValue))
            
            for paramName, paramValue in zip(statsColsName,statisticRow):
                print("[{}] = [{}] ".format(paramName, paramValue))
            retDictionaryNew=dict(zip(statsColsName,statisticRow) )
        return  True, retDictionaryNew
 
 
 
    def get_txrx_frame_rate_statistic(self, trafficName):
        '''
           * * *  Si Blocca: in attesa di traffico???  * * *
        '''
        methodLocalName = self.__lc_current_method_name()
        print("[{}]Statistic Tx-Rx Frame Rate 2 Retrieve [{}]".format(methodLocalName,trafficName))
        retDictionaryNew=dict()
        try:
            portStats_1 = self.__IXN.getFilteredList(self.__ROOT+'statistics', 'view', '-caption','Tx-Rx Frame Rate Statistics')[0]
        except Exception as excMsg:
            return  False,retDictionary
        statsColsName = self.__IXN.getAttribute(portStats_1 + '/page','-columnCaptions')
        statsRows = self.__IXN.getAttribute(portStats_1 + '/page','-rowValues')
        print("[{}]  ".format(   statsColsName))
        print("[{}]  ".format(   statsRows))
      

        for statisticRow in statsRows:
            statisticRow=statisticRow[0]
            #if trafficName  not in statisticRow: 
                #continue
            #else:
                #print("Found Tx-Rx Frame Rate  statistics for [{}] ".format(trafficName))
            for paramName, paramValue in zip(statsColsName,statisticRow):
                print("[{}] = [{}] ".format(paramName, paramValue))
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
        #    print ("{:s}".format(messageForDebugPurposes))
        #else:
        #   insert HERE the new logging method (still in progress...)   
        print ("{:s}".format(messageForDebugPurposes))


#######################################################################
#
#   MODULE TEST - Test sequences used for DB-Integrated testing
#
#######################################################################
if __name__ == "__main__":   #now use this part
    print(" ")
    print("========================================")
    print("ixiaDriver DB-Integrated testing debug")
    print("========================================")

    # DA AMBIENTE DI ESECUZIONE:
    currDir,fileName = os.path.split(os.path.realpath(__file__))
    xmlReport = currDir + '/test-reports/TestSuite.'+ fileName
    print("{}".format(xmlReport))
    r = Kunit(xmlReport)
    r.frame_open(xmlReport)



    print("\n\n\n\n\nTESTING SECTION *************************************")
    print("\n\n*** instrumentIXIA.py testing not implemented here ***")
    print("\n\n    execute /users/testkate/MYGITREPO/TESTFRAME/FRAMEWORK/examples/TestIXIA.py instead!!! ")
    print("\n\n")
    input("press enter to continue...")
    


    print(" ")
    print("========================================")
    print("ixiaDriver DB-Integrated -- END --    ")
    print("========================================")
    print(" ")


    r.frame_close()

    
    #sys.exit()











#!/usr/bin/env python
"""
###############################################################################
# MODULE: tl1_facility.py
#
# AUTHOR: C.Ghelfi
# DATE  : 23/11/2015
#
###############################################################################
"""

import re
import time
import os
import sys
import json


class TL1message():
    """ Collection of TL1 facilities
    """

    def __init__(self, tl1_msg):
        """
            Structured representation of generic TL1 Message
            A dictionary with following elements will be generated for a TL1 response message:
            - common for all message types:
                'C_SID'     : the equipment's SID
                'C_DATE'    : timestamp (date)
                'C_TIME'    : timestamp (time)
                'C_CODE'    : 'M' / '*C' / '**' / '*' / 'A'
                'C_TAG'     : the message TAG
            - only for Commands Response:
                'R_STATUS'  : COMPLD / DELAY / DENY / PRTL / RTRV
                'R_BODY_OK' : Body Section(Only for successfull command response)
                              list of 1 or more items - Dictionary:
                                 aid : AID of element (key for dictionary)
                                     'VALUES' : sequence ATTR=Value
                                     'STATE'  : Primary and Secondary state
                'R_BODY_KO' : Body Section (Only for failure command response)
                               list of two string response specification
            - only for Spontaneous Messages:
                'S_VMM'     : Verb and modifiers
                'S_BODY'    : dictionary
        """

        self.__m_plain = tl1_msg    # Plain ascii TL1 Message Response
        self.__m_coded = {}         # Coded Tl1 Message Response (dictionary)
        self.__m_event = None       # True is the message is a Spontaneous Message

        if tl1_msg is not None  and  tl1_msg != "":
            self.encode()


    def encode(self):
        """ Decompose an ASCII TL1 Message response to structured format
        """
        self.__m_event = False
        self.__m_coded = {}

        f_header = True
        f_ident  = True
        f_block  = True

        for line in self.__m_plain.split('\n'):
            if f_header:
                if line.strip() == "":
                    continue

                self.__m_coded['C_SID']  = " ".join(line.split()[:-2]).replace('"', '')
                self.__m_coded['C_DATE'] = line.split()[-2]
                self.__m_coded['C_TIME'] = line.split()[-1]
                f_header = False
                continue

            if f_ident:
                words = line.split()
                self.__m_event = ( words[0] == '*C' or
                                   words[0] == '**' or
                                   words[0] == '*'  or
                                   words[0] == 'A'  )

                self.__m_coded['C_CODE'] = words[0]
                self.__m_coded['C_TAG']  = words[1]

                if self.__m_event:
                    self.__m_coded['S_VMM'] = words[2:]
                else:
                    self.__m_coded['R_STATUS']  = words[2]
                    self.__m_coded['R_BODY_OK'] = {}
                    self.__m_coded['R_BODY_KO'] = []
                    self.__m_coded['R_ERROR']   = ""

                f_ident = False
                continue

            if f_block:
                if self.__m_event:
                    # Event Response
                    words = line.strip().replace('"', '').split(':')
                    self.__m_coded['EVE_AID']  = words[0]
                    self.__m_coded['EVE_TEXT'] = words[1]
                    f_block = False
                    continue

                # Command Response
                stripped_line = line.strip()
                if ( stripped_line.find('/*') != -1                                     and
                     stripped_line.find("[{:s}]".format(self.__m_coded['C_TAG'])) != -1 and
                     stripped_line.find('*/') != -1                                     ):
                    # REMARK found - closing capture
                    break
                if self.__m_coded['R_STATUS'] == "COMPLD":
                    words = stripped_line.replace('"', '').split(':')
                    row = {}
                    row[ words[0] ] = {'VALUES' : words[2], 'STATE' : words[3]}
                    self.__m_coded['R_BODY_OK'].update(row)
                elif self.__m_coded['R_STATUS'] == "DENY":
                    if len(stripped_line) == 4:
                        self.__m_coded['R_ERROR'] = stripped_line
                    else:
                        self.__m_coded['R_BODY_KO'].append(stripped_line)
                else:
                    print("[{:s}] NON ANCORA GESTITO".format(self.__m_coded['R_STATUS']))
                continue

            if line == ';':
                # TERMINATOR found - closing capture
                break


    def decode(self, codec="ASCII"):
        """ Format the structured TL1 message to supplied coded
            codec : "ASCII" / "JSON"
        """
        new_msg = ""
        if   codec == "ASCII":
            pass
        elif codec == "JSON":
            new_msg = json.dumps(self.__m_coded, indent=4, sort_keys=True)
        else:
            print("Codec not managed")

        return new_msg


    def get_sid(self):
        """ Return the SID
        """
        return self.__m_coded['C_SID']


    def get_time_stamp(self):
        """ Return a couple of string (date, time) for Message Time Stamp
        """
        return self.__m_coded['C_DATE'], self.__m_coded['C_TIME']


    def get_message_code(self):
        """ Return the TL1 Message code as follow: "M" / "**" / "*C" / "*" / "A"
        """
        return self.__m_coded['C_CODE']


    def get_tag(self):
        """ Return the TL1 Tag
        """
        return self.__m_coded['C_TAG']


    def get_cmd_status(self):
        """ Return a couple (result, code) as follow:
            result := True/False (True for TL1 respone message, False for spontaneous messages)
            code   := "COMPLD" / "DENY" / None     (None for spontaneous messages)
        """
        if self.__m_event:
            return False, None

        return True, self.__m_coded['R_STATUS']


    def get_cmd_aid_list(self):
        """ Return the AID list found on message
            If TL1 Message is a spontaneous message, or the command is failed, a None is returned
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        return list(self.__m_coded['R_BODY_OK'].keys())


    def get_cmd_status_value(self, aid):
        """ Return a couple (pst,sst) for command response
            (None, None) for not completed TL1 Messages
        """
        if self.__m_event:
            return None, None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None, None

        the_elem = self.__m_coded['R_BODY_OK'].get(aid)
        if the_elem is None:
            return None, None

        return the_elem['STATE'].split(',')


    def get_cmd_attr_value(self, aid, attr):
        """ Return the value for specified attribute and AID
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        for  i  in  self.__m_coded['R_BODY_OK'].get(aid)['VALUES'].split(','):
            the_attr, the_value = i.split('=')
            if the_attr == attr:
                return the_value

        return None


    def get_cmd_error_frame(self):
        """ Return a tuple (result, str1, str2) for a DENY response message
            'result' is False if the message isn't a command response
            'str1' and 'str2' contanis the DENY reponse values
        """
        if self.__m_event:
            return False, None, None

        if self.__m_coded['R_STATUS'] != "DENY":
            return False, None, None

        return True, self.__m_coded['R_ERROR'], self.__m_coded['R_BODY_KO']





if __name__ == "__main__":
    print("DEBUG")

    msg1 = "\n\
   PLEASE-SET-SID-C8A00 15-10-04 17:01:56\n\
*  243 REPT ALM EQPT\n\
   \"MDL-1-1-18:MN,ABNORMAL,NSA,10-04,17-01-56,NEND\"\n\
;\n\
"

    msg2 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-04 18:35:10\n\
M  379 COMPLD\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   /* RTRV-EQPT::MDL-1-1-1 [379] (536871116) */\n\
;\n\
"

    msg3 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-04 20:31:15\n\
M  165 COMPLD\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   \"MDL-1-1-18::ACTUALTYPE=PP1GE,AUTOPROV=OFF:OOS-MA,UAS\"\n\
   /* RTRV-EQPT::MDL-1-1-1&-18 [165] (536871116) */\n\
;\n\
"

    msg4 = "\n\
\n\
\n\
   PLEASE-SET-SID-C8A00 15-10-05 17:25:40\n\
M  792 DENY\n\
   IEAE\n\
   /* Input, Entity Already Exists */\n\
   /* Equipment is already Provisioned */\n\
   /* ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS [792] (536871116) */\n\
;\n\
"

    msg5 = "\n\
   \"nodeA - .TDM.EM_TEST.RtrvEqptALL\" 15-10-15 21:47:33\n\
M  963 COMPLD\n\
   \"SHELF-1-1::PROVISIONEDTYPE=UNVRSL320,ACTUALTYPE=UNVRSL320,AINSMODE=NOWAIT,SHELFNUM=1,SHELFROLE=MAIN,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   \"EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT\"\n\
   \"MDL-1-1-2::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-3::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-4::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-5::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-6::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-7::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-8::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-9::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MT320-1-1-10::PROVISIONEDTYPE=MT320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&UEQ\"\n\
   \"MT320-1-1-11::PROVISIONEDTYPE=MT320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,STBYH&UEQ\"\n\
   \"MDL-1-1-12::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-13::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-14::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-15::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-16::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-17::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"PP1GE-1-1-18::PROVISIONEDTYPE=PP1GE,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"MDL-1-1-18-1::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-2::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-3::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-4::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-5::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-6::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-7::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-8::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-9::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-18-10::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-19::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-20::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-21::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-22::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-23::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-24::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-25::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-26::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-27::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-28::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-29::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-30::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-31::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-32::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-33::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-34::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-35::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"MDL-1-1-36::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"POW320-1-1-37::PROVISIONEDTYPE=PSF320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,MEA\"\n\
   \"MDL-1-1-38::AUTOPROV=OFF:OOS-AUMA,UAS&UEQ\"\n\
   \"POW320-1-1-39::PROVISIONEDTYPE=PSF320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,MEA\"\n\
   \"FAN320-1-1-40::PROVISIONEDTYPE=FAN320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"FAN320-1-1-41::PROVISIONEDTYPE=FAN320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,FLT\"\n\
   \"TBUS-1-1-42::PROVISIONEDTYPE=TBUS320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   \"TBUS-1-1-43::PROVISIONEDTYPE=TBUS320,ACTUALTYPE=UNKNOWN,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:IS\"\n\
   /* RTRV-EQPT::ALL [963] (536871273) */\n\
;\n\
"

    if True:
        #print("[{:s}]\n{:s}".format(msg1, "-" * 80))
        mm = TL1message(msg3)
        print(mm.decode("JSON"))
        sys.exit(0)

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg3, "-" * 80))
        mm = TL1message(msg3)
        print(mm)
        print("@@@")
        lista = mm.get_cmd_aid_list()
        #print(lista[0] + " " + mm.get_cmd_status_value(lista[0])[0])
        #print(lista[0] + " " + mm.get_cmd_status_value(lista[0])[1])
        #print(lista[1] + " " + mm.get_cmd_status_value(lista[1])[0])
        #print(lista[1] + " " + mm.get_cmd_status_value(lista[1])[1])
        print(mm.get_cmd_attr_value("EC320-1-1-1", "REGION"))
        print(mm.get_cmd_attr_value("EC320-1-1-1", "PIPPO"))
        print(mm.get_cmd_attr_value("MDL-1-1-18", "AUTOPROV"))
        print("@@@")

        print("#" * 80)

        print("[{:s}]\n{:s}".format(msg4, "-" * 80))
        mm = TL1message(msg4)
        print(mm)
        if False:
            v1,v2,v3 = mm.get_cmd_error_frame()
            if v1:
                print("ERRORE: " + v2)
                print(v3[0])
                print(v3[1])

            print("-" * 80)
        #mm.encode("ASCII")

        sys.exit(0)

    tl1 = Plugin1850TL1("135.221.125.79")

    if False:
        # DB PULITO
        tl1.do("ACT-USER::admin:MYTAG::Root1850;")
        tl1.do("ED-PID::admin:::Root1850,Alcatel1,Alcatel1;")
        #
        tl1.do("SET-PRMTR-NE::::::REGION=ETSI,PROVMODE=MANEQ-AUTOFC;")
        tl1.do("RTRV-PRMTR-NE;")
        tl1.do("SET-ATTR-SECUDFLT::::::MAXSESSION=6;")
        tl1.do("ENT-EQPT::SHELF-1-1::::PROVISIONEDTYPE=UNVRSL320,SHELFNUM=1,SHELFROLE=MAIN;")
    else:
        # DB Inizializzato
        tl1.do("ACT-USER::admin:MYTAG::Alcatel1;")
        tl1.event_collection_start()
        time.sleep(2)
        tl1.do("ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS;", policy="COND", condPST="IS")
        time.sleep(30)
        tl1.do("RTRV-EQPT::MDL-1-1-18;")
        res = tl1.get_last_outcome()
        print(res)
        tl1.do("RMV-EQPT::PP1GE-1-1-18;")
        tl1.do("DLT-EQPT::PP1GE-1-1-18;")

    time.sleep(1)

    tl1.thr_event_terminate()

    print("FINE")

#!/usr/bin/env python
"""
###############################################################################
# MODULE: facility_tl1.py
#
# AUTHOR: C.Ghelfi
# DATE  : 23/11/2015
#
###############################################################################
"""

import sys
import json



class TL1check():
    """ TL1 Message Scanner
    """

    def __init__(self):
        """ Constructor for a TL1 Scanner
        """
        self.__aid_l = []   # List of AID (could be contains Regular Expression)
        self.__pst_l = []   # List of values for Primary State to search on a TL1 Message
        self.__sst_l = []   # List of values for Secondary State to search on a TL1 Message
        self.__fld_l = {}   # Dictionary of <ATTR,VALUE> couple to search on a TL1 Message


    def add_field(self, attr, value):
        """ Insert a new <ATTR,VALUE> field. It is possible to add more than one VALUE for
            an ATTR calling this method with different VALUE
            Please note: a Positional value is a Named value with ATTR := position
        """
        try:
            self.__fld_l[attr].append(value)
        except KeyError:
            self.__fld_l[attr] = [value]


    def res_field(self, attr=None, value=None):
        """ Remove a <ATTR,VALUE> field.
            A None for VALUE remove all fields for specified ATTR
            If used without parameters, the field list will be cleared
        """
        if attr is None:
            self.__fld_l = {}
        else:
            if value is not None:
                self.__fld_l[attr] = [x for x in self.__fld_l[attr] if x != value]
            else:
                self.__fld_l.pop(attr)


    def add_aid(self, aid):
        """ Insert an AID filter.
        """
        self.__aid_l.append(aid)


    def res_aid(self, aid=None):
        """ Remove a specified AID from list. A None for aid cause list cleanup
        """
        if aid is None:
            self.__aid_l = []
        else:
            self.__aid_l.remove(aid)


    def add_pst(self, pst):
        """ Add a PRIMARY STATE value
        """
        self.__pst_l.append(pst)


    def res_pst(self, pst=None):
        """ Remove a specified Primary State value from list. A None for pst cause list cleanup
        """
        if pst is None:
            self.__pst_l = []
        else:
            self.__pst_l.remove(pst)


    def add_sst(self, sst):
        """ Add a SECONDARY STATE value
        """
        self.__sst_l.append(sst)


    def res_sst(self, sst=None):
        """ Remove a specified Secondary State value from list. A None for pst cause list cleanup
        """
        if sst is None:
            self.__sst_l = []
        else:
            self.__sst_l.remove(sst)


    def evaluate_msg(self, msg, pst='OR', sst='OR', fld='OR'):
        """ Perform a filter check on supplied TL1 encoded message
            A tuple <True/False, result_list> is returned.
            The True/False indicates if the matching Filters cause a not empty result.
            In case of positive matching, the result_list return a dictionary of matching
            AID and a list of matched condition for this AID

            The Evaluation Rules foreseens an inner rules for specific type of
            filter (see table). It is possible to specify a boolean rule for
            'pst', 'sst', and 'fld', with optional paramenters.
            Then, all filters are evaluated with logical AND rule
                +---------+-------------+-----------------+
                | FILTER  | DESCRIPTION | INNER RULE      |
                +---------+-------------+-----------------+
                |   AID   | AID list    | always OR       |
                |   PST   | PST list    | pst := OR / AND |
                |   SST   | SST list    | sst := OR / AND |
                |   FLD   | Field list  | fld := OR / AND |
                +---------+-------------+-----------------+
                | General rule (after FILTERS evaluation) |
                |     AID  &&  PST  &&  SST  &&  FLD      |
                +-----------------------------------------+
            NOTE:
            if any Filter class isn't specified, its contribution is always TRUE
        """
        result = False

        result_list = {}

        # TL1 complete command scenario
        if msg.get_cmd_status() == (True, 'COMPLD'):

            for the_aid in msg.get_cmd_aid_list():

                if not self.__evaluate_aid(the_aid):
                    continue

                match_list = []

                the_pst,the_sst = msg.get_cmd_status_value(the_aid)

                match_pst = self.__evaluate_pst(the_pst, rule=pst)
                match_sst = self.__evaluate_sst(the_sst, rule=sst)

                #print(match_pst, match_sst)

                if match_pst[0] and match_sst[0]:

                    for the_attr,the_val in msg.get_cmd_attr_values(the_aid).items():
                        the_att_val = self.__evaluate_attr_val(the_attr, the_val)

                        if the_att_val[0]:
                            result = True
                            match_list.append(the_att_val[1])
                            #print(the_aid, match_pst[1], match_sst[1], the_att_val[1])

                    if match_pst[1] != {}:
                        match_list.append(match_pst[1])
                    if match_sst[1] != {}:
                        match_list.append(match_sst[1])


                if match_list != []:
                    result_list[the_aid] = match_list

            return result, result_list


        print("UNMANAGED SCENARIO")
        return False,None


    def __evaluate_aid(self, aid):
        """ INTERNAL USAGE
        """
        if len(self.__aid_l) == 0:
            return True

        if aid in self.__aid_l:
            return True

        return False


    def __evaluate_pst(self, pst_list, rule='OR'):
        """ INTERNAL USAGE
        """
        if len(self.__pst_l) == 0:
            return True, {}

        intersection = set(pst_list).intersection(self.__pst_l)

        if rule == 'OR':
            if len(intersection) > 0:
                return True, intersection
        else:
            if intersection == set(pst_list):
                return True, intersection

        return False, None


    def __evaluate_sst(self, sst_list, rule='OR'):
        """ INTERNAL USAGE
        """
        if len(self.__sst_l) == 0:
            return True, {}

        intersection = set(sst_list).intersection(self.__sst_l)

        if rule == 'OR':
            if len(intersection) > 0:
                return True, intersection
        else:
            if intersection == set(sst_list):
                return True, intersection

        return False, None


    def __evaluate_attr_val(self, the_attr, the_val, rule='OR'):
        """ INTERNAL USAGE
        """
        for attr, values in self.__fld_l.items():
            if attr == the_attr:
                for val in values:
                    if val == the_val:
                        return True, "{:s}={:s}".format(attr, val)

        return False, ""


    def debug(self):
        """ INTERNAL USAGE
        """
        print("aid list : {}".format(self.__aid_l))
        print("fld list : {}".format(self.__fld_l))
        print("PST list : {}".format(self.__pst_l))
        print("SST list : {}".format(self.__sst_l))




class TL1message():
    """ TL1 Message decomposer
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
                                 aid : AID or index of element (key for dictionary)
                                     'VAL_REF': sequence ATTR=Value
                                     'VAL_POS': positional value list
                                     'STATE'  : Primary and Secondary state
                'R_BODY_KO' : Body Section (Only for failure command response)
                               list of two string response specification
            - only for Spontaneous Messages:
                'S_VMM'     : Verb and modifiers
                'S_AID'     : AID for event
                'S_BODY'    : Text of event
        """

        self.__m_plain = tl1_msg    # Plain ascii TL1 Message Response
        self.__m_coded = None       # Coded Tl1 Message Response (dictionary)
        self.__m_event = None       # True is the message is a Spontaneous Message

        if tl1_msg is not None  and  tl1_msg != "":
            self.__encode()


    def __encode_event(self):
        """ INTERNAL USAGE
        """
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
                check_event = ( words[0] == '*C' or
                                words[0] == '**' or
                                words[0] == '*'  or
                                words[0] == 'A'  )
                if not check_event:
                    print("MESSAGGIO MALFORMATO")
                    return

                self.__m_coded['C_CODE'] = words[0]
                self.__m_coded['C_TAG']  = words[1]
                self.__m_coded['S_VMM']  = words[2:]
                f_ident = False
                continue

            if f_block:
                # Event Response
                words = line.strip().replace('"', '').split(':')
                self.__m_coded['S_AID']  = words[0]
                self.__m_coded['S_BODY'] = words[1].split(',')
                f_block = False
                continue

            if line == ';':
                # TERMINATOR found - closing encoding
                break


    def __encode_response_std(self):
        """ INTERNAL USAGE
        """
        f_header = True
        f_ident  = True
        f_block  = True

        f_skip_n = 0

        for line in self.__m_plain.split('\n'):
            if f_skip_n > 0:
                # Skip one or more lines
                f_skip_n = f_skip_n - 1
                continue

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
                check_event = ( words[0] == '*C' or
                                words[0] == '**' or
                                words[0] == '*'  or
                                words[0] == 'A'  )
                if check_event:
                    print("MESSAGGIO MALFORMATO")
                    return

                self.__m_coded['C_CODE']    = words[0]
                self.__m_coded['C_TAG']     = words[1]
                self.__m_coded['R_STATUS']  = words[2]
                self.__m_coded['R_BODY_OK'] = {}
                self.__m_coded['R_BODY_KO'] = []
                self.__m_coded['R_ERROR']   = ""
                f_ident = False
                continue

            if f_block:
                # Command Response
                stripped_line = line.strip()
                if stripped_line == '>':
                    f_skip_n = 2    # Long response - skip next 2 lines
                    continue
                if ( stripped_line.find('/*') != -1                                     and
                     stripped_line.find("[{:s}]".format(self.__m_coded['C_TAG'])) != -1 and
                     stripped_line.find('*/') != -1                                     ):
                    # REMARK found - closing encoding
                    tmp = stripped_line.replace("/* ","")
                    tmp = tmp[:tmp.find(":")]
                    self.__m_coded['R_BODY_CMD'] = tmp
                    break
                if self.__m_coded['R_STATUS'] == "COMPLD":
                    words = stripped_line.replace('"', '').split(':')
                    row = {}

                    attr_val_list = {}
                    if words[2] != "":
                        for elem in words[2].split(','):
                            attr_val_list[elem.split('=')[0]] = elem.split('=')[1]

                    row[ words[0] ] = {'VAL_REF' : attr_val_list, 'STATE' : words[3]}

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
                # TERMINATOR found - closing encoding
                break


    def __encode_response_asap_prof(self):
        """ INTERNAL USAGE
        """
        f_header = True
        f_ident  = True
        f_block  = True

        f_skip_n = 0

        counter = 1

        for line in self.__m_plain.split('\n'):
            if f_skip_n > 0:
                # Skip one or more lines
                f_skip_n = f_skip_n - 1
                continue

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
                check_event = ( words[0] == '*C' or
                                words[0] == '**' or
                                words[0] == '*'  or
                                words[0] == 'A'  )
                if check_event:
                    print("MESSAGGIO MALFORMATO")
                    return

                self.__m_coded['C_CODE']    = words[0]
                self.__m_coded['C_TAG']     = words[1]
                self.__m_coded['R_STATUS']  = words[2]
                self.__m_coded['R_BODY_OK'] = {}
                self.__m_coded['R_BODY_KO'] = []
                self.__m_coded['R_ERROR']   = ""
                f_ident = False
                continue

            if f_block:
                # Command Response
                stripped_line = line.strip()
                if stripped_line == '>':
                    f_skip_n = 2    # Long response - skip next 2 lines
                    continue
                if ( stripped_line.find('/*') != -1                                     and
                     stripped_line.find("[{:s}]".format(self.__m_coded['C_TAG'])) != -1 and
                     stripped_line.find('*/') != -1                                     ):
                    # REMARK found - closing encoding
                    tmp = stripped_line.replace("/* ","")
                    tmp = tmp[:tmp.find(":")]
                    self.__m_coded['R_BODY_CMD'] = tmp
                    break
                if self.__m_coded['R_STATUS'] == "COMPLD":
                    words = stripped_line.replace('"', '').split(':')
                    row = {}
                    if words[0] != "":
                        attr_val_list = {}
                        for elem in words[2].split(','):
                            attr_val_list[elem.split('=')[0]] = elem.split('=')[1]
                        row[ words[0] ] = {'VAL_REF' : attr_val_list}
                    else:
                        row[ str(counter) ] = {'VAL_POS' : words[2].split(',')}
                        counter = counter + 1
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
                # TERMINATOR found - closing encoding
                break


    def __encode(self):
        """ INTERNAL USAGE
            Decompose an ASCII TL1 Message response to structured format
        """
        is_event = False
        is_response_std = False
        is_response_asap_prof = False

        for line in self.__m_plain.split('\n'):
            if line.strip() == "":
                continue

            marker = line.split()[0]

            if marker == "M":
                if self.__m_plain.find("RTRV-ASAP-PROF") != -1:
                    is_response_asap_prof = True
                else:
                    is_response_std = True
                self.__m_event = False
                break

            if marker == '*C' or marker == '**' or marker == '*' or marker == 'A':
                is_event = True
                self.__m_event = True
                break

        self.__m_coded = {}     # Reset internal coded message

        if is_response_std:
            self.__encode_response_std()
            return

        if is_response_asap_prof:
            self.__encode_response_asap_prof()
            return

        if is_event:
            self.__encode_event()
            return

        print("UNMANAGED MESSAGE TYPE")


    def decode(self, codec="ASCII"):
        """ Format the structured TL1 message to supplied coded
            codec : "ASCII" / "JSON"
        """
        new_msg = ""
        if   codec == "ASCII":
            pass
        elif codec == "JSON":
            new_msg = json.dumps(self.__m_coded, indent=4, sort_keys=True, separators=(',',' : '))
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

        try:
            pst_list,sst_list = the_elem['STATE'].split(',')
            return pst_list.split('&'), sst_list.split('&')
        except Exception as eee:
            return None, None


    def get_cmd_attr_value(self, aid, attr):
        """ Return the value for specified attribute and AID
            None if wrong parameters are supplied
            Only for <ATTR,VALUE> response list
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VAL_REF'][attr]
        except Exception as eee:
            return None

        return None


    def get_cmd_attr_values(self, aid):
        """ Return the <attr,value> list for specified AID
            None if wrong parameters are supplied
            Only for <ATTR,VALUE> response list
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VAL_REF']
        except Exception as eee:
            return None


    def get_cmd_positional_value(self, aid, pos):
        """ Return the value for specified positional attribute and AID
            None if wrong parameters are supplied
            Only for Positional response list
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VAL_POS'][pos]
        except Exception as eee:
            return None


    def get_cmd_positional_values(self, aid):
        """ Return the value for specified positional attribute and AID
            None if wrong parameters are supplied
            Only for Positional response list
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VAL_POS']
        except Exception as eee:
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

    msg1 = """

   PLEASE-SET-SID-C8A00 15-10-04 17:01:56
*  243 REPT ALM EQPT
   "MDL-1-1-18:MN,ABNORMAL,NSA,10-04,17-01-56,NEND"
;
"""

    msg2 = """

   PLEASE-SET-SID-C8A00 15-10-04 18:35:10
M  379 COMPLD
   "EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT"
   /* RTRV-EQPT::MDL-1-1-1 [379] (536871116) */
;
"""

    msg3 = """

   PLEASE-SET-SID-C8A00 15-10-04 20:31:15
M  165 COMPLD
   "EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT"
   "MDL-1-1-18::ACTUALTYPE=PP1GE,AUTOPROV=OFF:OOS-MA,UAS"
   /* RTRV-EQPT::MDL-1-1-1&-18 [165] (536871116) */
;
"""

    msg4 = """

   PLEASE-SET-SID-C8A00 15-10-05 17:25:40
M  792 DENY
   IEAE
   /* Input, Entity Already Exists */
   /* Equipment is already Provisioned */
   /* ENT-EQPT::PP1GE-1-1-18::::PROVISIONEDTYPE=PP1GE:IS [792] (536871116) */
;
"""

    msg5 = """

   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-1::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AUMA,PMD&SGEO"
   "MVC4-1-1-36-2::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X010010011101010010010101110010,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-3::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-4::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-5::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-6::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-7::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-8::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-9::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-10::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-11::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-12::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-13::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-14::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-15::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-16::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-17::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-18::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-19::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-20::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-21::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-22::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-23::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-24::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-25::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-26::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-27::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-28::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-29::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-30::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-31::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-32::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-33:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-34:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-35:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-36:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-37:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-38:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-39:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-40:::OOS-AUMA,DSBLD&UAS"
   "MVC4-1-1-36-41::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-42::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-43::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-44::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-45::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-46::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-47::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X010010011101010010010101110010,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-48::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-49::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X010010011101010010010101110010,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-50::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-51::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-52::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-53::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-54::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-55::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-56::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-57::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-58::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-59::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-60::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-61::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
>
   "nodeA - HFmCheckPomOnMVC4TU12-rg" 14-03-16 01:55:45
M  780 COMPLD
   "MVC4-1-1-36-62::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-63::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   "MVC4-1-1-36-64::AINSTH=0-1,PTFTYPE=MODVC4,PTFRATE=VC4,RDITYPE=1BIT,SDSFMODE=POISSON,BRSTINTVL=7,BRSTTH=1000,SDTH=6,SFTH=3,TRC=X000000000000000000000000000000,TRCEXPECTED=X000000000000000000000000000000,TRCMON=N,TRCCONSACT=Y,ALMPROF=LBL-ASAPVC4-SYSDFLT,TCAPROF=LBL-THPVC4-SYSDFLT,LOSTRUCT=3xTU3,CAPLIST=HOTIM&HOTTISO&HOTTIRTRV&BURSTHOBER&POISSONHOBER&LOINGPOM&LOEGPOM&LOTIM&LOTTIRTRV&BURSTLOBER&POISSONLOBER,MGRACD=<null>:OOS-AU,PMD&SGEO"
   /* RTRV-PTF::MVC4-1-1-36-1&&-64::::PTFTYPE=MODVC4,PTFRATE=VC4 [780] (536870923) */
;
"""

    #mm = TL1message(msg1)
    #print(mm.decode("JSON"))
    #mm = TL1message(msg4)
    #print(mm.decode("JSON"))
    #mm = TL1message(msg3)
    #print(mm.decode("JSON"))
    mm = TL1message(msg5)
    print(mm.decode("JSON"))
    print(mm.get_cmd_attr_value("MVC4-1-1-36-23", "TRC"))
    filt = TL1check()
    filt.add_aid("MVC4-1-1-36-33")
    filt.add_aid("MVC4-1-1-36-23")
    filt.add_aid("MVC4-1-1-36-49")
    filt.add_aid("MVC4-1-1-36-3")
    filt.add_pst("OOS-AU")
    filt.add_sst("SGEO")
    filt.add_sst("PMD")
    filt.add_field("PTFTYPE", "MODVC4")
    filt.add_field("TRC", "X010010011101010010010101110010")
    filt.debug()
    print(filt.evaluate_msg(mm, sst='AND'))

    sys.exit(0)

    #print("[{:s}]\n{:s}".format(msg1, "-" * 80))
    mm = TL1message(msg3)
    print(mm.decode("JSON"))

    filt = TL1check()
    filt.add_field("PTFRATE", "MODVC4")
    filt.debug()
    print(filt.evaluate_msg(mm))

    print("FINE")

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


def is_autonomous_msg(code):
    """ Return True if the specified code is any of:
        *C  : autonomous critical alarm
        **  : autonomous major alarm
        *   : autonomous minor or warning alarm
        A   : autonomous non-alarm event
        I   " autonomous information message
    """
    return code == '*C' or code == '**' or code == '*' or code == 'A' or code == 'I'


def is_any_alarm(code):
    """ Return True if the specified code is any of:
        *C  : autonomous critical alarm
        **  : autonomous major alarm
        *   : autonomous minor or warning alarm
    """
    return code == '*C' or code == '**' or code == '*'



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
        self.__fld_l[attr] = value
        #try:
            #self.__fld_l[attr].append(value)
        #except KeyError:
            #self.__fld_l[attr] = [value]


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

                match_pst = self.__evaluate_pst(msg.get_cmd_pst(the_aid), rule=pst)
                match_sst = self.__evaluate_sst(msg.get_cmd_sst(the_aid), rule=sst)

                if match_pst[0] and match_sst[0]:

                    #print("messaggio := {}".format(msg.get_cmd_attr_values(the_aid)))
                    #print(" da filtr := {}".format(self.__fld_l))

                    for the_attr,the_val in msg.get_cmd_attr_values(the_aid).items():

                        match_attr_val = self.__evaluate_attr_val(the_attr, the_val, rule=fld)
                        print("<{},{}> : {}".format(the_attr,the_val, match_attr_val))

                        if match_attr_val[0]:
                            match_list.append(match_attr_val[1])

                    if match_pst[1] != {}:
                        match_list.append(match_pst[1])

                    if match_sst[1] != {}:
                        match_list.append(match_sst[1])

                if match_list != []:
                    result_list[the_aid] = match_list

            result = (len(result_list) > 0)

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
        if rule == 'OR':
            for attr, values in self.__fld_l.items():
                if attr == the_attr:
                    if isinstance(values, list):
                        for val in list(values):
                            if val == the_val:
                                return True, "{:s}={:s}".format(attr, val)
                    else:
                        if values == the_val:
                            return True, "{:s}={:s}".format(attr, values)
        else:
            pass

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
                'C_CODE'    : 'M' / '*C' / '**' / '*' / 'A' / 'I'
                'C_TAG'     : the message TAG
            - only for Commands Response:
                'R_STATUS'  : COMPLD / DELAY / DENY / PRTL / RTRV
                'R_BODY_OK' : Body Section(Only for successfull command response)
                              list of 1 or more items - Dictionary:
                                 aid : AID or index of element (key for dictionary)
                                     'VALUE': sequence ATTR=Value
                                     'PST'    : Primary State value list
                                     'SST'    : Secondary State value list
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
                if not is_autonomous_msg(words[0]):
                    print("MESSAGGIO MALFORMATO")
                    return

                self.__m_coded['C_CODE'] = words[0]
                self.__m_coded['C_TAG']  = words[1]
                self.__m_coded['S_VMM']  = " ".join(words[2:])
                f_ident = False
                continue

            if f_block:
                # Event Response
                #print("EVENT {}".format(line.strip().replace('"', '')))
                if is_any_alarm(self.__m_coded['C_CODE']):
                    words = line.strip().replace('"', '').split(':')
                    self.__m_coded['S_AID']  = words[0]
                    self.__m_coded['S_BODY'] = words[1]
                else:
                    words = line.strip().replace('"', '')
                    if words.count(':') == 5:
                        self.__m_coded['S_AID'] = words.split(':')[2]
                    elif words.count(':') == 1:
                        self.__m_coded['S_AID'] = words.split(':')[0]
                    self.__m_coded['S_BODY'] = words

                f_block = False
                continue

            if line == ';':
                # TERMINATOR found - closing encoding
                break


    def __encode_resp_std(self):
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

                if is_autonomous_msg(words[0]):
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

                    if words[3].find(',') != -1:
                        my_pst_list = words[3].split(',')[0].split('&')
                        my_sst_list = words[3].split(',')[1].split('&')
                    else:
                        my_pst_list = words[3].split('&')
                        my_sst_list = ""
                    row[ words[0] ] = {'VALUE' : attr_val_list, 'PST' : my_pst_list, 'SST' : my_sst_list}

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


    def __encode_resp_ent_crs(self):
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

                if is_autonomous_msg(words[0]):
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
                    row[ words[0] ] = {}

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


    def __encode_resp_asap_prof(self):
        """ INTERNAL USAGE
        """
        f_header = True
        f_ident  = True
        f_block  = True

        f_skip_n = 0

        pseudo_aid = 1  # Identifier for "emtpy-aid" response rows

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
                if is_autonomous_msg(words[0]):
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
                        row[ words[0] ] = {'VALUE' : attr_val_list}
                    else:
                        positional = 1
                        attr_val_list = {}
                        for elem in words[2].split(','):
                            attr_val_list[ positional ] = elem
                            positional = positional + 1
                        row[ str(pseudo_aid) ] = {'VALUE' : attr_val_list}
                        pseudo_aid = pseudo_aid + 1
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


    def __encode_resp_rtrv_cond(self):
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
                if is_autonomous_msg(words[0]):
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
                    the_aid = words[0]

                    row = {}
                    positional = 1
                    attr_val_list = {}
                    for elem in words[1].split(','):
                        attr_val_list[ positional ] = elem
                        positional = positional + 1
                    row[ the_aid ] = {'VALUE' : attr_val_list}
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


    def __encode_resp_rtrv_no_status(self):
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

                if is_autonomous_msg(words[0]):
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
                    print(words)
                    attr_val_list = {}
                    if words[2] != "":
                        for elem in words[2].split(','):
                            attr_val_list[elem.split('=')[0]] = elem.split('=')[1]

                    row[ words[0] ] = {'VALUE' : attr_val_list }

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
        response_type = "std"

        for line in self.__m_plain.split('\n'):
            if line.strip() == "":
                continue

            marker = line.split()[0]

            if is_autonomous_msg(marker):
                is_event = True
                self.__m_event = True
                break

            if marker == "M":
                if   self.__m_plain.find("RTRV-ASAP-PROF") != -1:
                    response_type = "ASAP_PROF"
                elif self.__m_plain.find("RTRV-COND") != -1:
                    response_type = "RTRV_COND"
                elif self.__m_plain.find("ENT-CRS") != -1:
                    response_type = "ENT_CRS"
                elif self.__m_plain.find("RTRV-LOPOOL") != -1:
                    response_type = "RTRV_LOPOOL"
                else:
                    response_type = "STD"
                self.__m_event = False
                break

        self.__m_coded = {}     # Reset internal coded message

        if response_type == "STD":
            self.__encode_resp_std()
            return

        if response_type == "ASAP_PROF":
            self.__encode_resp_asap_prof()
            return

        if response_type == "RTRV_COND":
            self.__encode_resp_rtrv_cond()
            return

        if response_type == "RTRV_LOPOOL":
            self.__encode_resp_rtrv_no_status()
            return

        if response_type == "ENT_CRS":
            self.__encode_resp_ent_crs()
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
        """ Return the TL1 Message code as follow: "M" / "**" / "*C" / "*" / "A" / "I"
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


    def get_cmd_pst(self, aid):
        """ For specified aid item, return the Primary State value
            In case of errors, a None is returned
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        the_elem = self.__m_coded['R_BODY_OK'].get(aid)
        if the_elem is None:
            return None

        try:
            return the_elem['PST']
        except Exception as eee:
            return None


    def get_cmd_sst(self, aid):
        """ For specified aid item, return the Secondary State value
            In case of errors, a None is returned
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        the_elem = self.__m_coded['R_BODY_OK'].get(aid)
        if the_elem is None:
            return None

        try:
            return the_elem['SST']
        except Exception as eee:
            return None


    def get_cmd_response_size(self):
        """ Return the number of valid rows for current TL1 Response
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        return len(self.__m_coded['R_BODY_OK'])


    def get_cmd_attr_value(self, aid, attr):
        """ for <ATTR,VALUE> response list: return value of specified attribute
            for positional response list: 'attr' indicate the positional index
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VALUE'][attr]
        except Exception as eee:
            return None

        return None


    def get_cmd_attr_values(self, aid):
        """ Return the response list for specified AID
            The response could be a <ATTR,VALUE> list for named parameters, or
            a <POS,VALUE> list for positional parameters
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None

        try:
            return self.__m_coded['R_BODY_OK'].get(aid)['VALUE']
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


    def get_eve_aid(self):
        """ Get Event AID
        """
        return self.__m_coded['S_AID']


    def get_eve_type(self):
        """ Get Event Type content
        """
        return self.__m_coded['S_VMM']


    def get_eve_body(self):
        """ Get Event Body content
        """
        return self.__m_coded['S_BODY']




if __name__ == "__main__":
    print("DEBUG")

    msg3 = """

   PLEASE-SET-SID-C8A00 15-10-04 20:31:15
M  165 COMPLD
   "EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT"
   "MDL-1-1-18::ACTUALTYPE=PP1GE,AUTOPROV=OFF:OOS-MA,UAS"
   /* RTRV-EQPT::MDL-1-1-1&-18 [165] (536871116) */
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

    msg6 = """

   PLEASE-SET-SID-63880 15-09-18 05:11:48
M  480 COMPLD
   "ASAPEQPT-0,EQPT::DFLT=N,USERLABEL=LBL-ASAPEQPT-None"
   "::ABNORMAL,NR,NSA,NEND"
   "::AIRTEMP,NR,NSA,NEND"
   "::BPERROR,NR,SA,NEND"
   "::CONTBUS,NR,SA,NEND"
   "::CONTBUS,NR,NSA,NEND"
   "::CONTCOM,NR,SA,NEND"
   "::DBF,NR,NSA,NEND"
   "::FA,NR,SA,NEND"
   "::FA,NR,NSA,NENDxx"
   "::HWFAIL,NR,SA,NEND"
   "::HWFAIL,NR,NSA,NEND"
   "::IMPROPRMVL,NR,SA,NEND"
   "::IMPROPRMVL,NR,NSA,NEND"
   "::LANFAIL,NR,SA,NEND"
   "::MAN,NR,SA,NEND"
   "::MAN,NR,NSA,NEND"
   "::MISC-1,NR,NSA,NEND"
   "::MTXLNKFAIL,NR,SA,NEND"
   "::MTXLNKFAIL,NR,NSA,NEND"
   "::NTPOOSYNC,NR,NSA,NEND"
   "::PRCDRERR,NR,SA,NEND"
   "::PRCDRERR,NR,NSA,NEND"
   "::PWR,NR,SA,NEND"
   "::PWR,NR,NSA,NEND"
   "::RAIDSYNC,NR,NSA,NEND"
   "::SYNCEQPT,NR,SA,NEND"
   "::SYNCEQPT,NR,NSA,NEND"
   "::CLKADJ,NR,NSA,NEND"
   "::IR-EOLSPAN,NR,NSA,NEND"
   "::IR-N1,NR,NSA,NEND"
   "::IR-VOA,NR,NSA,NEND"
   "::IR-IT,NR,NSA,NEND"
   "::IR-OP1,NR,NSA,NEND"
   "::IR-OP2,NR,NSA,NEND"
   "::DBPROB,NR,SA,NEND"
   "::DBCKFAIL,NR,SA,NEND"
   "::SWCKFAIL,NR,SA,NEND"
   "::SWCKFAIL,NR,SA,NEND"
   "::MNGIFPLGIN,NR,NSA,NEND"
   "::DISKFULL,NR,NSA,NEND"
   "::DSCFGALIGN,NR,NSA,NEND"
   "::PWROFF,NR,SA,NEND"
   "::PWROFF,NR,NSA,NEND"
   /* RTRV-ASAP-PROF::ASAPEQPT-0 [480] (536871198) */
;
"""

    msg8 = """

   PLEASE-SET-SID-10980 12-07-21 08:34:57
M  693 COMPLD
   "MVC4-1-1-7-1,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-2,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-3,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-4,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-5,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-6,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-7,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-8,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-9,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-10,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-11,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-12,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-13,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-14,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-15,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-16,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-17,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-18,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-19,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-20,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-21,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-22,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-23,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-24,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-25,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-26,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-27,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-28,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-29,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-30,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-31,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-32,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-33,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-34,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-35,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-36,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-37,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-38,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-39,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-40,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-41,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-42,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-43,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-44,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-45,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-46,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-47,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-48,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-49,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-50,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-51,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-52,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-53,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-54,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-55,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-56,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-57,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-58,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-59,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-60,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-61,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-62,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-63,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-64,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-65,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-66,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-67,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-68,VC4:NR,MAN,NSA,07-21,07-47-56,NEND,RCV"
   "MVC4-1-1-7-69,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-70,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-71,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-72,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-73,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-74,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-75,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-76,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-77,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-78,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-79,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-80,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-81,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-82,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-83,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-84,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-85,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-86,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-87,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-88,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-89,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-90,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-91,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-92,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-93,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-94,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-95,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-96,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-97,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-98,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-99,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-100,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-101,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-102,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-103,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-104,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-105,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-106,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-107,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-108,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-109,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-110,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-111,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-112,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-113,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-114,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-115,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-116,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-117,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-118,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-119,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-120,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-121,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-122,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-123,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-124,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-125,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-126,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-127,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-128,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-129,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-130,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-131,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-132,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-133,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-134,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-135,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-136,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-137,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-138,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-139,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-140,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-141,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-142,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-143,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-144,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-145,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-146,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-147,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-148,VC4:NR,MAN,NSA,07-21,07-47-57,NEND,RCV"
   "MVC4-1-1-7-149,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-150,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-151,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-152,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-153,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-154,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-155,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-156,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-157,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-158,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-159,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-160,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-161,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-162,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-163,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-164,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-165,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-166,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-167,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-168,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-169,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-170,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-171,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-172,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-173,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-174,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-175,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-176,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-177,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-178,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-179,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-180,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-181,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-182,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-183,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-184,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-185,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-186,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-187,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-188,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-189,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-190,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-191,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-192,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-193,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-194,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-195,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-196,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-197,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-198,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-199,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-200,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-201,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-202,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-203,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-204,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-205,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-206,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-207,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-208,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-209,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-210,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-211,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-212,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-213,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-214,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-215,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-216,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-217,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-218,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-219,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-220,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-221,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-222,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-223,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-224,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-225,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-226,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-227,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-228,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-229,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-230,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-231,VC4:NR,MAN,NSA,07-21,07-47-58,NEND,RCV"
   "MVC4-1-1-7-232,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-233,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-234,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-235,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-236,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-237,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-238,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-239,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-240,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-241,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-242,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-243,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-244,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-245,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-246,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-247,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-248,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-249,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-250,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-251,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-252,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-253,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-254,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-255,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-256,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-257,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-258,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-259,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-260,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-261,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-262,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-263,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-264,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-265,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-266,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-267,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-268,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-269,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-270,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-271,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-272,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-273,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-274,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-275,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-276,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-277,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-278,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-279,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-280,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-281,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-282,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-283,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-284,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-285,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-286,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-287,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-288,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-289,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-290,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-291,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-292,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-293,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-294,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-295,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-296,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-297,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-298,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-299,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-300,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-301,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-302,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-303,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-304,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-305,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-306,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-307,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-308,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-309,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-310,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-311,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-312,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-313,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-314,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-315,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-316,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-317,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-318,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-319,VC4:NR,MAN,NSA,07-21,07-47-59,NEND,RCV"
   "MVC4-1-1-7-320,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-321,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-322,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-323,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-324,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-325,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-326,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-327,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-328,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-329,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-330,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-331,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-332,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-333,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-334,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-335,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-336,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-337,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-338,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-339,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-340,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-341,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-342,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-343,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-344,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-345,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-346,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-347,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-348,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-349,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-350,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-351,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-352,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-353,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-354,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-355,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-356,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-357,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-358,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-359,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-360,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-361,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-362,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-363,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-364,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-365,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-366,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-367,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-368,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-369,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-370,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-371,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-372,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-373,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-374,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-375,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-376,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-377,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-378,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-379,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-380,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-381,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-382,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-383,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   "MVC4-1-1-7-384,VC4:NR,MAN,NSA,07-21,07-48-00,NEND,RCV"
   /* RTRV-COND-VC4::ALL:::MAN [693] (536870999) */
;
"""


    mm = TL1message(msg8)
    print(mm.decode("JSON"))

    sys.exit(0)

    if True:
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
        filt.add_field("TRC", "PIPPO")
        filt.debug()
        print(filt.evaluate_msg(mm, sst='AND'))
    else:
        mm = TL1message(msg6)
        print(mm.decode("JSON"))
        print(mm.get_cmd_attr_values("9"))
        print(mm.get_cmd_attr_value("9", 4))

    sys.exit(0)

    mm = TL1message(msg3)
    print(mm.decode("JSON"))

    filt = TL1check()
    filt.add_field("PTFRATE", "MODVC4")
    filt.debug()
    print(filt.evaluate_msg(mm))

    print("FINE")

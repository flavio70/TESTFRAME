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
import re


def is_autonomous_msg(code):
    """ Return True if the specified code is any of:
        *C  : autonomous critical alarm
        **  : autonomous major alarm
        *   : autonomous minor or warning alarm
        A   : autonomous non-alarm event
        I   : autonomous information message
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

                match_pst = self.__evaluate_pst(msg.get_cmd_pst(the_aid)[0], rule=pst)
                match_sst = self.__evaluate_sst(msg.get_cmd_sst(the_aid)[0], rule=sst)
                #the assumption is that we find pst and sst fields only to the first element list
                #because in case of presence of pst and sst the message is made by only one element list

                if match_pst[0] and match_sst[0]:

                    #print("messaggio := {}".format(msg.get_cmd_attr_values(the_aid)))
                    #print(" da filtr := {}".format(self.__fld_l))
                    
                    zq_aid_list = msg.get_cmd_attr_values(the_aid)
                    for zq_i in range(len(zq_aid_list)):
                        for the_attr,the_val in zq_aid_list[zq_i].items():
    
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
        self.__m_type = None        # Response type code used for parsing different output scenarious: 'STD'|RTRV-COND...

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
                self.__m_coded['S_AID'] = ""
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
                    the_aid = words[0]
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
                        
                        
                    if the_aid in self.__m_coded['R_BODY_OK'].keys():
                        #aid already present in the R_BODY_OK dict structure
                        self.__m_coded['R_BODY_OK'][the_aid].append({'VALUE' : attr_val_list, 'PST' : my_pst_list, 'SST' : my_sst_list})
                    else:
                        #aid is not present in the R_BODY_OK dict structure
                        row[ the_aid ]=[]
                        row[ the_aid ].append({'VALUE' : attr_val_list, 'PST' : my_pst_list, 'SST' : my_sst_list})
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
                    the_aid=words[0]
                    #row[ words[0] ] = {}
                    
                                          
                    if the_aid in self.__m_coded['R_BODY_OK'].keys():
                        #aid already present in the R_BODY_OK dict structure
                        self.__m_coded['R_BODY_OK'][the_aid].append({})
                    else:
                        #aid is not present in the R_BODY_OK dict structure
                        row[ the_aid ]=[]
                        row[ the_aid ].append({})
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
                            
                                                
                        if words[0] in self.__m_coded['R_BODY_OK'].keys():
                            #aid already present in the R_BODY_OK dict structure
                            self.__m_coded['R_BODY_OK'][words[0]].append({'VALUE' : attr_val_list})
                        else:
                            #aid is not present in the R_BODY_OK dict structure
                            row[ words[0] ]=[]
                            row[ words[0] ].append({'VALUE' : attr_val_list})
                            self.__m_coded['R_BODY_OK'].update(row)                                    
                    else:
                        positional = 1
                        attr_val_list = {}
                        for elem in words[2].split(','):
                            attr_val_list[ positional ] = elem
                            positional = positional + 1
  
  
                                              
                        if pseudo_aid in self.__m_coded['R_BODY_OK'].keys():
                            #aid already present in the R_BODY_OK dict structure
                            self.__m_coded['R_BODY_OK'][pseudo_aid].append({'VALUE' : attr_val_list})
                        else:
                            #aid is not present in the R_BODY_OK dict structure
                            row[ pseudo_aid ]=[]
                            row[ pseudo_aid ].append({'VALUE' : attr_val_list})
                            self.__m_coded['R_BODY_OK'].update(row)

                        pseudo_aid = pseudo_aid + 1
                        
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

                    if the_aid in self.__m_coded['R_BODY_OK'].keys():
                        #aid already present in the R_BODY_OK dict structure
                        self.__m_coded['R_BODY_OK'][the_aid].append({'VALUE' : attr_val_list})
                    else:
                        #aid is not present in the R_BODY_OK dict structure
                        row[ the_aid ]=[]
                        row[ the_aid ].append({'VALUE' : attr_val_list})
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


    def __encode_resp_rtrv_pos_and_name(self):
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
                    if words[1] != "":
                        local_index = 1
                        for elem in words[1].split(','):
                            attr_val_list[str(local_index)] = elem
                            local_index += 1

                    if words[2] != "":
                        for elem in words[2].split(','):
                            attr_val_list[elem.split('=')[0]] = elem.split('=')[1]
                                           
                        if words[0] in self.__m_coded['R_BODY_OK'].keys():
                            #aid already present in the R_BODY_OK dict structure
                            self.__m_coded['R_BODY_OK'][words[0]].append({'VALUE' : attr_val_list})
                        else:
                            #aid is not present in the R_BODY_OK dict structure
                            row[ words[0] ]=[]
                            row[ words[0] ].append({'VALUE' : attr_val_list})
                            self.__m_coded['R_BODY_OK'].update(row)

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


    def __encode_resp_rtrv_crs(self):
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
                    if words[1] != "":
                        local_index = 1
                        for elem in words[1].split(','):
                            attr_val_list[str(local_index)] = elem
                            local_index += 1
                            
                    if words[3].find(',') != -1:
                        my_pst_list = words[3].split(',')[0].split('&')
                        my_sst_list = words[3].split(',')[1].split('&')
                    else:
                        my_pst_list = words[3].split('&')
                        my_sst_list = ""        

                    if words[2] != "":
                        for elem in words[2].split(','):
                            attr_val_list[elem.split('=')[0]] = elem.split('=')[1]
                                           
                        if words[0] in self.__m_coded['R_BODY_OK'].keys():
                            #aid already present in the R_BODY_OK dict structure
                            self.__m_coded['R_BODY_OK'][words[0]].append({'VALUE' : attr_val_list,'PST' : my_pst_list, 'SST' : my_sst_list})
                        else:
                            #aid is not present in the R_BODY_OK dict structure
                            row[ words[0] ]=[]
                            row[ words[0] ].append({'VALUE' : attr_val_list,'PST' : my_pst_list, 'SST' : my_sst_list})
                            self.__m_coded['R_BODY_OK'].update(row)

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


                        if words[0] in self.__m_coded['R_BODY_OK'].keys():
                            #aid already present in the R_BODY_OK dict structure
                            self.__m_coded['R_BODY_OK'][words[0]].append({'VALUE' : attr_val_list})
                        else:
                            #aid is not present in the R_BODY_OK dict structure
                            row[ words[0] ]=[]
                            row[ words[0] ].append({'VALUE' : attr_val_list})
                            self.__m_coded['R_BODY_OK'].update(row)



                    #row[ words[0] ] = {'VALUE' : attr_val_list }

                    #self.__m_coded['R_BODY_OK'].update(row)
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
                    self.__m_type = "ASAP_PROF"
                elif self.__m_plain.find("RTRV-COND") != -1:
                    response_type = "RTRV_COND"
                    self.__m_type = "RTRV-COND"
                elif self.__m_plain.find("ENT-CRS") != -1:
                    response_type = "ENT_CRS"
                    self.__m_type = "ENT_CRS"
                elif self.__m_plain.find("RTRV-LOPOOL") != -1:
                    response_type = "RTRV_LOPOOL"
                    self.__m_type = "RTRV_LOPOOL"
                elif self.__m_plain.find("RTRV-PM") != -1:
                    response_type = "RTRV_POS_AND_NAME"
                    self.__m_type = "RTRV_POS_AND_NAME"
                elif self.__m_plain.find("RTRV-CRS") != -1:
                    response_type = "RTRV_CRS"
                    self.__m_type = "RTRV_CRS"
                elif self.__m_plain.find("RTRV-ALM") != -1:
                    response_type = "RTRV_COND"
                    self.__m_type = "RTRV_COND"
                elif self.__m_plain.find("RTRV-FFP-STM") != -1:
                    response_type = "ASAP_PROF"
                    self.__m_type = "ASAP_PROF"
                else:
                    response_type = "STD"
                    self.__m_type = "STD"
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

        if response_type == "RTRV_POS_AND_NAME":
            self.__encode_resp_rtrv_pos_and_name()
            return
        
        if response_type == "RTRV_CRS":
            self.__encode_resp_rtrv_crs()
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

        if aid not in self.__m_coded['R_BODY_OK'].keys():
            #aid not present in the Body result
            return None
   
        the_elem_list = self.__m_coded['R_BODY_OK'][aid]
        if not the_elem_list:
            #the list is empty
            return None

        try:
            res=[]
            for elem in the_elem_list:res.append(elem['PST'])
            return res
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

        if aid not in self.__m_coded['R_BODY_OK'].keys():
            #aid not present in the Body results
            return None
  
        the_elem_list = self.__m_coded['R_BODY_OK'][aid]
        if not the_elem_list:
            #the list is empty
            return None

        try:
            res=[]
            for elem in the_elem_list:res.append(elem['SST'])
            return res
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
    
    def get_cmd_display_output_rows(self):
        """ Return and display the list of the valid rows (one dictionary is one rows) 
            in the TL1 Response and calculate the number of valid rows 
            None if wrong parameters are supplied
        """
        c = 1
        b = []
        
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None
        
        if self.__m_coded['R_BODY_OK'] == {}:
            return None
        
        for the_key,the_val in self.__m_coded['R_BODY_OK'].items():
                  print("Values the_key {} the_val {}\n".format(the_key,the_val))
                  
        a = self.__m_coded['R_BODY_OK'][the_key].__len__() #calcola la lunghezza della lista di dizionari
        
        for errore in self.__m_coded['R_BODY_OK'][the_key]:
            b.append(errore)
            print("Dizionario {} = {}".format(int(c),errore))
            c = c + 1   
        print("\n")
        return b


    def get_cmd_attr_value(self, aid, attr):
        """ for <ATTR,VALUE> response list: return value of specified attribute
            for positional response list: 'attr' indicate the positional index
            None if wrong parameters are supplied
        """
        if self.__m_event:
            return None

        if self.get_cmd_status() != (True, "COMPLD"):
            return None
            
        if aid not in self.__m_coded['R_BODY_OK'].keys():
            #aid not present in the Body result
            return None

        if aid.find('*') == -1:
            the_elem_list = self.__m_coded['R_BODY_OK'][aid]
            if not the_elem_list:
                #the list is empty
                return None      
            try:
                res=[]
                for elem in the_elem_list:res.append(elem['VALUE'][attr])
                return res
                #return self.__m_coded['R_BODY_OK'].get(aid)['VALUE'][attr]
            except Exception as eee:
                return None
        else:
            try:
                for the_key,the_val in self.__m_coded['R_BODY_OK'].items():
                    if re.search(aid, the_key):
                        #the_val is the item list to be processed
                        if not the_elem_list:
                            #the list is empty
                            return None
                        res=[]
                        for elem in the_val:res.append(elem['VALUE'][attr])
                        return res
                        #return the_val['VALUE'][attr]
                    else:
                        return None
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

        if aid not in self.__m_coded['R_BODY_OK'].keys():
            #aid not present in the Body result
            return None


        the_elem_list = self.__m_coded['R_BODY_OK'][aid]
        if not the_elem_list:
            #the list is empty
            return None
        try:        
            res=[]
            for elem in the_elem_list:res.append(elem['VALUE'])
            return res
        
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



    def get_msg_type(self):
        """ Get Message type
        """
        return self.__m_type

if __name__ == "__main__":
    print("DEBUG")

    MSG3 = """

   PLEASE-SET-SID-C8A00 15-10-04 20:31:15
M  165 COMPLD
   "EC320-1-1-1::PROVISIONEDTYPE=EC320,ACTUALTYPE=EC320,AINSMODE=NOWAIT,ALMPROF=LBL-ASAPEQPT-SYSDFLT,REGION=ETSI,PROVMODE=MANEQ-AUTOFC:OOS-AU,WRK&FLT"
   "MDL-1-1-18::ACTUALTYPE=PP1GE,AUTOPROV=OFF:OOS-MA,UAS"
   /* RTRV-EQPT::MDL-1-1-1&-18 [165] (536871116) */
;
"""

    MSG5 = """

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

    MSG6 = """

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

    MSG8 = """

   PLEASE-SET-SID-10980 12-09-13 05:45:11
M  416 COMPLD
   "MVC4-1-1-7-1:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-2:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-3:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-4:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-5:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-6:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-7:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-8:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-9:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-10:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-11:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-12:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-13:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-14:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-15:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-16:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-17:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-18:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-19:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-20:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-21:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-22:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-23:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-24:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-25:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-26:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-27:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-28:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-29:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-30:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-31:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-32:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-33:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-34:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-35:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-36:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-37:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-38:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-39:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-40:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-41:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-42:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-43:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-44:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-45:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-46:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-47:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-48:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-49:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-50:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-51:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-52:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-53:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-54:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-55:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-56:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-57:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-58:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-59:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-60:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-61:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-62:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-63:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-64:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-65:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-66:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-67:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-68:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-69:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-70:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-71:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-72:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-73:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-74:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-75:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-76:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-77:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-78:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-79:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-80:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-81:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-82:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-83:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-84:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-85:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-86:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-87:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-88:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-89:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-90:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-91:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-92:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-93:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-94:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-95:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-96:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-97:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-98:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-99:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-100:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-101:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-102:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-103:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-104:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-105:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-106:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-107:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-108:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-109:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-110:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-111:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-112:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-113:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-114:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-115:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-116:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-117:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-118:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-119:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-120:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-121:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-122:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-123:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-124:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-125:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-126:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-127:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-128:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-129:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-130:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-131:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-132:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-133:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-134:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-135:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-136:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-137:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-138:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-139:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-140:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-141:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-142:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-143:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-144:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-145:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-146:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-147:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-148:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-149:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-150:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-151:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-152:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-153:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-154:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-155:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-156:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-157:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-158:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-159:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-160:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-161:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-162:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-163:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-164:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-165:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-166:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-167:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-168:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-169:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-170:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-171:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-172:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-173:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-174:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-175:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-176:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-177:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-178:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-179:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-180:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-181:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-182:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-183:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-184:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-185:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-186:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-187:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-188:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-189:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-190:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-191:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-192:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-193:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-194:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-195:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-196:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-197:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-198:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-199:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-200:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-201:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-202:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-203:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-204:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-205:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-206:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-207:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-208:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-209:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-210:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-211:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-212:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-213:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-214:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-215:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-216:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-217:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-218:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-219:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-220:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-221:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-222:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-223:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-224:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-225:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-226:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-227:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-228:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-229:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-230:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-231:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-232:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-233:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-234:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-235:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-236:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-237:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-238:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-239:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-240:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-241:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-242:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-243:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-244:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-245:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-246:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-247:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-248:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-249:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-250:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-251:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-252:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-253:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-254:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-255:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-256:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-257:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-258:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-259:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-260:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-261:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-262:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-263:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-264:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-265:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-266:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-267:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-268:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-269:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-270:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-271:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-272:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-273:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-274:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-275:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-276:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-277:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-278:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-279:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-280:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-281:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-282:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-283:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-284:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-285:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-286:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-287:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-288:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-289:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-290:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-291:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-292:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-293:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-294:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-295:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-296:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-297:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-298:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-299:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-300:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-301:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-302:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-303:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-304:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-305:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-306:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-307:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-308:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-309:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-310:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-311:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-312:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-313:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-314:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-315:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-316:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-317:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-318:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-319:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-320:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-321:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-322:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-323:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-324:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-325:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-326:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-327:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-328:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-329:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-330:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-331:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-332:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-333:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-334:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-335:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-336:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-337:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-338:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-339:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-340:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-341:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-342:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-343:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-344:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-345:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-346:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-347:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-348:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-349:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-350:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-351:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-352:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-353:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-354:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-355:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-356:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-357:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-358:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-359:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-360:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-361:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-362:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-363:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-364:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-365:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-366:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-367:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-368:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-369:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-370:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-371:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-372:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-373:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-374:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-375:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-376:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-377:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-378:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-379:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-380:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-381:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-382:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-383:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   "MVC4-1-1-7-384:NEND,P:TMPER=15-MIN,PMSTATE=ON,DIRN=RCV"
   /* RTRV-PMMODE-VC4::MVC4-1-1-7-1&&-384:::NEND,RCV:TMPER=15-MIN [416] (536871001) */
;
"""

    MSG9 = """

   PLEASE-SET-SID-10980 16-05-01 01:13:16
M  103 COMPLD
   "MVC4-1-1-7-34,VC4:WR,T-SES-HOVC-15-MIN,NSA,05-01,11-49-06,NEND,RCV,15,15,15-MIN"
   /* RTRV-ALM-VC4::MVC4-1-1-7-34:::WR,T-SES-HOVC-15-MIN,NSA,NEND,RCV [103] (536871054) */
;"""


    MM = TL1message(MSG9)
    print(MM.decode("JSON"))
    #print(MM.get_cmd_attr_value("STM64AU4-1-1-13-1-36,MVC4-1-1-12-100", "1"))
    #print(MM.get_cmd_attr_value("STM64AU4-1-1-13-1-.*,MVC4-1-1-12-100", "1"))

    sys.exit(0)

    if True:
        MM = TL1message(MSG5)
        print(MM.decode("JSON"))
        print(MM.get_cmd_attr_value("MVC4-1-1-36-23", "TRC"))
        FILT = TL1check()
        FILT.add_aid("MVC4-1-1-36-33")
        FILT.add_aid("MVC4-1-1-36-23")
        FILT.add_aid("MVC4-1-1-36-49")
        FILT.add_aid("MVC4-1-1-36-3")
        FILT.add_pst("OOS-AU")
        FILT.add_sst("SGEO")
        FILT.add_sst("PMD")
        FILT.add_field("PTFTYPE", "MODVC4")
        FILT.add_field("TRC", "X010010011101010010010101110010")
        FILT.add_field("TRC", "PIPPO")
        FILT.debug()
        print(FILT.evaluate_msg(MM, sst='AND'))
    else:
        MM = TL1message(MSG6)
        print(MM.decode("JSON"))
        print(MM.get_cmd_attr_values("9"))
        print(MM.get_cmd_attr_value("9", 4))

    sys.exit(0)

    MM = TL1message(MSG3)
    print(MM.decode("JSON"))

    FILT = TL1check()
    FILT.add_field("PTFRATE", "MODVC4")
    FILT.debug()
    print(FILT.evaluate_msg(MM))

    print("FINE")

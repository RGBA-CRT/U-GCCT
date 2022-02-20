#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json
from typing import Text
from unicodedata import name


class TextTable:
    def __init__(self):
        self.name = ""
        self.address = 0
        self.type = 0

    def get_table(self):
        pass
    
    def get_text(self, id):
        pass

    def parse_stop(self):
        pass

    def parse(self, util, code):
        pass

class FixedLengthTable(TextTable):
    def __init__(self,text_table):
        self.name = text_table.name
        self.address = text_table.address
        self.type = text_table.type
        self.width = 0
        self.count = 0
        self.table = dict()
        self.table_idx = 0
        self.cur_text = ""
        self.cur_char_idx=0
    
    def get_table(self):
        return self.table
    
    def get_text(self, id):
        try:
            text = self.table[id]
        except KeyError as e:
            text = ("(OutOfIndex:0x{:0"+str(self.width*2)+"X})").format(id)
        return text


    def parse_stop(self):
        self.table[self.table_idx] = self.cur_text
        self.table_idx=self.table_idx+1
        self.cur_text=""
        self.cur_char_idx=0

    def parse(self, util, code):
        code_text, found =  util.get_text(code)

        self.cur_text  = self.cur_text + code_text
        self.cur_char_idx = self.cur_char_idx+1
        if(self.cur_char_idx >= self.width):
            self.parse_stop()

        if(self.table_idx > self.count):
            return False
        else:
            return True
            

class GameCodeManager:
    def __init__(self, generate_mode=False, check_duplicate=False):
        self.generate_mode = generate_mode
        self.check_duplicate = check_duplicate
        
        self.start = 0
        self.end = 0
        # byte_width = 0
        self.code_table = dict()
        self.text_tables = dict()

    def get_text(self, code):
        if self.generate_mode == True:
            raise Exception("not decode mode")
            
        try:
            text = self.code_table[code]
            found = True
        except KeyError as e:
            text = "({})".format(code)
            found = False
        return text, found

    def get_code(self, text):
        if self.generate_mode != True:
            raise Exception("not encode mode")

        found = True
        try:
            code = int(self.code_table[text], 16)
        except KeyError as e:
            if(' ' in self.code_table):
                code = int(self.code_table[' '], 16)
                found = False
            else:
                code = 0
                found = False

        return code, found

    def parse_text(self, text):
        # 互換用。\nが使えるのでそちら推奨
        if text == "[\\n]":
            return "\n"
        
        text=text.replace("\\n","\n")

        if text == "[SP]":
            return " "
        elif text == "[PRESS A]":
            return "[PRESS A]\n"
        elif text in {"[NULL]", "[SEQ]"}:
            return text
        else:
            return text

    def parse_row(self, row):
        try:
            # check text code
            int(row[0], 16)

            code = str.upper(row[0])
            text = self.parse_text(row[1])

            if (len(code) % 2):
                raise KeyError("Please describe the code in even digits. code:{}, text:{}".format(code,text))

            if self.generate_mode == False:
                key = code
                value = text
            else:
                key = text
                value = code

            if self.check_duplicate:
                if key in self.code_table:
                    raise KeyError("key {} has duplicated. old: {}, new: {}".format(
                        key, self.code_table[key], value))
                elif value in self.code_table.values():
                    raise KeyError("value {} has duplicated".format(value))

            self.code_table[key] = value

        except ValueError as e:
            opr = str.upper(row[0])
            if opr == "START":
                self.start = int(row[1], 16)
            elif opr == "END":
                self.end = int(row[1], 16)
            elif opr == "REM":
                pass
            elif opr == "TEXT_TABLE":
                self.add_table(row)
            # elif opr == "BYTE":
            #     self.byte_width = int(row[1])
            else:
                raise e

        return True
    
    def add_table(self, row):
        tbl=TextTable()
        tbl.name=row[1]
        tbl.address=int(row[2], 16)
        tbl.type=row[3]
        if(tbl.type == "FIXED_LENGTH"):
            fix_tbl = FixedLengthTable(tbl)            
            fix_tbl.width=int(row[4])
            fix_tbl.count=int(row[5])
            self.text_tables[tbl.name]=fix_tbl

        else:
            raise KeyError("Table type is invalid. type={}".format(tbl_type))
        

    def load(self, filename):
        with open(filename, newline='', encoding="utf-8") as csvfile:
            csv_table = csv.reader(csvfile, delimiter=',')
            line = 0
            for row in csv_table:
                # print("\"{}\"\t".format(row))
                try:
                    self.parse_row(row)
                except Exception as e:
                    print('csv warning: {}\n  line:{} \"{}\"'.format(
                        e, line, ",".join(row)))

                line += 1

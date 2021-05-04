#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import json


class GameCodeManager:
    start = 0
    end = 0
    # byte_width = 0
    code_table = dict()
    generate_mode = False
    check_duplicate = True

    def __init__(self, generate_mode=False, check_duplicate=False):
        self.generate_mode = generate_mode
        self.check_duplicate = check_duplicate

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
        if text == "[\\n]":
            return "\n"
        elif text == "[SP]":
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
            # elif opr == "BYTE":
            #     self.byte_width = int(row[1])
            else:
                raise e

        return True

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

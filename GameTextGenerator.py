#!/usr/bin/env python
# -*- coding: utf-8 -*-

from GameCodeUtil import GameCodeManager
import sys

if len(sys.argv) < 3:
    print("usage: {} game-code-def.csv to-convert-text".format(sys.argv[0]))
    exit()

filename = sys.argv[1]
text = sys.argv[2]

table = GameCodeManager(generate_mode=True, check_duplicate=False)
table.load(filename)


def print_code(code):
    code_text = ""
    disp = False
    bit_shift = 24

    while(bit_shift >= 0):
        digit = (code >> bit_shift) & 0xFF
        # print("c:{:02x} digit:{:02x}, bs:{}".format(code,digit,bit_shift))
        if disp | digit | (bit_shift == 0):
            code_text += "{:02X} ".format(digit)
            disp = True
        bit_shift -= 8
    return code_text


def detail_printer(char, code, found):
    print("char:{} code:{} {}".format(char, print_code(
        code), "" if found else " !!! code not found"))


def oneline_printer(char, code, found):
    print(print_code(code), end="")


def do_convert(text, printer):
    for char in text:
        code, found = table.get_code(char)
        printer(char, code, found)

    char = '[NULL]'
    code, found = table.get_code(char)
    printer(char, code, found)


do_convert(text, detail_printer)
print("\ncodes: ")
do_convert(text, oneline_printer)
print("")

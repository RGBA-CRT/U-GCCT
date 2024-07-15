#!/usr/bin/env python
# -*- coding: utf-8 -*-

# usage
# python3 -X utf8 target\inu_gba\inu.py "H:\My-File\ROM\GBA\犬夜叉\INU.gba" |tee target\inu_gba\SystemMessageTable.txt   

import sys
import datetime
import os
import re
import struct  
from typing import List
from enum import IntEnum

base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(base_dir)
from GameCodeUtil import GameCodeManager

class InuTableEntry:
    value: int
    abs_addr: int

class InuTable:
    name: str
    values: List[InuTableEntry] = []
    width: int
    file_offset: int

    def __init__(self):
        self.values = []

    def GetFileOffset(self, idx):
        return (self.values[idx].abs_addr & 0xFFFFFF)
    
    def PrintTable(self):
        print(self.name,hex(self.file_offset), "=================")
        for idx, entry in enumerate(self.values):   
            print(hex(idx), hex(entry.value), hex(entry.abs_addr))

class InuTableType(IntEnum):
    ABS = 0,
    REL32=1,
    REL16 = 2

    def GetWidth(self):
        if self == self.REL16:
            return 2
        else:
            return 4
        

def InuTableValueToAbs(type : InuTableType, base, idx, adr):
    if type == InuTableType.ABS:
        return adr
    elif type  == InuTableType.REL32:
        return (base + idx*4 + adr) | 0x08000000
    elif type  == InuTableType.REL16:
        return (base + idx*2 + adr) | 0x08000000
    else:
        return 0

def parse_dword_table(table_bytes, size):
    format = '<'+str(size)+'I'
    return list(struct.unpack(format, table_bytes))
def parse_short_table(table_bytes, size):
    format = '<'+str(size)+'H'
    return list(struct.unpack(format, table_bytes))

def load_raw_table(file, offset, size, entry_size=4):
    file.seek(offset)
    table = file.read(int(size*entry_size))
    if entry_size==4:
        return parse_dword_table(table, size)
    elif entry_size==2:
        return parse_short_table(table, size)
    
def load_table(file, name, offset, size, type : InuTableType):
    ret = InuTable()
    ret.width = type.GetWidth()
    ret.name = name
    ret.file_offset = offset
    # ret.values = List[InuTableEntry]=[]
    
    raw_table = load_raw_table(file, offset, size, ret.width)
    for i, v in enumerate(raw_table):
        entry = InuTableEntry()
        entry.value = v
        entry.abs_addr = InuTableValueToAbs(type, offset, i, v)
        # print(dir(ret))
        ret.values.append(entry)

    return ret


# def inu_offset_table_to_abs(table, base, entry_size=4):
#     for idx, entry in enumerate(table):
#         table[idx] = (base+idx*entry_size) + entry

# def print_inu_offset_table(table):
#     # real = base & 0x00FFFFFF
#     # print("base: ",hex(base), "real=", hex(real), type(table))
#     # print("idx\tval\taddr\toffset")
#     print(table.name,hex(table.file_offset), "=================")
#     for idx, entry in enumerate(table.values):
#         # adr = (base+idx*4) + entry
#         # print(hex(idx), hex(entry), hex(adr), hex(adr & 0xFFFFFF))   
#         print(hex(idx), hex(entry.value), hex(entry.abs_addr))

def get_text(codebook, buffer):
    end = len(buffer)
    i = 0
    prefix = ""
    ret = ""
    # todo: [Skip 0xNN %d times]
    while(i < end):
        pos = i
        b = buffer[i]

        code = "{}{:02X}".format(prefix, b)
        text, found = codebook.get_text(code)

        
        prefix = ""
        if not found:
            ret += ("[x{}]".format(code))

        elif text.startswith("[SEQ]"):
            prefix = code

        elif text == "[NULL]":
            break

        elif text.startswith("[CMD"):
            label = text[text.find(']')+1:]
            ret += ("[CMD:{},{}".format(code,label))

            if text.startswith("[CMD_W"):
                match = re.search(r'\d+', text)
                cmd_len = int(match.group())
                ret += (",arg:")

                # cmd_arg=infile.read(cmd_len)
                cmd_arg = buffer[i+1:i+cmd_len+1]
                space=False
                for a in cmd_arg:
                    if space: ret += (" ")
                    ret += (("{:02X}".format(a)))
                    space=True
                i += cmd_len

            ret += ("]")
        else:
            ret += text
        i+=1
        
    return ret

def run_text(file, codebook, offset):
    file.seek(offset)
    buffer = file.read(128)
    return get_text(codebook, buffer)


def main():
    csvpath = os.path.join(base_dir, "csv", "inu_utf8.csv")
    gamepath = sys.argv[1]
    # gamepath = "H:\My-File\ROM\GBA\犬夜叉\INU.gba"

    code_table = GameCodeManager(generate_mode=False, check_duplicate=False)
    code_table.load(csvpath)

    infile = open(gamepath, "rb")
    with infile:    
        RootTable = load_table(infile, "RootTable", 0x007dd63c, int(1128/4), InuTableType.ABS)
        # RootTable.PrintTable()

        MessageTableTable = load_table(infile, "MessageTableTable", RootTable.GetFileOffset(2), int(0x71), InuTableType.REL32)
        TextScriptTable = load_table(infile, "TextScriptTable", RootTable.GetFileOffset(8), int(256/2), InuTableType.REL16)
        
        # SystemMessageTable = load_table(infile, "SystemMessageTable", MessageTableTable.GetFileOffset(4), int(0x171), InuTableType.REL16)
        # tbl0 = load_table(infile, "0", MessageTableTable.GetFileOffset(0x09), int(0x300), InuTableType.REL16)
        #MessageTableTable 0xaab9c =================

        # TABLE0: 0xFF, 名前テーブル。キャラとか
        # TABLE1: 0xa4, アイテム名テーブル
        # TABLE2: 0xa4, アイテム名テーブル
        # TABLE3: 0xa4, アイテム説明テーブル
        # TABLE4: 0x171, システムメッセージ、タイトル画面とかデバッグとか
        # TABLE5: 0x1a5, システムメッセージ2，マップとかキャラのセリフとか
        # TABLE6: 0x1f, 小タイトル
        # TABLE7: 0xff, 勝利条件
        # TABLE8: 0x400～, 「マップ5、はじまり、はじまり」
        # TABLE11h: 0x200~, map1
        # TABLE1bh: 0x200~, last
        # TABLE1ch: 0x100~, last
        # TABLE28h: 0x255~, naraku]
        # TABLE29h: 0x4, 開発中
        # TABLE2ah: 0x4, 開発中
        tbl_list = [
            [0x00, "name", 0xFF],
            [0x01, "item_name", 0xa4],
            [0x02, "item_name", 0xa4],
            [0x03, "item_desc", 0xa4],
            [0x04, "sys_title", 0x171],
            [0x05, "sys_map", 0x1a5],
            [0x06, "arc_title", 0x1f],
            [0x07, "win", 0xFF],
            [0x08, "template", 0x4],
            [0x11, "map1", 0x200],
            [0x12, "map2", 0x200],
            [0x13, "map3", 0x200],
            [0x14, "map4", 0x200],
            [0x15, "map5", 0x200],
            [0x16, "map6", 0x200],
            [0x17, "map7", 0x200],
            [0x18, "map8", 0x200],
            [0x19, "map9", 0x200],
            [0x1A, "map10", 0x200],
            [0x1B, "map11", 0x200],
            [0x1C, "map12", 0x200],
            [0x1D, "map13", 0x200],
            [0x1E, "map14", 0x200],
            [0x1F, "map15", 0x200],
            [0x20, "map16", 0x200],
            [0x21, "map17", 0x200],
            [0x22, "map18", 0x200],
            [0x23, "map19", 0x200],
            [0x24, "map20", 0x200],
            [0x25, "map21", 0x200],
            [0x26, "map22", 0x200],
            [0x27, "map23", 0x200],
            [0x28, "map24", 0x255],
            [0x29, "map25_dummy", 0x200],

            [0x2e, "untitled", 0x200],
            [0x2f, "untitled", 0x200],
            # キャラのセリフっぽい
            [0x30, "untitled", 0x80],
            [0x31, "untitled", 0x80],
            [0x32, "untitled", 0x80],
            [0x33, "untitled", 0x80],
            [0x34, "untitled", 0x80],
            [0x35, "untitled", 0x80],
            
            [0x36, "untitled", 0x80],
            [0x37, "untitled", 0x80],
            [0x38, "untitled", 0x80],
            [0x39, "untitled", 0x80],
            [0x3a, "untitled", 0x80],
            [0x3b, "untitled", 0x80],
            [0x3c, "untitled", 0x80],
            [0x3d, "untitled", 0x80],
            [0x3e, "untitled", 0x80],
            [0x3f, "untitled", 0x80],
            [0x40, "untitled", 0x80],
            [0x41, "untitled", 0x80],
            [0x42, "untitled", 0x80],
            [0x43, "untitled", 0x80],
            [0x44, "untitled", 0x80],
            [0x45, "untitled", 0x80],
            [0x46, "untitled", 0x80],
            [0x47, "untitled", 0x80],

            [0x51, "untitled", 0x80],
            [0x52, "untitled", 0x80],
            [0x53, "untitled", 0x80],
            [0x54, "untitled", 0x80],
            [0x55, "untitled", 0x80],
            [0x56, "untitled", 0x80],
            [0x57, "untitled", 0x80],
            [0x58, "untitled", 0x80],
            [0x59, "untitled", 0x80],
            [0x5a, "untitled", 0x80],
            [0x5b, "untitled", 0x80],
            [0x5c, "untitled", 0x80],
            [0x5d, "untitled", 0x80],
            [0x5e, "untitled", 0x80],
            [0x5f, "untitled", 0x80],
            [0x60, "untitled", 0x80],
            [0x61, "untitled", 0x80],
            [0x62, "untitled", 0x80],
            [0x63, "untitled", 0x80],
            [0x64, "untitled", 0x80],
            [0x65, "untitled", 0x80],
            [0x66, "untitled", 0x80],
            [0x67, "untitled", 0x80],
        ]


        testTbl = load_table(infile, "unknown", 0x6ab1ff, int(256/2),
                              InuTableType.REL16)

        RootTable.PrintTable()
        # SystemMessageTable.PrintTable()
        MessageTableTable.PrintTable()
        TextScriptTable.PrintTable()
        testTbl.PrintTable()

        # for i,v in enumerate(SystemMessageTable.values):
        #     print(hex(i), hex(v.value), hex(v.abs_addr), "================")
        #     print(run_text(infile, code_table, v.abs_addr & 0xFFFFFF))
        #     print()

        # for i,v in enumerate(tbl0.values):
        #     print(hex(i), hex(v.value), hex(v.abs_addr), "================")
        #     print(run_text(infile, code_table, v.abs_addr & 0xFFFFFF))
        #     print()

        for tbl_info in tbl_list:
            filename = "inu_txt_{:02x}_{}.txt".format(tbl_info[0], tbl_info[1])
            print(filename)
            f = open(os.path.join(os.path.dirname(__file__), filename),"w")

            tbl = load_table(infile, tbl_info[1], MessageTableTable.GetFileOffset(tbl_info[0]),
                            int(tbl_info[2]), InuTableType.REL16)
            for i,v in enumerate(tbl.values):
                print(hex(i), hex(v.value), hex(v.abs_addr), "================", file=f)
                print(run_text(infile, code_table, v.abs_addr & 0xFFFFFF), file=f)
                print(file=f)

            f.close()


        
main()

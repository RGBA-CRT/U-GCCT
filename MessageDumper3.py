#!/usr/bin/env python
# -*- coding: utf-8 -*-

from GameCodeUtil import GameCodeManager
import sys
import datetime
import os
import re
buflen = 100*1024

if len(sys.argv) < 3:
    print("usage: {} game-code-def.csv game-file.rom".format(sys.argv[0]))
    exit()

csvpath = sys.argv[1]
gamepath = sys.argv[2]

table = GameCodeManager(generate_mode=False, check_duplicate=False)
table.load(csvpath)


def print_table_256(table, prefix):
    seq_list = []

    for iy in range(0, 256, 16):
        printable = False
        for ix in range(0, 16):
            code = '{}{:02X}'.format(prefix, iy+ix)
            text, found = table.get_text(code)
            if found:
                printable = True
                break

        if printable:
            print("[{}{:02X}]\t".format(prefix, iy), end="")
            for ix in range(0, 16):
                code = '{}{:02X}'.format(prefix, iy+ix)
                text, found = table.get_text(code)
                print("{}\t".format(text.replace("\n", "\\n")), end="")

                if text == "[SEQ]":
                    seq_list.append(code)

            print("")
    print("")

    for seq in seq_list:
        print_table_256(table, seq)


def print_table(table):
    print(
        "  \t[x0]\t[x1]\t[x2]\t[x3]\t[x4]\t[x5]\t[x6]\t[x7]\t[x8]\t[x9]\t[xA]\t[xB]\t[xC]\t[xD]\t[xE]\t[xF]")
    print_table_256(table, "")

def create_text_table(util, file):    
    print(util.text_tables.keys())
    for key in util.text_tables.keys():
        text_table = util.text_tables[key]
        print("table: {} in 0x{:X}".format(text_table.name, text_table.address))
        file.seek(text_table.address)
        offset=0
        while(True):
            buf = infile.read(1)
            if len(buf) == 0:
                text_table.parse_stop()
                break
            # print("{:X}: {:02X}".format(offset+text_table.address,buf[0]))
            code = "{:02X}".format(buf[0])
            ret = text_table.parse(util, code)
            if(ret == False):
                break
            offset=offset+1

        text_table_dict = text_table.get_table()
        for i in text_table_dict.keys():
            print(" {:04X}: {}".format(i, text_table.get_text(i)))


        

print_table(table)

infile_stat = os.stat(gamepath)

infile = open(gamepath, "rb")

create_text_table(table, infile)

outfile = open("{}_dump.txt".format(gamepath), "w", encoding="utf-8")
outfile.write("MessageDumper v3.0 \t Programmed by RGBA_CRT 2021\n")
outfile.write("dump date: {}\n".format(str(datetime.datetime.now())))
outfile.write("code define file: {}\n".format(csvpath))
outfile.write("=================================================\n")

buf_pos = table.start
infile.seek(buf_pos)

end = table.end
if end == 0:
    end = infile_stat.st_size

print("start: {:08X}".format(table.start))
print("end  : {:08X}".format(end))

start_time = datetime.datetime.now()

prefix = ""
while(1):
    offset = infile.tell()
    buffer = infile.read(buflen)
    if len(buffer) == 0:
        break

    i = 0
    # todo: [Skip 0xNN %d times]
    while(i < len(buffer)):
        pos = offset + i
        if pos > end:
            break
        b = buffer[i]

        code = "{}{:02X}".format(prefix, b)
        text, found = table.get_text(code)

        
        prefix = ""
        if text.startswith("[SEQ]"):
            prefix = code

        elif text == "[NULL]":
            outfile.write("\n\n\n0x{:08X}:\n".format(pos+1))

        elif text.startswith("[CMD"):
            label = text[text.find(']')+1:]
            outfile.write("[CMD:{},{}".format(code,label))

            if text.startswith("[CMD_W"):
                match = re.search(r'\d+', text)
                cmd_len = int(match.group())
                outfile.write(",arg:")

                # cmd_arg=infile.read(cmd_len)
                cmd_arg = buffer[i+1:i+cmd_len+1]
                space=False
                for a in cmd_arg:
                    if space: outfile.write(" ")
                    outfile.write("{:02X}".format(a))
                    space=True
                i += cmd_len

            outfile.write("]")

        elif text.startswith("[REF"):
            args = text[text.find('[')+1:text.find(']')].split('/')
            
            idx_len = int(args[1])
            table_name = args[2]
            idx_mask = int(args[3], 16)
            idx_offset = int(args[4])

            if idx_len==1:
                idx_raw = int(buffer[i+1])
            elif idx_len==2:
                idx_raw = int(buffer[i+2]) | int(buffer[i+1])<<8
            else:
                # 本当はパース時にチェックしたいが...
                raise ValueError("[REF] index error")
            
            index = (idx_raw + idx_offset) & idx_mask
            text = table.text_tables[table_name].get_text(index)
            # print("arglist:{} raw_index={:08X}, index={:5d}(0x{:04X}), text={}".format(args,idx_raw,index,index,text)," buf=",buffer[i+1:i+idx_len+1])
            outfile.write("[REF:{},arg:".format(code))
            space=False
            for b in buffer[i+1:i+1+idx_len]:
                if space: outfile.write(" ")
                outfile.write("{:02X}".format(b))
                space=True
            # outfile.write(",{},{},{:08X}]".format(text,index,idx_raw))
            # outfile.write(",idx:{:X},{}]".format(index,text))
            outfile.write(",{}]".format(text))
            i += idx_len
        else:
            outfile.write(text)

        i += 1

    if infile.tell() > end:
        break

    process_size = end-table.start
    process_pos = offset-table.start
    print("processing {}%\t\t\r".format(
        int((process_pos*100)/process_size)))

    # break

end_time = datetime.datetime.now()
print("processing time: ", end_time-start_time)

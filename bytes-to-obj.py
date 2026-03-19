import sys
import re

# utils
def to_bytestring_from_int_with_size(number: int, sizeof_bytestring: int):
    return number.to_bytes(sizeof_bytestring, 'little', signed=False).hex()

def to_bytestring_from_str(string: str):
    return ''.join(hex(ord(c))[2:] + ' ' for c in string)

def to_bytestring_from_str_with_size(string: str, sizeof_bytestring: int):
    bytestring = ''.join(hex(ord(c))[2:] for c in string)
    if len(string) > sizeof_bytestring:
        raise Exception
    for _ in range(sizeof_bytestring - len(string)):
        bytestring += '00'
    return bytestring




# structs
# https://wiki.osdev.org/COFF
class COFFObjectFile:
    def __init__(self, text_no_exts: str, externs: list[str], occurences: dict):
        len_of_occurences = 0
        for key in occurences.keys():
            len_of_occurences += len(occurences[key])
        text_section_shift = 20 + 0 + 40 + len_of_occurences * 10
        true_sizeof_text = int((len(text_no_exts) + 1) / 3)
        f_symptr = text_section_shift + true_sizeof_text + 0
        f_nsyms = 6 + len(externs)
        file_header_data = FileHeader(f_symptr, f_nsyms).data
        text_section_header_data = TextSectionHeader(
            true_sizeof_text, 0x3C, 0x3C + true_sizeof_text, len(externs)).data
        text_section_data_data = TextSectionData(text_no_exts).data
        r_vaddr = []
        r_symndx = []
        # redo me
        for i, occur in enumerate(occurences.values()):
            for o in occur:
                r_vaddr.append(o)
                r_symndx.append(5 + i)
        reloc_entries_data = RelocationEntries(r_vaddr, r_symndx).data
        symbol_table_data = SymbolTable(externs).data
        string_table_data = StringTable(f_symptr, f_nsyms, externs).data

        self.data = file_header_data + text_section_header_data + text_section_data_data + \
            reloc_entries_data + symbol_table_data + string_table_data

class FileHeader:
    def __init__(self, f_symptr: int, f_nsyms: int):
        self.data = '64 86 01 00 00 00 00 00 ' + to_bytestring_from_int_with_size(f_symptr, 4) + \
            ' ' + to_bytestring_from_int_with_size(f_nsyms, 4) + ' 00 00 00 00 '

# have no need in that header
class OptionalHeader:
    pass

class TextSectionHeader:
    def __init__(self, s_size: int, s_scnptr: int, s_relptr: int, s_nreloc: int):
        self.data = '2e 74 65 78 74 00 00 00 00 00 00 00 00 00 00 00 ' + to_bytestring_from_int_with_size(s_size, 4) + \
        ' ' + to_bytestring_from_int_with_size(s_scnptr, 4) + to_bytestring_from_int_with_size(s_relptr, 4) + ' 00 00 00 00 ' + \
        to_bytestring_from_int_with_size(s_nreloc, 2) + ' 00 00 20 00 50 60 '

class TextSectionData:
    def __init__(self, text_bytes):
        self.data = text_bytes

class RelocationEntries:
    def __init__(self, r_vaddr: list, r_symndx: list):
        if len(r_vaddr) != len(r_symndx):
            raise Exception
        self.data = ''
        for i, _ in enumerate(r_vaddr):
            self.data += to_bytestring_from_int_with_size(r_vaddr[i], 4) + ' ' + \
            to_bytestring_from_int_with_size(r_symndx[i], 4) + ' 04 00 '

# have no need in that header
class LineNumberEntries:
    pass

class SymbolTable:
    def __init__(self, externs):
        self.data = '2e 66 69 6c 65 00 00 00 00 00 00 00 fe ff' + \
        '00 00 67 01 6d 61 69 6e 2e 73 00 00 00 00 00 00 00 00 00 00 00 00 2e 74 65 78 74 00 00 00' + \
        '00 00 00 00 01 00 00 00 03 01 22 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 2e 61' + \
        '62 73 6f 6c 75 74 00 00 00 00 ff ff 00 00 03 00 '
        last_externs_size = 4  # has to be 4 at beginning
        for i, extern in enumerate(externs):
            self.data += '00 00 00 00 ' + to_bytestring_from_int_with_size(last_externs_size, 4) + \
            ' 00 00 00 00 00 00 00 00 02 00 '
            last_externs_size += len(extern) + 1
        self.data += '73 74 61 72 74 00 00 00 00 00 00 00 01 00 00 00 02 00'

class StringTable:
    def __init__(self, f_symptr: int, f_nsyms: int, symbol_names: list[str]):
        self.base_offset = f_symptr + f_nsyms * 18
        symbol_count = 4
        symbols = ''
        for name in symbol_names:
            symbol_count += len(name) + 1
            symbols += to_bytestring_from_str(name) + ' 00'
        self.data = ''
        if symbol_names:
            self.data = to_bytestring_from_int_with_size(symbol_count, 4) + symbols





# 
def main():
    filename = sys.argv[1]
    try:
        file = open(filename, "r")
    except (FileNotFoundError, IOError):
        print("Cannot open file! Usage: " +
            f"{sys.argv[0]} input_filename")
        file.close()
        return
    
    contents = file.read()
    file.close()

    text_len = to_bytestring_from_int_with_size(len(contents), 4)

    contents = remove_comments(contents)

    contents = contents.replace('\n', ' ')
    # replace all multiple spaces with one
    contents = re.sub(r'\s+', ' ', contents)
    contents += ' '

    contents, occurences = get_externs_from_string(contents)
    contents = strings_into_bytes(contents)
    externs = list(occurences.keys())

    contents = contents[:-1]  # delete last ' '

    coff = COFFObjectFile(contents, externs, occurences)
    
    plain_obj_str = coff.data

    plain_obj_str = plain_obj_str.replace(' ', '')
    plain_obj_bytes = []
    for i in range(0, len(plain_obj_str), 2):
        two_chars = plain_obj_str[i:i+2]
        one_byte = int(two_chars, 16)
        plain_obj_bytes.append(one_byte)


    with (open('obj.obj', 'ab')) as output_file:
        output_file.truncate(0) # clear file
        bytes_to_write = bytes(plain_obj_bytes)
        output_file.write(bytes_to_write)


# more utils
def get_externs_from_string(contents: str):
    occurences = {}
    matches = re.findall("[eE]8 (.*?) ", contents)
    funcs_symbols = [m for m in matches if len(m) > 2]
    for sym in funcs_symbols:
        split_contents = contents.split(' ')
        sym_pos = split_contents.index(sym)
        if sym in occurences:
            occurences[sym].append(sym_pos)
        else:
            occurences[sym] = [sym_pos]
        contents = contents.replace(sym, '00 00 00 00', 1)
    return contents, occurences

def strings_into_bytes(contents):
    string_pattern = r'\"(.*?)\"'
    strings_found = re.findall(string_pattern, contents)
    for string in strings_found:
        contents = contents.replace('"' + string + '"', to_bytestring_from_str(string))
        idk = 0
    return contents

def remove_comments(contents):
    contents = re.sub(r'#.*?\n', '', contents)
    contents = re.sub(r'#.*', '', contents)   # for end-of-string removal
    return contents


if __name__ == '__main__':
    main()
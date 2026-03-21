import sys
import re

# utils
def to_bytestring_from_int_with_size(number: int, sizeof_bytestring: int):
    bytestring = number.to_bytes(sizeof_bytestring, 'little', signed=False).hex()
    bytestring_spaced = ''.join([b + bytestring[i+1] + ' ' for i, b in enumerate(bytestring[::2])])
    return bytestring_spaced

def to_bytestring_from_str(string: str):
    return to_bytestring_from_str_with_size(string, len(string))

def to_bytestring_from_str_with_size(string: str, sizeof_bytestring: int):
    bytestring = ''.join(hex(ord(c))[2:] + ' ' for c in string)
    if len(string) > sizeof_bytestring:
        raise Exception
    for _ in range(sizeof_bytestring - len(string)):
        bytestring += '00 '
    return bytestring




# structs
# https://wiki.osdev.org/COFF
# https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
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
        Machine = '64 86 ' # 0x8664. this means machine is x64
        NumberOfSections = '01 00 ' # 0x000x number of sections in total
        TimeDateStamp = '00 00 00 00 ' # time and date of build. zeroes here
        PointerToSymbolTable = to_bytestring_from_int_with_size(f_symptr, 4)
        NumberOfSymbols = to_bytestring_from_int_with_size(f_nsyms, 4)
        SizeOfOptionalHeader = '00 00 ' # 0x0000. must be zero for object files
        Characteristics = '00 00 ' # 0x0000. unknown flag

        self.data = Machine + NumberOfSections + TimeDateStamp + \
            PointerToSymbolTable + NumberOfSymbols + SizeOfOptionalHeader + \
            Characteristics

# have no need in that header in object file
class OptionalHeader:
    pass

class TextSectionHeader:
    def __init__(self, s_size: int, s_scnptr: int, s_relptr: int, s_nreloc: int):
        Name = to_bytestring_from_str_with_size('.text', 8)
        VirtualSize = '00 00 00 00 ' # 0x0000. should be set to zero for object files
        VirtualAddress = '00 00 00 00 ' # 0x0000. for simplicity should be set to zero
        SizeOfRawData = to_bytestring_from_int_with_size(s_size, 4)
        PointerToRawData = to_bytestring_from_int_with_size(s_scnptr, 4)
        PointerToRelocations = to_bytestring_from_int_with_size(s_relptr, 4)
        PointerToLinenumbers = '00 00 00 00 ' # 0x0000. COFF debugging information is deprecated
        NumberOfRelocations = to_bytestring_from_int_with_size(s_nreloc, 2)
        NumberOfLinenumbers = '00 00 ' # 0x0000. COFF debugging information is deprecated
        Characteristics = '20 00 00 60 ' # 0x60000020
        # this means following flags set:
        # IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ

        self.data = Name + VirtualSize + VirtualAddress + SizeOfRawData + \
                PointerToRawData + PointerToRelocations + PointerToLinenumbers + \
                NumberOfRelocations + NumberOfLinenumbers + Characteristics

class TextSectionData:
    def __init__(self, text_bytes):
        self.data = text_bytes

class RelocationEntries:
    def __init__(self, r_vaddr: list, r_symndx: list):
        if len(r_vaddr) != len(r_symndx):
            raise Exception
        self.data = ''
        for i, _ in enumerate(r_vaddr):
            # offset from the beginning of the section, plus the value of the section's RVA/Offset field
            VirtualAddress = to_bytestring_from_int_with_size(r_vaddr[i], 4)
            # a zero-based index into the symbol table
            SymbolTableIndex = to_bytestring_from_int_with_size(r_symndx[i], 4)
            Type = '04 00 ' # 0x0004. means IMAGE_REL_AMD64_REL32 flag set
            self.data += VirtualAddress + SymbolTableIndex + Type

# have no need in that header (deprecated)
class LineNumberEntries:
    pass

class SymbolTable:
    def __init__(self, externs):
        self.data = ''

        # .file symbol
        self.make_symbol_bytes( to_bytestring_from_str_with_size('.file', 8), \
                          '00 00 00 00 ', 'FE FF ', '00 00 ', '67 ', '01 ' )
        
        # main.s symbol
        self.make_symbol_bytes( to_bytestring_from_str_with_size('main.s', 8), \
                          '00 00 00 00 ', '00 00 ', '00 00 ', '00 ', '00 ' )
        
        # .text symbol
        self.make_symbol_bytes( to_bytestring_from_str_with_size('.text', 8), \
                          '00 00 00 00 ', '01 00 ', '00 00 ', '03 ', '01 ' )
        
        # unknown symbol
        self.make_symbol_bytes( '22 00 00 00 01 00 00 00 ', \
                          '00 00 00 00 ', '01 00 ', '00 00 ', '03 ', '01 ' )
        
        # .absolut symbol
        self.make_symbol_bytes( to_bytestring_from_str_with_size('.absolut', 8), \
                          '00 00 00 00 ', 'FF FF ', '00 00 ', '03 ', '00 ' )
        
        # 
        last_externs_size = 4  # has to be 4 at beginning
        for i, extern in enumerate(externs):
            self.make_symbol_bytes( '00 00 00 00 ' + to_bytestring_from_int_with_size(last_externs_size, 4), \
                                   '00 00 00 00 ', '00 00 ', '00 00 ', '02 ', '00 ' )
            last_externs_size += len(extern) + 1
        
        # start symbol
        self.make_symbol_bytes( to_bytestring_from_str_with_size('start', 8), \
                          '00 00 00 00 ', '01 00 ', '00 00 ', '02 ', '00 ' )
        

    def make_symbol_bytes(self, Name, Value, SectionNumber, Type, StorageClass, NumberOfAuxSymbols):
        self.data += Name + Value + SectionNumber + Type + StorageClass + NumberOfAuxSymbols        

class StringTable:
    def __init__(self, f_symptr: int, f_nsyms: int, symbol_names: list[str]):
        symbol_count = 4  # padding
        symbols = ''
        for name in symbol_names:
            symbol_count += len(name) + 1
            symbols += to_bytestring_from_str(name) + '00 '
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
            f"{sys.argv[0]} <input_filename>")
        file.close()
        return
    
    contents = file.read()
    file.close()

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
    matches = re.findall(r"[eE]8 (.*?) ", contents)
    funcs_symbols = [m for m in matches if len(m) > 2] # don't take single bytes
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
    return contents

def remove_comments(contents):
    contents = re.sub(r'#.*?\n', '', contents)
    contents = re.sub(r'#.*', '', contents)   # for end-of-string removal
    return contents


if __name__ == '__main__':
    main()
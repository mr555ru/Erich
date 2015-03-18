# -*- coding: utf-8 -*-

#    Copyright 2015 mr555ru

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import lexical
from lexical import corellated_table

TOKEN_INTEGER = 1
TOKEN_IDENTIFYER = 2
TOKEN_ONE_LITER_DELIMITER = 3
TOKEN_2L_DELIMITER = 4
TOKEN_STRING = 5
TOKEN_KEYWORD = 6
TOKEN_EOSTRING = 7
TOKEN_EOFILE = 8

primitive_types = ["int", "char", "string", "boolean"]
primitive_types1 = tuple([(TOKEN_KEYWORD, i) for i in primitive_types])

VAR_INT = 1 #0 in assembly
VAR_CHAR = 2
VAR_BOOL = 3
VAR_STRING = 4 #1 in assembly
NO_VAR = 0

primitive_types_dict = {"int":VAR_INT, "char":VAR_CHAR, "boolean":VAR_BOOL, "string":VAR_STRING}
primitive_types_dict2 = {VAR_INT:"int", VAR_CHAR:"char", VAR_BOOL:"boolean", VAR_STRING:"string", NO_VAR:"ERROR PLZ CHECK ME"}

variables = {} #name: type
arrays = {} #name: (type, length)

all_constants = []

STRING_LENGTH = 255

CONSTANTS_COUNTER = 1
PROCEDURE_COUNTER = 1
FORS_COUNTER = 1


dict_first = {"while": ((TOKEN_KEYWORD, "while"),), #TODO MAKE IT KEYWORDS
              "for": ((TOKEN_KEYWORD, "for"),),
              "if": ((TOKEN_KEYWORD, "if"),),
              "array_declaration": ((TOKEN_KEYWORD, "array"),),
              "dowhile": ((TOKEN_KEYWORD, "do"),),
              "brackets": ((TOKEN_ONE_LITER_DELIMITER, "{"),),
              "procedure": ((TOKEN_KEYWORD, "print"), (TOKEN_KEYWORD, "write"), (TOKEN_KEYWORD, "read"), (TOKEN_KEYWORD, "examine"),
                            (TOKEN_KEYWORD, "to_str"), (TOKEN_KEYWORD, "to_int"), (TOKEN_KEYWORD, "to_char"),
                            (TOKEN_KEYWORD, "asm"), (TOKEN_KEYWORD, "to_bool")),
              "expression": ((TOKEN_IDENTIFYER, None),) + primitive_types1,
              "empty_codestring": ((TOKEN_EOSTRING, None),(TOKEN_ONE_LITER_DELIMITER, "}")),
              "multiline_comment": ((TOKEN_STRING, None),),
              "codestring": ((TOKEN_KEYWORD, "while"),(TOKEN_KEYWORD, "for"),(TOKEN_KEYWORD, "if"),(TOKEN_KEYWORD, "for"),
                             (TOKEN_KEYWORD, "do"),(TOKEN_ONE_LITER_DELIMITER, "{"),(TOKEN_IDENTIFYER, None), (TOKEN_EOSTRING, None)),
              "array_const": ((TOKEN_ONE_LITER_DELIMITER, "["),)}
             

dict_follow = {"expression2": ((TOKEN_EOSTRING, None),(TOKEN_ONE_LITER_DELIMITER, ","),
                               (TOKEN_ONE_LITER_DELIMITER, "}"),(TOKEN_ONE_LITER_DELIMITER, ")"),
                               (TOKEN_ONE_LITER_DELIMITER, ":"),(TOKEN_KEYWORD, "to"),(TOKEN_KEYWORD, "step")) + dict_first["codestring"],
               "text": ((TOKEN_EOFILE, None), (TOKEN_ONE_LITER_DELIMITER, "}")),
               "array_const": ((TOKEN_ONE_LITER_DELIMITER, "]"),)}
# = {"text": ((TOKEN_EOFILE, None))} #procedure_name, token_type, value (None if doesn't matter)

class Travelling_Data:
    """Data that is used in process of syntax analysis.
    This includes: current token_type and token_number, source file object,
                   string and position,
                   string no.,
                   """
    
    def __init__(self, token_type, token_number, source, string, position, string_index, output_file):
        self.token_type = token_type
        self.token_number = token_number
        self.source = source
        self.string = string
        self.position = position
        self.string_index = string_index
        self.output_files = [output_file]
        self.output_index = 0
        self.jumps_counter = 1
        self.terminated = False
        self.argument = {}
        self._variables = ""
        
    def lexical_scan(self):
        """wrap-up of the lexical.Scan"""
        values = lexical.Scan(self.source, self.string, self.position)
        if values is None or self.terminated:
            self.token_type = TOKEN_EOFILE
            self.token_number = None
        else:
            self.token_type, self.token_number, self.string, self.position = values
            
        if self.token_type == TOKEN_EOSTRING:
            self.string_index += 1
        
        
    def get_token_value(self):
        """Get token value from token_type and token_number in token tables
        (system of token tables was a requirement, could be done easier ofc)
        """
        return get_token_value(self.token_type, self.token_number)
    
    def write(self, string):
        """Write line of asm-code to file."""
        if not self.terminated:
            self.output_files[0].write(string)
            self.output_files[0].write("\n")
            
    def write_label(self, string):
        """Write asm label to file.
        Attribute string is label's name.
        """
        if not self.terminated:
            self.output_files[0].write(string)
            self.output_files[0].write(":\n")
        
    def close(self):
        """Close all files."""
        self.source.close()
        for output_file in self.output_files:
            output_file.close()
        
    def terminate(self, string):
        """Terminate the execution of syntax analyser with raising the flag
        self.terminated. This is used when error occurs."""
        if not self.terminated:
            print string
            self.terminated = True
            
    def reset_argument(self):
        self.argument = {}
            
    def set_argument(self,keyword,value):
        """For custom arguments. Might not be used currently :S"""
        self.argument[keyword] = value
    
    def get_argument(self, keyword):
        try:
            return self.argument[keyword]
        except KeyError:
            return None
        
    def temp_output(self):
        newfile = open('temp%d.erc' % self.output_index, 'w+')
        self.output_index += 1
        self.output_files = [newfile] + self.output_files
        
    def incorporate(self, procname):
        if len(self.output_files) == 1:
            return False
        self.output_files[0].seek(0)
        self.output_files[1].write("jmp jump_%d\n" % self.jumps_counter)
        self.output_files[1].write("\n:%s\n" % procname)
        for line in self.output_files[0]:
            self.output_files[1].write(line)
        self.output_files[1].write("ret\n\n:jump_%d\n" % self.jumps_counter)
        self.jumps_counter += 1
        self.output_files[0].close()
        self.output_files = self.output_files[1:]
        return True
        
    def write_variable(self, string):
        """Save correct asm variable string for future use.
        Needed to write all variables in the end of asm-file."""
        self._variables += string + "\n"
        
    
    def execute_variables(self):
        """Write all asm variable strings. Used once at the end of the asm-file creating."""
        self.write(self._variables)
        
# HELPER FUNCTIONS

def get_token_value(token_type, token_number):
    if token_type == TOKEN_EOSTRING or token_type == TOKEN_EOFILE:
        return None
    else:
        return corellated_table[token_type][token_number]

def in_follow(procedure_name, token_type, token_number):
    expected_tokens = dict_follow[procedure_name]
    flag = False
    token_value = get_token_value(token_type, token_number)
    for expected_token in expected_tokens:
        if expected_token[0] == token_type:
            if expected_token[1] is None or expected_token[1] == token_value:
                flag = True
                break
    return flag
    
def in_first(procedure_name, token_type, token_number): #TODO DRY
    expected_tokens = dict_first[procedure_name]
    flag = False
    token_value = get_token_value(token_type, token_number)
    for expected_token in expected_tokens:
        if expected_token[0] == token_type:
            if expected_token[1] is None or expected_token[1] == token_value:
                flag = True
                break
    return flag

operators = [(TOKEN_KEYWORD, "and"),
             (TOKEN_KEYWORD, "or"),
             (TOKEN_KEYWORD, "xor"),
             (TOKEN_2L_DELIMITER, '>='),
             (TOKEN_2L_DELIMITER, '<='),
             (TOKEN_2L_DELIMITER, '=='),
             (TOKEN_2L_DELIMITER, '!='),
             (TOKEN_ONE_LITER_DELIMITER, '+'),
             (TOKEN_ONE_LITER_DELIMITER, '-'),
             (TOKEN_ONE_LITER_DELIMITER, '*'),
             (TOKEN_ONE_LITER_DELIMITER, '/'),
             (TOKEN_ONE_LITER_DELIMITER, '>'),
             (TOKEN_ONE_LITER_DELIMITER, '<'),
             (TOKEN_ONE_LITER_DELIMITER, '?'),]

operators_return_boolean = ['and', 'or', 'xor', '>=', '<=', '==', '!=', '>', '<']
operators_return_int = ['+', '-', '*', '/', '\\']

def save_const(name):
    if name not in all_constants:
        all_constants.append(name)
        

def check_pushed_int(data):
    global PROCEDURE_COUNTER
    data.write("pop [r8w]")
    data.write("cmp [r8w], 0")
    ok_mark = "@type_%d_ok" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    data.write("je %s" % ok_mark)
    data.write("push %d" % data.string_index)
    data.write("jmp @ERROR_ASSIGN_STRING_TO_INTEGER") #data.terminate("Symantic error on line %d: trying to assign non-array value to array variable" % data.string_index)
    data.write_label(ok_mark)
    
def check_pushed_string(data):
    global PROCEDURE_COUNTER
    data.write("pop r8w")
    data.write("cmp [r8w], 1")
    ok_mark = "@type_%d_ok" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    data.write("je %s" % ok_mark)
    data.write("push %d" % data.string_index)
    data.write("jmp @ERROR_ASSIGN_STRING_TO_INTEGER") #data.terminate("Symantic error on line %d: trying to assign non-array value to array variable" % data.string_index)
    data.write_label(ok_mark)
    

def error_msg(data, name, msg):
    msg = " " + msg
    global PROCEDURE_COUNTER
    data.write_label(name)
    data.write("pop cx")
    data.write("mov [r9w], 10")
    msg1 = "Error:"
    data.write("mov ah, 2h")
    for c in msg1:
        data.write("mov dx, %d;%s" % (ord(c), c))
        data.write("int 21h")
    
    """data.write("mov ax, cx")
    repeat_mark = "@get_%d" % PROCEDURE_COUNTER
    repeat_mark2 = "@get2_%d" % PROCEDURE_COUNTER
    repeat_mark3 = "@out_%d" % PROCEDURE_COUNTER
    repeat_mark4 = "@out2_%d" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    data.write("push -1")
    data.write("mov bx,0")
    data.write_label(repeat_mark)
    data.write("mov dx,0")
    data.write("div [r9w]")
    data.write("mov concatenator[bx], dx")
    data.write("inc bx")
    data.write("cmp ax, 0")
    data.write("jne %s" % repeat_mark)
    data.write("mov cx, 1")
    data.write_label(repeat_mark2)
    data.write("mov di, cx")
    data.write("push concatenator[di-1]")
    data.write("inc cx")
    data.write("cmp cx, bx")
    data.write("jne %s" % repeat_mark2)
    data.write("mov ah, 2h")
    data.write_label(repeat_mark3)
    data.write("pop dx")
    data.write("cmp dx,-1")
    data.write("je %s" % repeat_mark4)
    data.write("add dl, '0'")
    data.write("int 21h")
    data.write("jmp %s" % repeat_mark3)
    data.write_label(repeat_mark4)"""
    
    for c in msg:
        data.write("mov dx, %d;%s" % (ord(c), c))
        data.write("int 21h")
        
    data.write("int 20h")
    
    
    
    

# MAIN FUNCTIONS

def text(data):
    data = codestring(data)
    while not in_follow("text", data.token_type, data.token_number):
        if data.token_type == TOKEN_EOSTRING:
            data.lexical_scan()
        else:
            data.terminate("Error on line %d: EOSTRING not found where expected" % data.string_index)
        data = codestring(data)
    return data
    
def codestring(data):
    global CONSTANTS_COUNTER
    data.write("; ===CODE STRING # %d===" % data.string_index)
    if in_first("while", data.token_type, data.token_number):
        data = code_while(data)
    elif in_first("for", data.token_type, data.token_number):
        data = code_for(data)
    elif in_first("if", data.token_type, data.token_number):
        data = code_if(data)
    elif in_first("dowhile", data.token_type, data.token_number):
        data = dowhile(data)
    elif in_first("procedure", data.token_type, data.token_number):
        data = procedure(data)
    elif in_first("array_declaration", data.token_type, data.token_number):
        data = array_declaration(data)
    elif in_first("brackets", data.token_type, data.token_number):
        data.lexical_scan() # throws out first bracket
        data = text(data)
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "}":
            data.lexical_scan()
        else:
            data.terminate("Error on line %d: Closing bracket } not found where expected" % data.string_index)
    elif in_first("expression", data.token_type, data.token_number):
        data = expression(data)
    elif in_first("multiline_comment", data.token_type, data.token_number):
        data.lexical_scan()
    elif in_first("empty_codestring", data.token_type, data.token_number):
        pass
    else:
        data.terminate("Error on line %d: Cannot identify this code string %s" % (data.string_index, data.get_token_value()))
        data.lexical_scan()
    return data

def array_declaration(data):
    global PROCEDURE_COUNTER 
    arraysize = 0
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == "array"
    data.lexical_scan()
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "of":
        data.lexical_scan()
        if data.token_type == TOKEN_KEYWORD and data.get_token_value() in primitive_types:
            declaration = data.get_token_value()
            data.lexical_scan()
        else:
            data.terminate("Error on line %d: Wrong array type %s" % (data.string_index, data.get_token_value()))
    else:
        data.terminate('Error on line %d: "of" not found where expected' % data.string_index)
    if data.token_type == TOKEN_IDENTIFYER:
        var_name = data.get_token_value()
        data.lexical_scan()
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "[":
            data.lexical_scan()
            if data.token_type == TOKEN_INTEGER:
                arraysize = int(data.get_token_value())
                data.lexical_scan()
            else:
                data.terminate('Error on line %d: array size can be only constant integer, found %s' % (data.string_index, data.get_token_value()))
            if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "]":
                data.lexical_scan()
            else:
                data.terminate('Error on line %d: "]" not found where expected' % data.string_index)
        else:
            data.terminate('Error on line %d: "[" not found where expected' % data.string_index)
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "=":
            data.lexical_scan()
            data = array_const(data)
            
            check_pushed_string(data)
            data.write("pop dx ;length")
            data.write("cmp dx, %d" % arraysize)
            data.write("jle @check_%d" % PROCEDURE_COUNTER)
            data.write("push %d" % data.string_index)
            data.write("jmp @ERROR_OUT_OF_BOUNDS")
            data.write("\n@check_%d:" % PROCEDURE_COUNTER)
            PROCEDURE_COUNTER += 1
            data.write("add dx, dx")
            data.write("mov di,0")
            repeat_mark = "@save_string_%d" % PROCEDURE_COUNTER
            PROCEDURE_COUNTER += 1
            data.write_label(repeat_mark)
            data.write("pop ax")
            data.write("mov %s[di],ax" % var_name)
            data.write("inc di")
            data.write("inc di")
            data.write("cmp di, dx")
            data.write("jl %s\n" % repeat_mark)
            #data.write("dec di")
            data.write("mov %s[di],0; terminator" % var_name)
            
        else:
            if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "filled":
                data.lexical_scan()
                if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "with":
                    data.lexical_scan()
                    data = expression2(data)
                    
                    check_pushed_int(data)
                    data.write("pop ax")
                    for i in xrange(arraysize):
                        data.write("mov %s[%d], ax" % (var_name, i*2))
                    
                else:
                    data.terminate('Error on line %d: "with" not found where expected' % data.string_index)
            else:
                data.terminate('Error on line %d: expected "=" or "filled", found %s' % (data.string_index, data.get_token_value()))
    else:
        data.terminate('Error on line %d: identifyer not found where expected' % data.string_index)
    data.write_variable("%s dw %s dup (?)" % (var_name, arraysize))
    arrays[var_name] = (primitive_types_dict[declaration], arraysize)
    return data
        
def expression(data):
    global PROCEDURE_COUNTER 
    declaration = ""
    operator_type = ""
    var_element = False
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() in primitive_types:
        declaration = data.get_token_value()
        data.lexical_scan()
    if data.token_type == TOKEN_IDENTIFYER:
        var_name = data.get_token_value()
        data.lexical_scan()
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "[":
            if declaration != "":
                data.terminate('Semantic error on line %d: cannot declare element of array!' % data.string_index)
            data.lexical_scan()
            data = expression2(data)
            check_pushed_int(data)
            data.write("pop [r14w]")
            var_element = True
            if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "]":
                data.lexical_scan()
            else:
                data.terminate('Error on line %d: "]" not found where expected' % data.string_index)
        elif declaration != "":
            if declaration != "string" and not (var_name in variables):
                data.write_variable("%s dw ?" % var_name)
                variables[var_name] = primitive_types_dict[declaration]
            elif declaration == "string" and not (var_name in arrays.keys()):
                data.write_variable("%s dw %s dup (?)" % (var_name, STRING_LENGTH))
                arrays[var_name] = (VAR_CHAR, STRING_LENGTH)
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "=":
            data.lexical_scan()
            operator_type = "="
        elif declaration != "":
            if variables[var_name] == VAR_CHAR:
                data.write("mov %s, %s" % (var_name, ord(' ')))
            else:
                data.write("mov %s, 0" % var_name)
            return data
        elif data.token_type == TOKEN_2L_DELIMITER and data.get_token_value() == "+=":
            data.lexical_scan()
            operator_type = "+="
        elif data.token_type == TOKEN_2L_DELIMITER and data.get_token_value() == "-=":
            data.lexical_scan()
            operator_type = "-="
        elif data.token_type == TOKEN_2L_DELIMITER and data.get_token_value() == "*=":
            data.lexical_scan()
            operator_type = "*="
        elif data.token_type == TOKEN_2L_DELIMITER and data.get_token_value() == "/=":
            data.lexical_scan()
            operator_type = "/="
        elif data.token_type == TOKEN_2L_DELIMITER and data.get_token_value() == "\\=":
            data.lexical_scan()
            operator_type = "/="
        else:
            data.terminate('Error on line %d: proper assignment not found where expected, found %s' % (data.string_index, data.get_token_value()))
        data = expression2(data)
        if var_name in arrays.keys():
            if not var_element:
                if operator_type != "=":
                    data.terminate('Symantic error on line %d: to array/string variable only "=" can be used!' % data.string_index)
                check_pushed_string(data)
                data.write("pop dx ;length")
                data.write("cmp dx, %d" % arrays[var_name][1])
                data.write("jle @check_%d" % PROCEDURE_COUNTER)
                data.write("push %d" % data.string_index)
                data.write("jmp @ERROR_OUT_OF_BOUNDS")
                data.write("\n@check_%d:" % PROCEDURE_COUNTER)
                PROCEDURE_COUNTER += 1
                data.write("mov di,0")
                repeat_mark = "@save_string_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write_label(repeat_mark)
                data.write("pop ax")
                data.write("mov %s[di],ax" % var_name)
                data.write("inc di")
                data.write("cmp di, dx")
                data.write("jne %s\n" % repeat_mark)
                data.write("mov %s[di],0; terminator" % var_name)
            else:
                check_pushed_int(data)
                data.write("pop ax")
                data.write("mov bx, [r14w]")
                data.write("add bx, bx")
                data.write("mov %s[bx], ax" % var_name)
        else:
            check_pushed_int(data)
            if operator_type == "=":
                data.write("pop ax")
                data.write("mov %s,ax" % var_name)
            else:
                data.write("pop bx")
                data.write("mov ax %s" % var_name)
                
                if operator_type[0] == "+":
                    data.write("add ax, bx")
                elif operator_type[0] == "-":
                    data.write("sub ax, bx")
                elif operator_type[0] == "*":
                    data.write("mul bx")
                elif operator_type[0] == "/" or operator == "\\":
                    data.write("push dx")
                    data.write("mov dx, 0")
                    data.write("div bx")
                    data.write("pop dx")
                data.write("mov %s,ax" % var_name)
    else:
        #this can't be actually LEL
        pass
    data.reset_argument()
    data.set_argument("variable", var_name)
    return data

def expression2(data):
    global CONSTANTS_COUNTER, PROCEDURE_COUNTER
    
    constant = ""
    exp_type = NO_VAR
    
    optimize_flag = False
    
    data = expression3(data)
    #exp_type = data.get_argument("type")
    while (data.token_type, data.get_token_value()) in operators: #отступил
        
        
        operator = data.get_token_value()
        data.lexical_scan()
        if operator == "?": #INDIVIDUAL TASK
            t_1_mark = "@ternary_%d_1" % PROCEDURE_COUNTER
            t_2_mark = "@ternary_%d_2" % PROCEDURE_COUNTER
            
            check_pushed_int(data)
            data.write("pop ax")
            data.write("cmp ax, 0")
                
            data.write("je %s" % t_1_mark)
            
            data = expression2(data)
            data.write("jmp %s" % t_2_mark)
            if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == ":":
                data.lexical_scan()
            else:
                data.terminate('Error on line %d: ":" not found where expected' % data.string_index)
            data.write_label(t_1_mark)
            data = expression2(data)
            data.write_label(t_2_mark)
        else:
            data = expression3(data)
        
            marks = ["@exp2_%d_%d" % (x, PROCEDURE_COUNTER) for x in xrange(35)]
            
            PROCEDURE_COUNTER += 1
            
            data.write("pop r9w")
            data.write("cmp r9w, 1")
            data.write("jne %s" % marks[0])
            data.write("push ax")
            data.write("mov ax, %d" % ord(operator[0]))
            data.write("cmp ax, %d; operator = +" % ord("+"))
            data.write("pop ax")
            data.write("jne %s" % marks[11])
            data.write("pop ax; length")
            
            data.write("mov dx, -1")
            data.write_label(marks[20])
            data.write("pop bx")
            data.write("inc dx")
            data.write("mov di, dx")
            data.write("mov concatenator2[di], bx")
            data.write("cmp bx, 0")
            data.write("je %s" % marks[21])
            data.write("cmp dx, ax")
            data.write("jg %s" % marks[22])
            data.write("cmp dx, 256")
            data.write("je %s" % marks[23])
            data.write("jmp %s" % marks[20])
            data.write_label(marks[23])
            data.write("dec dx")
            data.write_label(marks[22])
            data.write("mov di, dx")
            data.write("mov concatenator2[di], 0")
            data.write_label(marks[21])
            data.write("mov [r12w], dx")
            
            data.write("pop [r8w]")
            data.write("cmp [r8w], 1")
            data.write("jne %s" % marks[4])
            data.write("pop ax; length")
            data.write("mov dx, -1")
            data.write_label(marks[24])
            data.write("pop bx")
            data.write("inc dx")
            data.write("mov di, dx")
            data.write("mov concatenator[di], bx")
            
            data.write("cmp bx, 0")
            data.write("je %s" % marks[25])
            data.write("cmp dx, ax")
            data.write("jg %s" % marks[26])
            data.write("cmp dx, 255")
            data.write("je %s" % marks[27])
            data.write("jmp %s" % marks[24])
            data.write_label(marks[27])
            data.write("dec dx")
            data.write_label(marks[26])
            data.write("mov di, dx")
            data.write("mov concatenator[di], 0")
            data.write_label(marks[25])
            
            data.write("mov ax, [r12w]")
            data.write("mov bx, -1")
            data.write_label(marks[28])
            data.write("inc bx")
            data.write("mov cx, concatenator2[bx]")
            data.write("mov di, dx")
            data.write("add di, bx")
            data.write("mov concatenator[di], cx")
            
            data.write("cmp bx, ax")
            data.write("je %s" % marks[32])
            data.write("cmp di, 255")
            data.write("je %s" % marks[30])
            data.write("jmp %s" % marks[28])
            data.write_label(marks[30])
            data.write("mov concatenator[di], 0")
            data.write_label(marks[32])
            data.write("mov ax, di")
            data.write_label(marks[29])
           
            data.write("push concatenator[di]")
            data.write("dec di")
            data.write("cmp di, 0")
            data.write("jl %s" % marks[31])
            data.write("jmp %s" % marks[29])
            data.write_label(marks[31])
            data.write("push ax")
            data.write("push 1")
            data.write("jmp %s" % marks[10])
            
            data.write_label(marks[0])
            data.write("pop bx")
            data.write("pop [r8w]")
            data.write("cmp [r8w], 0")
            data.write("jne %s" % marks[4])
            data.write("pop ax")
            if operator == "+":
                data.write("add ax, bx")
            elif operator == "-":
                data.write("sub ax, bx")
            elif operator == "*":
                data.write("mul bx")
            elif operator == "/" or operator == "\\":
                data.write("push dx")
                data.write("mov dx, 0")
                data.write("div bx")
                data.write("pop dx")
            elif operator == "and":
                data.write("and ax, bx")
            elif operator == "or":
                data.write("or ax, bx")
            elif operator == "xor":
                data.write("xor ax, bx")
            elif operator == "==":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jne %s" % mark)
                data.write("mov ax, -1")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, 0")
                data.write_label(mark2)
            elif operator == "!=":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jne %s" % mark)
                data.write("mov ax, 0")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, -1")
                data.write_label(mark2)
            elif operator == ">":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jg %s" % mark)
                data.write("mov ax, 0")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, -1")
                data.write_label(mark2)
            elif operator == "<":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jl %s" % mark)
                data.write("mov ax, 0")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, -1")
                data.write_label(mark2)
            elif operator == ">=":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jge %s" % mark)
                data.write("mov ax, 0")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, -1")
                data.write_label(mark2)
            elif operator == "<=":
                mark = "@equals_%d" % PROCEDURE_COUNTER
                mark2 = "@equals2_%d" % PROCEDURE_COUNTER
                PROCEDURE_COUNTER += 1
                data.write("cmp ax, bx")
                data.write("jle %s" % mark)
                data.write("mov ax, 0")
                data.write("jmp %s" % mark2)
                data.write_label(mark)
                data.write("mov ax, -1")
                data.write_label(mark2)
                
            #data.write("change ax %s bx" % operator)
            data.write("push ax")
            data.write("push 0")
            data.write("jmp %s" % marks[10])
            
            data.write_label(marks[4])
            data.write("push %d" % data.string_index)
            data.write("jmp @ERROR_CANNOT_OPERATE")
            
            data.write_label(marks[8])
            data.write("push %d" % data.string_index)
            data.write("jmp @ERROR_RESULT_TOO_LONG")
            
            data.write_label(marks[11])
            data.write("push %d" % data.string_index)
            data.write("jmp @ERROR_WRONG_OPERATOR_FOR_ARRAYS")
            
            data.write_label(marks[10])
        
    return data

def expression3(data):
    global PROCEDURE_COUNTER
    exp_not = False
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "not":
        data.lexical_scan()
        exp_not = True
    if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "(":
        data.lexical_scan()
        data = expression2(data)
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == ")":
            data.lexical_scan()
        else:
            data.terminate('Error on line %d: ) not found where expected' % data.string_index)
        
    elif data.token_type == TOKEN_STRING:
        if len(data.get_token_value()) != 1:
            data.write("push 0 ;terminator")
            for symbol in data.get_token_value()[::-1]:
                data.write("push %d ;ord(%s)" % (ord(symbol),symbol))
            data.write("push %d" % (len(data.get_token_value())+1))
            data.write("push 1")
        else: #it's actually a char!
            data.write("push %d ;ord(%s)" % (ord(data.get_token_value()[0]),data.get_token_value()[0])) #does it work?
            data.write("push 0")
        data.lexical_scan()
    elif data.token_type == TOKEN_INTEGER:
        data.write("push %s" % data.get_token_value())
        data.write("push 0")
        data.lexical_scan()
    elif data.token_type == TOKEN_KEYWORD and data.get_token_value() == "true":
        data.write("push 1")
        data.write("push 0")
        data.lexical_scan()
    elif data.token_type == TOKEN_KEYWORD and data.get_token_value() == "false":
        data.write("push 0")
        data.write("push 0")
        data.lexical_scan()
    elif in_first("procedure", data.token_type, data.token_number):
        data = procedure(data)
    elif data.token_type == TOKEN_IDENTIFYER:
        var_name = data.get_token_value()
        data.lexical_scan()
        is_array_elm = False
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "[":
        
            array_ok_mark = "@array_%d_ok" % PROCEDURE_COUNTER
            PROCEDURE_COUNTER += 1
            data.lexical_scan()
            is_array_elm = True
            data = expression2(data)
            data.write("pop r8w")
            data.write("cmp r8w, 0")
            data.write("je %s" % array_ok_mark)
            data.write("push %d" % data.string_index)
            data.write("jmp @ERROR_NOT_INTEGER") #TODO REALIZE
            data.write_label(array_ok_mark)
            data.write("pop di")
            data.write("add di, di")
            data.write("push [%s+di]" % var_name)
            data.write("push 0")
            if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "]":
                data.lexical_scan()
            else:
                data.terminate('Error on line %d: "]" not found where expected' % data.string_index)

        else:
            if not is_array_elm:
                if not var_name in arrays:
                    data.write("push [%s]" % var_name)
                    data.write("push 0")
                else:
                    data.write("push 0 ;terminator")
                    data.write("mov di,%d" % arrays[var_name][1])
                    repeat_mark = "@push_string_%d" % PROCEDURE_COUNTER
                    PROCEDURE_COUNTER += 1
                    data.write_label(repeat_mark)
                    data.write("push [%s+di]" % var_name)
                    data.write("dec di")
                    data.write("cmp di, 0")
                    data.write("jge %s" % repeat_mark)
                    data.write("push %d" % (arrays[var_name][1]+1))
                    data.write("push 1")
                
    else:
        data.terminate('Error on line %d: operand type %s is incorrect' % (data.string_index, str(data.get_token_value())))
    
    if exp_not:
        not_mark1 = "@not1_%d" % PROCEDURE_COUNTER
        not_mark2 = "@not2_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        check_pushed_int(data)
        data.write("pop ax")
        data.write("cmp ax, 0")
        data.write("jne %s" % not_mark1)
        data.write("push -1")
        data.write("jmp %s" % not_mark2)
        data.write_label(not_mark1)
        data.write("push 0")
        data.write_label(not_mark2)
        data.write("push 0")
    return data
    
def code_while(data):
    global PROCEDURE_COUNTER
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == "while":
    data.lexical_scan()
    while_mark = "@while_%d" % PROCEDURE_COUNTER
    data.write("\n%s:" % while_mark)
    end_while_mark = "@end_while_%d" % PROCEDURE_COUNTER
    
    divergence_mark1 = "@while_if_1_%d" % PROCEDURE_COUNTER
    divergence_mark2 = "@while_if_2_%d" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    data = expression2(data)
    check_pushed_int(data)
    data.write("pop ax")
    data.write("cmp ax, 0")
    data.write("je %s" % end_while_mark)
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
    data = codestring(data)
    data.write("jmp %s\n" % while_mark)
    data.write("%s:" %end_while_mark)
    return data

def code_for(data):
    global PROCEDURE_COUNTER, CONSTANTS_COUNTER
    for_mark = "@for_%d" % PROCEDURE_COUNTER
    end_for_mark = "@end_for_%d" % PROCEDURE_COUNTER
    complicated_mark1 = "@for_if1_%d" % PROCEDURE_COUNTER
    complicated_mark2 = "@for_if2_%d" % PROCEDURE_COUNTER
    divergence_mark1 = "@for_div1_%d" % PROCEDURE_COUNTER
    divergence_mark2 = "@for_div2_%d" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == "for":
    data.lexical_scan()
    data = expression(data)
    equals_var = data.get_argument("variable")
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "to":
        data.lexical_scan()
    else:
        data.terminate('Error on line %d: "to" not found where expected' % data.string_index)
    data = expression2(data)
    equals_const = "r20w"
    for_const = "r21w"
    step_const = "r22w"
    #data.optimizer_constants_trig = True
    check_pushed_int(data)
    data.write("pop ax")
    data.write("mov [%s], ax" % equals_const)
    data.write("mov ax, [%s]" % equals_var)
    data.write("cmp ax, [%s]" % equals_const)
    data.write("jle %s" % divergence_mark1)
    data.write("mov [%s],1" % for_const)
    data.write("jmp %s" % divergence_mark2)
    data.write_label(divergence_mark1)
    data.write("mov [%s],0" % for_const)
    data.write_label(divergence_mark2)
    
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "step":
        data.lexical_scan()
        data = expression2(data)
        check_pushed_int(data)
        data.write("pop [%s]" % step_const)
    else:
        data.write("mov [%s], 1" % step_const)
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
        
    data.write_label(for_mark)
    """data.write("push ax")
    data.write("mov ax, [%s]" % equals_var)
    data.write("cmp ax, [%s]" % equals_const)
    data.write("pop ax")
    data.write("jle %s" % complicated_mark1)
    data.write("cmp [%s], 1" % for_const)
    data.write("je %s" % end_for_mark)
    data.write("jmp %s" % complicated_mark2)
    data.write_label(complicated_mark1)
    data.write("cmp [%s], 0" % for_const)
    data.write("je %s" % end_for_mark)
    data.write_label(complicated_mark2)"""
    
    data = codestring(data)
    data.write("mov ax, [%s]" % equals_var)
    data.write("cmp ax, [%s]" % equals_const)
    data.write("je %s" % end_for_mark)
    data.write("jl %s" % complicated_mark1)
    data.write("cmp [%s], 0" % for_const)
    data.write("je %s" % end_for_mark)
    data.write("mov bx, [%s]" % step_const)
    data.write("sub [%s], bx" % equals_var)
    data.write("jmp %s" % complicated_mark2)
    data.write_label(complicated_mark1)
    data.write("cmp [%s], 1" % for_const)
    data.write("je %s" % end_for_mark)
    data.write("mov bx, [%s]" % step_const)
    data.write("add [%s], bx" % equals_var)
    data.write_label(complicated_mark2)
    data.write("jmp %s\n" % for_mark)
    data.write_label(end_for_mark)
    return data

def code_if(data):
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == "if":
    global PROCEDURE_COUNTER
    data.lexical_scan()
    end_if_mark = "@if_was_wrong_%d" % PROCEDURE_COUNTER
    data = expression2(data)
    check_pushed_int(data)
    data.write("pop ax")
    data.write("cmp ax, 0")
    data.write("je %s" % end_if_mark)
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
    data = codestring(data)
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "else":
        end_else_mark = "@else_was_skipped_%d" % PROCEDURE_COUNTER
        data.write("jmp %s" % end_else_mark)
        data.write_label(end_if_mark)
        data.lexical_scan()
        if data.token_type == TOKEN_EOSTRING:
            data.lexical_scan()
        data = codestring(data)
        data.write_label(end_else_mark)
    else:
        data.write_label(end_if_mark)
        
    PROCEDURE_COUNTER += 1
    return data

def dowhile(data):
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == "do":
    global PROCEDURE_COUNTER
    repeat_mark = "@dowhile_%d" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    data.write_label("\n"+repeat_mark)
    data.lexical_scan()
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
    data = codestring(data)
    if data.token_type == TOKEN_EOSTRING:
        data.lexical_scan()
    if data.token_type == TOKEN_KEYWORD and data.get_token_value() == "dowhile":
        data.lexical_scan()
    else:
        data.terminate('Error on line %d: "dowhile" not found where expected' % data.string_index)
    data = expression2(data)
    check_pushed_int(data)
    data.write("pop ax")
    data.write("cmp ax, 0")
    data.write("jne %s" % repeat_mark)
    return data

def procedure(data):
    global PROCEDURE_COUNTER
    #assuming data.token_type == TOKEN_IDENTIFYER and data.get_token_value() == in procedures:
    procedure_type = data.get_token_value()
    data.lexical_scan()
    if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == "(":
        data.lexical_scan()
        if procedure_type == "asm":
            if data.token_type == TOKEN_STRING:
                data.write(data.get_token_value + "; direct entry")
            else:
                data.terminate("Semantic error on line %d: in 'asm' procedure only constant strings are allowed" % data.string_index)
        if procedure_type != "read":
            data = expression2(data)
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == ")":
            data.lexical_scan()
        else:
            data.terminate('Error on line %d: in procedure ) not found where expected %s' % (data.string_index, data.get_token_value()))
    else:
        data.terminate('Error on line %d: ( not found where expected' % data.string_index)
    if procedure_type == "print":
        check_pushed_string(data)
        data.write("pop dx ;length")
        data.write("mov cx,0")
        repeat_mark = "@print_%d" % PROCEDURE_COUNTER
        end_mark = "@print_stop_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        data.write_label(repeat_mark)
        data.write("pop ax")
        data.write("cmp ax, 0; terminator")
        data.write("je %s" % end_mark)
        
        data.write("mov dx, ax")
        data.write("mov ah, 2h")
        data.write("int 21h")
        
        data.write("inc cx")
        data.write("cmp cx, dx")
        data.write("jl %s\n" % repeat_mark)
        data.write_label(end_mark)
        data.write("mov dl, 10")
        data.write("mov ah, 2h")
        data.write("int 21h")
        data.write("mov dl, 13")
        data.write("int 21h")
    elif procedure_type == "write":
        check_pushed_string(data)
        data.write("pop dx ;length")
        data.write("mov cx,0")
        repeat_mark = "@print_%d" % PROCEDURE_COUNTER
        end_mark = "@print_stop_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        data.write_label(repeat_mark)
        data.write("pop ax")
        data.write("cmp ax, 0; terminator")
        data.write("je %s" % end_mark)
        
        data.write("mov dx, ax")
        data.write("mov ah, 2h")
        data.write("int 21h")
        
        data.write("inc cx")
        data.write("cmp cx, dx")
        data.write("jl %s\n" % repeat_mark)
        data.write_label(end_mark)
    elif procedure_type == "to_str":
        
        repeat_mark = "@get_%d" % PROCEDURE_COUNTER
        repeat_mark2 = "@get2_%d" % PROCEDURE_COUNTER
        neg_mark = "@get3_%d" % PROCEDURE_COUNTER
        neg_mark2 = "@get4_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        check_pushed_int(data)
        data.write("mov [r9w], 10")
        data.write("pop ax")
        data.write("mov [r8w], 0")
        data.write("test ax, ax")
        data.write("jns %s" % neg_mark)
        data.write("neg ax")
        data.write("mov [r8w], 1")
        data.write_label(neg_mark)
        data.write("push 0; terminator")
        data.write("mov bx,0")
        data.write_label(repeat_mark)
        data.write("mov dx,0")
        data.write("div r9w")
        data.write("add dx,30h")
        data.write("mov concatenator[bx], dx")
        data.write("inc bx")
        data.write("cmp ax, 0")
        data.write("jne %s" % repeat_mark)
        data.write("cmp [r8w], 1")
        data.write("jne %s" % neg_mark2)
        data.write("mov concatenator[bx], 2Dh") #знак минуса
        data.write("inc bx")
        data.write_label(neg_mark2)
        data.write("mov cx, 1")
        data.write("inc bx")
        data.write_label(repeat_mark2)
        data.write("mov di, cx")
        data.write("push concatenator[di-1]")
        data.write("inc cx")
        data.write("cmp cx, bx")
        data.write("jne %s" % repeat_mark2)
        data.write("push bx")
        data.write("push 1")
        
    elif procedure_type == "to_char":
        
        check_pushed_int(data)
        data.write("pop ax")
        data.write("push 0")
        data.write("push ax")
        data.write("push 2")
        data.write("push 1")

    elif procedure_type == "to_bool":
        
        check_pushed_int(data)
        mark = "@tobool_%d" % PROCEDURE_COUNTER
        mark2 = "@tobool2_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        data.write("pop ax")
        data.write("cmp ax, 0")
        data.write("jne %s" % mark)
        data.write("push 0")
        data.write("push %s" % ord('e'))
        data.write("push %s" % ord('s'))
        data.write("push %s" % ord('l'))
        data.write("push %s" % ord('a'))
        data.write("push %s" % ord('f'))
        data.write("push 6")
        data.write("push 1")
        data.write("jmp %s" % mark2)
        data.write_label(mark)
        data.write("push 0")
        data.write("push %s" % ord('e'))
        data.write("push %s" % ord('u'))
        data.write("push %s" % ord('r'))
        data.write("push %s" % ord('t'))
        data.write("push 5")
        data.write("push 1")
        data.write_label(mark2)
        
    elif procedure_type == "examine":
        data.write("pop bx")
        data.write("pop ax")
        data.write("push bx")
        data.write("push 0")
        
        
    elif procedure_type == "to_int":
        
        check_pushed_string(data)
        data.write("pop di ;length")
        data.write("mov cx,0")
        data.write("mov bx, 0")
        repeat_mark = "@print_%d" % PROCEDURE_COUNTER
        end_mark = "@print_stop_%d" % PROCEDURE_COUNTER
        nonok_mark = "@toint3_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        data.write_label(repeat_mark)
        data.write("pop ax")
        data.write("cmp ax, 0; terminator")
        data.write("je %s" % end_mark)
        data.write("mov ah,0")
        data.write("sub ax, 30h")
        data.write("cmp ax, 9")
        data.write("jg %s" % nonok_mark)
        data.write("add bx, ax")
        data.write("mov ax, 10")
        data.write("mul bx")
        data.write("mov bx, ax")
        data.write_label(nonok_mark)
        
        data.write("inc cx")
        data.write("cmp cx, di")
        data.write("jl %s\n" % repeat_mark)
        data.write_label(end_mark)
        data.write("mov ax, bx")
        data.write("mov dx, 0")
        data.write("mov bx, 10")
        data.write("div bx")
        data.write("push ax")
        data.write("push 0")
        
    elif procedure_type == "read":
        
        data.write("mov cx, 0")
        repeat_mark = "@read_%d" % PROCEDURE_COUNTER
        repeat_mark2 = "@read2_%d" % PROCEDURE_COUNTER
        repeat_mark3 = "@read3_%d" % PROCEDURE_COUNTER
        PROCEDURE_COUNTER += 1
        data.write_label(repeat_mark)
        data.write("inc cx")
        data.write("mov ah, 01h")
        data.write("int 21h")
        data.write("mov ah, 0")
        data.write("mov di, cx")
        data.write("mov concatenator[di], ax")
        data.write("cmp al, 13")
        data.write("je %s" % repeat_mark3)
        data.write("cmp cx, 255")
        data.write("je %s" % repeat_mark3)
        data.write("jmp %s" % repeat_mark)
        data.write_label(repeat_mark3)
        data.write("mov dx, cx")
        data.write("dec cx")
        data.write_label(repeat_mark2)
        data.write("mov di, cx")
        data.write("push concatenator[di]")
        data.write("dec cx")
        data.write("cmp cx, -1")
        data.write("jne %s" % repeat_mark2)
        data.write("push dx")
        data.write("push 1")
        
        
        
    return data

def array_const(data):
    global PROCEDURE_COUNTER
    #assuming data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == '[':
    data.lexical_scan()
    data = expression2(data)
    check_pushed_int(data)
    length = 1
    while not in_follow("array_const", data.token_type, data.token_number):
        length += 1
        if data.token_type == TOKEN_ONE_LITER_DELIMITER and data.get_token_value() == ",":
            data.lexical_scan()
        else:
            data.terminate('Error on line %d: in array declaration , not found where expected %s' % (data.string_index, data.get_token_value()))
        data = expression2(data)
        check_pushed_int(data) #type is poped, only raw numbers here!
    #ends on ']'
    data.lexical_scan()
    
    repeat_mark = "@arrayconst1_%d" % PROCEDURE_COUNTER
    repeat_mark2 = "@arrayconst2_%d" % PROCEDURE_COUNTER
    PROCEDURE_COUNTER += 1
    
    
    data.write("mov cx,%d" % length)
    data.write("add cx, cx")
    data.write_label(repeat_mark)
    data.write("pop ax")
    data.write("mov di, cx")
    data.write("mov concatenator[di], ax")
    data.write("dec cx")
    data.write("dec cx")
    data.write("cmp cx, 0")
    data.write("jne %s" % repeat_mark)
    data.write("mov cx,%d" % length)
    data.write("add cx, cx")
    data.write_label(repeat_mark2)
    data.write("mov di, cx")
    data.write("push concatenator[di]")
    data.write("dec cx")
    data.write("dec cx")
    data.write("cmp cx, 0")
    data.write("jne %s" % repeat_mark2)
    data.write("push %d" % length)
    data.write("push 1")
    
    return data

def mainloop():
    source = open('test.eri', 'r')
    output = open('output.asm', 'w')
    string = source.readline()
    position = 0
    string_index = 1
    flag = True
    values = lexical.Scan(source, string, position)
    
    data = Travelling_Data(values[0], values[1], source, values[2], values[3], string_index, output)
    print "syntax analysis has begun"
    data.write(""".model tiny ; для создания com-файла
.code ; сегмент кода
.386
org 100h ; для создания com-файла
@start: ; начало программы""")
    text(data)
    
    data.write("jmp @finnish")
    
    error_msg(data, "@ERROR_ASSIGN_STRING_TO_INTEGER", "trying to assign array to integer")
    error_msg(data, "@ERROR_CANNOT_OPERATE", "cannot calculate array and integer")
    error_msg(data, "@ERROR_NOT_INTEGER", "array index can only be integer")
    error_msg(data, "@ERROR_OUT_OF_BOUNDS", "array out of bounds")
    error_msg(data, "@ERROR_RESULT_TOO_LONG", "concatenating arrays have too big sum length")
    error_msg(data, "@ERROR_WRONG_OPERATOR_FOR_ARRAYS", "can only use + with arrays")
    error_msg(data, "@ERROR_CANNOT_TOINT", "couldn't convert string to integer")
    
    data.write("@finnish:")
    data.write("int 20h")
    
    data.write("ret\n")
    data.execute_variables()
    data.write("r8w dw ?")
    data.write("r9w dw ?")
    data.write("r10w dw ?")
    data.write("r11w dw ?")
    data.write("r12w dw ?")
    data.write("r13w dw ?")
    data.write("r14w dw ?")
    data.write("r20w dw ?")
    data.write("r21w dw ?")
    data.write("r22w dw ?")
    data.write("concatenator dw 512 dup (?)")
    data.write("concatenator2 dw 256 dup (?)")
    data.write("end @start\n")
    print "syntax analysis has ended"
    data.close()

if __name__ == "__main__":
    mainloop()

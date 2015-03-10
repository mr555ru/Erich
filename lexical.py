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

import string
import keyword

STATE_EMPTY = 0
STATE_READING_INTEGER = 1
STATE_READING_IDENTIFYER = 2
STATE_POSSIBLE_2L_DELIMITER = 3
STATE_TERMINATING = 999
STATE_ERROR = 1000
STATE_READING_STRING_ONE_QUOTE = 41
STATE_READING_STRING_TWO_QUOTES = 42
STATE_READING_COMMENT = 6
STATE_FOUND_ONE_QUOTE = 100
STATE_FOUND_TWO_QUOTES = 101
STATE_MULTILINE_STRING = 7
STATE_MULTILINE_STRING_FOUND_ONE_QUOTE = 102
STATE_MULTILINE_STRING_FOUND_TWO_QUOTES = 103
STATE_POSSIBLE_END_OF_STRING = 8

TOKEN_INTEGER = 1
TOKEN_IDENTIFYER = 2
TOKEN_ONE_LITER_DELIMITER = 3
TOKEN_2L_DELIMITER = 4
TOKEN_STRING = 5
TOKEN_KEYWORD = 6
TOKEN_EOSTRING = 7
UNDEFINED = 999

TOKEN_DOESNT_EXIST = -1

SetDigits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
SetEngLetters = list(string.letters) + ["_"] #автоматически достает все буквы из уже существующей функции и добавляет "_"
SetSpaces = [' ', '\t', ';', '\n'] # ; игнорируется
SetTwoLiter = ['>=', '<=', '==', '!=', '+=', '-=', '*=', '/=', '\\=']
SetTwoLiterFirst = [twoliter[0] for twoliter in SetTwoLiter] #создает список первых символов из SetTwoLiter
SetKeywords = ["array",
                "of",
                "filled",
                "with",
                "int",
                "char",
                "string",
                "boolean",
                "and",
                "or",
                "xor",
                "not",
                "true",
                "false",
                "while",
                "for",
                "to",
                "step",
                "do",
                "dowhile",
                "print",
                "write",
                "read",
                "examine",
                "to_int",
                "to_str",
                "to_char",
                "asm",
                "if",
                "else"]#keyword.kwlist #автоматически достает все ключевые слова языка Python из уже существующей функции
OneQuote = "'"
TwoQuotes = '"'
OneLineCommentBegin = '#'


Table_Integers = []
Table_Identifiers = []
Table_TwoLitDelimiters = []
Table_OneLitDelimiters = []
Table_Strings = []
Table_Keywords = SetKeywords

corellated_table     = {TOKEN_INTEGER: Table_Integers, 
                        TOKEN_IDENTIFYER: Table_Identifiers,
                        TOKEN_ONE_LITER_DELIMITER: Table_OneLitDelimiters,
                        TOKEN_2L_DELIMITER: Table_TwoLitDelimiters,
                        TOKEN_STRING: Table_Strings,
                        TOKEN_KEYWORD: Table_Keywords
                       } #связывает таблицу с соответствующим токеном

token_descriptions   = {TOKEN_INTEGER: "int",
                        TOKEN_IDENTIFYER: "id",
                        TOKEN_ONE_LITER_DELIMITER: "1ld",
                        TOKEN_2L_DELIMITER: "2ld",
                        TOKEN_STRING: "str",
                        TOKEN_KEYWORD: "kw",
                        TOKEN_EOSTRING: "eostring"
                       } #связывает строковое обозначение с соответствующим токеном

def eostring(string, position): #проверка на конец строки
    if position >= len(string):
        return True
    return False


def Scan(inputfile, inputstring, position, pry=False): #pry: подглядывать
    inputstring = inputstring.lower()
    
    if pry:
        rememberpos = position
    
    #Инициализация
    state = STATE_EMPTY
    tokentype = UNDEFINED
    tokenvalue = ''
    
    #Цикл
    while not state == STATE_TERMINATING:
        
        if eostring(inputstring, position): #обработка конца строки
            if state != STATE_POSSIBLE_2L_DELIMITER:
                if state == STATE_MULTILINE_STRING:
                    tokenvalue += '\n'
                    inputstring = inputfile.readline()
                    inputstring = inputstring.lower()
                    if inputstring == '':
                        return None #eof
                    position = 0
                elif (state == STATE_READING_INTEGER) or (state == STATE_READING_IDENTIFYER) or (state == STATE_EMPTY) or (state == STATE_READING_COMMENT):
                    if state == STATE_EMPTY or state == STATE_READING_COMMENT:
                        tokentype = TOKEN_EOSTRING
                        tokenvalue = ''
                    state = STATE_TERMINATING
                    if not pry:
                        inputstring = inputfile.readline()
                        inputstring = inputstring.lower()
                        if inputstring == '':
                            return None #eof
                        position = 0
            else:
                tokentype = TOKEN_ONE_LITER_DELIMITER
                state = STATE_TERMINATING
            
        
        if state == STATE_EMPTY:
            
            
            if inputstring[position] in SetDigits:
                tokentype = TOKEN_INTEGER
                tokenvalue = inputstring[position]
                state = STATE_READING_INTEGER
            
            elif inputstring[position] in SetEngLetters:
                tokentype = TOKEN_IDENTIFYER
                tokenvalue = inputstring[position]
                state = STATE_READING_IDENTIFYER
                
            elif inputstring[position] == TwoQuotes:
                tokentype = TOKEN_STRING
                tokenvalue = ''
                state = STATE_READING_STRING_TWO_QUOTES
                
            elif inputstring[position] == OneQuote:
                state = STATE_FOUND_ONE_QUOTE
                
            elif inputstring[position] == OneLineCommentBegin:
                state = STATE_READING_COMMENT
                
            elif inputstring[position] in SetSpaces:
                state = STATE_EMPTY
            
            elif inputstring[position] in SetTwoLiterFirst:
                state = STATE_POSSIBLE_2L_DELIMITER
                tokenvalue = inputstring[position]
                tokentype = TOKEN_2L_DELIMITER
                
            else: #предполагаем, что это однолитерный разделитель
                tokentype = TOKEN_ONE_LITER_DELIMITER
                tokenvalue = inputstring[position]
                position += 1
                state = STATE_TERMINATING
                
        elif state == STATE_READING_INTEGER:
            if inputstring[position] in SetDigits:
                tokenvalue += inputstring[position]
                state = STATE_READING_INTEGER
            else:
                state = STATE_TERMINATING
                
        elif state == STATE_READING_IDENTIFYER:
            if inputstring[position] in SetDigits or inputstring[position] in SetEngLetters:
                tokenvalue += inputstring[position]
                state = STATE_READING_IDENTIFYER
            else:
                state = STATE_TERMINATING
                
        elif state == STATE_READING_STRING_TWO_QUOTES:
            if inputstring[position] == TwoQuotes:
                state = STATE_TERMINATING
                position += 1
            else:
                tokenvalue += inputstring[position]
                state = STATE_READING_STRING_TWO_QUOTES
                
        elif state == STATE_FOUND_ONE_QUOTE:
            if inputstring[position] == OneQuote:
                state = STATE_FOUND_TWO_QUOTES
            else:
                state = STATE_READING_STRING_ONE_QUOTE
                tokentype = TOKEN_STRING
                tokenvalue = inputstring[position]
                
        elif state == STATE_FOUND_TWO_QUOTES:
            if inputstring[position] == OneQuote:
                state = STATE_MULTILINE_STRING
                tokentype = TOKEN_STRING
                tokenvalue = ''
            else:
                tokentype = TOKEN_STRING
                tokenvalue = ''
                state = STATE_TERMINATING
                position += 1
                
        elif state == STATE_READING_STRING_ONE_QUOTE:
            if inputstring[position] == OneQuote:
                state = STATE_TERMINATING
                position += 1
            else:
                tokenvalue += inputstring[position]
                state = STATE_READING_STRING_ONE_QUOTE
                
        elif state == STATE_MULTILINE_STRING:
            if inputstring[position] == OneQuote:
                state = STATE_MULTILINE_STRING_FOUND_ONE_QUOTE
            else:
                tokenvalue += inputstring[position]
                state = STATE_MULTILINE_STRING
                
        elif state == STATE_MULTILINE_STRING_FOUND_ONE_QUOTE:
            if inputstring[position] == OneQuote:
                state = STATE_MULTILINE_STRING_FOUND_TWO_QUOTES
            else:
                tokenvalue += "'" + inputstring[position]
                state = STATE_MULTILINE_STRING
                
        elif state == STATE_MULTILINE_STRING_FOUND_TWO_QUOTES:
            if inputstring[position] == OneQuote:
                state = STATE_TERMINATING
                position += 1
            else:
                tokenvalue += "''" + inputstring[position]
                state = STATE_MULTILINE_STRING
                
        elif state == STATE_POSSIBLE_2L_DELIMITER:
            if (tokenvalue + inputstring[position]) in SetTwoLiter:
                tokenvalue += inputstring[position]
                tokentype = TOKEN_2L_DELIMITER
                state = STATE_TERMINATING
                position += 1
            else:
                tokentype = TOKEN_ONE_LITER_DELIMITER
                state = STATE_TERMINATING
                
                
        elif state == STATE_READING_COMMENT:
            pass
        
        position += 1
        
    position -= 1
    
    token_number = 0
    
    if tokentype == TOKEN_IDENTIFYER and tokenvalue in SetKeywords:
        tokentype = TOKEN_KEYWORD
        token_number = SetKeywords.index(tokenvalue)
    elif tokentype == TOKEN_EOSTRING:
        token_number = 0
    else:
        table = corellated_table[tokentype]
        if tokenvalue in table:
            token_number = table.index(tokenvalue)
        else:
            token_number = len(table)
            table.append(tokenvalue)
            
    if pry:
        position = rememberpos
    return (tokentype, token_number, inputstring, position)
 
 
def mainloop():
     source = open('test.eri', 'r')
     string = source.readline()
     position = 0
     flag = True
     
     while flag:
         values = Scan(source, string, position)
         if values is None: #достигнут конец файла
             flag = False
             return 0
         
         token_description = token_descriptions[values[0]]
         token_number = values[1]
         string = values[2]
         position = values[3]
         
         if values[0] != TOKEN_EOSTRING:
             table = corellated_table[values[0]]
             token_value = table[token_number]
            
             print "%s #%i: %s" % (token_description, token_number, token_value)
         else:
             print "EOSTRING"
         #raw_input()
         
def print_table(table, name):
    print "==============%s==============" % name
    for i in xrange(len(table)):
        print "%d\t%s" % (i, table[i])
        
def print_tables():
    for tokentype, table in corellated_table.items():
        print_table(table, token_descriptions[tokentype])
         
if __name__ == "__main__":
    mainloop() 
    print_tables()
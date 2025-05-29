#!/usr/bin/env python3
import sys
import tokenize
import io

def check_syntax(filename):
    with open(filename, 'rb') as file:
        try:
            tokens = list(tokenize.tokenize(file.readline))
            print("No syntax errors found.")
        except tokenize.TokenError as e:
            print(f"Tokenize Error: {e}")
        except IndentationError as e:
            print(f"Indentation Error: {e}")
        except SyntaxError as e:
            print(f"Syntax Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <python_file>")
    else:
        check_syntax(sys.argv[1]) 
"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import re
from pathlib import Path

# Third Party Libraries
import pandas as pd
from loguru import logger

PWD = Path(os.path.dirname(__file__))

ALPHA = "A-Z"
DIGIT = r"\d"
SPACE = " "
HYPHEN = "-"
SPECIAL = r"()?:.,'=+/"

# Basic Lexical Items
# The following basic lexical items are defined for use in this specification:
LEXICAL_ITEMS = {
    # • ALPHA ::= 'A'|'B'|'C'|'D'|'E'|'F'|’G'|'H'|'I'|'J'|'K'|'L'|
    # 'M'|'N'|'O'|'P'|'Q'|'R'|'S'|'T'|'U'|'V'|'W'|'X'|'Y'|'Z'
    "ALPHA": rf"[{ALPHA}]",
    # • DIGIT ::= '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
    "DIGIT": rf"[{DIGIT}]",
    # • ALPHANUM ::= ALPHA | DIGIT
    "ALPHANUM": rf"[{ALPHA}{DIGIT}]",
    # • SPACE ::= ' '
    "SPACE": rf"[{SPACE}]",
    # • HYPHEN ::= '-'
    "HYPHEN": rf"[{HYPHEN}]",
    # • FEF ::= Carriage_return | Line_Feed
    "FEF": r"[\n\r]",
    # • SEP ::= 1{ SPACE | FEF }
    "SEP": r"[\s\r\n]",
    # • SPECIAL ::= SPACE | '(' | ')' | '?' | ':' | '.' | ',' | ''' | '=' | '+' | '/'
    "SPECIAL": rf"[{SPACE}{re.escape(SPECIAL)}]",
    # • CHARACTER ::= ALPHA | DIGIT | SPECIAL | FEF | HYPHEN
    "CHARACTER": rf"[{ALPHA}{DIGIT}{SPACE}{re.escape(SPECIAL)}\n\r{HYPHEN}]",
    # • LIM_CHAR ::= ALPHA | DIGIT | SPECIAL | FEF
    "LIM_CHAR": rf"[{ALPHA}{DIGIT}{SPACE}{re.escape(SPECIAL)}\n\r]",
    # • START-OF-FIELD ::= HYPHEN
    #Note: LIM_CHAR represents any allowed character except HYPHEN which is reserved to
    #indicate the start of a field. On the contrary, CHARACTER represents any allowed
    #element of the character set.
}

df = pd.read_csv(os.path.join(PWD, "built_data", "adexp_primary.csv"))

PATTERN = re.compile(r"(\d+)\s?\{\s?([A-Za-z_]+)\s?\}\s?(\d+)?")

def grammar_to_regex(expr: str) -> str:
    def repl(match):
        minimum = int(match.group(1))
        token = match.group(2)
        maximum = int(match.group(3))

        regex = LEXICAL_ITEMS[token]

        if minimum == maximum or maximum is None:
            return f"{regex}{{{minimum}}}"

        return f"{regex}{{{minimum},{maximum}}}"

    return PATTERN.sub(repl, expr)

for row in df.itertuples():
    syntax = str(row.syntax)
    strip_chars = ["'", "‘", "”", "\"", "“", "’"]
    for char in strip_chars:
        syntax = syntax.replace(char, "")
    logger.debug(syntax)

    # Character limit
    char_limit = re.search(r"(\d+)\{\s?([A-Za-z_]+)\s?\}(\d+)", syntax)
    if char_limit:
        if LEXICAL_ITEMS.get(char_limit.group(2)):
            grammar_regex = grammar_to_regex(syntax)
            logger.success(f"Grammar regex: {grammar_regex}")
        else:
            logger.error(f"Unknown lexical item: {char_limit.group(2)}")
        logger.info(char_limit)

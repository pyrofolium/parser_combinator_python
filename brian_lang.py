from typing import Tuple
from enum import Enum
from lib import (
    LetterParser,
    OptionalParser,
    RepeatParser,
    LazyParser,
    ConvertToType,
    IgnoreParser,
)
from functools import reduce


class OPERATOR(Enum):
    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4


FLOAT = float

EXPRESSION = Tuple[OPERATOR, "EXPRESSION", "EXPRESSION"] | FLOAT

AnyDigitParser = reduce(
    lambda acc, x: acc | x, [LetterParser(str(i)) for i in range(10)]
)
sign_parser = LetterParser("-")
point_parser = LetterParser(".")
float_parser = ConvertToType(
    OptionalParser(sign_parser)
    + RepeatParser(AnyDigitParser)
    + OptionalParser(point_parser + RepeatParser(AnyDigitParser)),
    lambda x: float("".join(x)),
)
operator_parser = reduce(
    lambda acc, x: acc | x, [LetterParser(i) for i in ("+", "-", "*", "/")]
)
space_parser = IgnoreParser(OptionalParser(RepeatParser(LetterParser(" "))))
expression_parser = (
    space_parser
    + (
        ConvertToType(
            IgnoreParser(LetterParser("("))
            + space_parser
            + LazyParser(lambda: expression_parser)
            + space_parser
            + IgnoreParser(LetterParser(")")),
            lambda x: x,
        )
        * ConvertToType(
            float_parser
            + OptionalParser(
                space_parser
                + operator_parser
                + space_parser
                + RepeatParser(LazyParser(lambda: expression_parser))
            ),
        )
    )
    + space_parser
)

print(expression_parser.parse("5 / 1 * 4)"))

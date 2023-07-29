from abc import ABC
from functools import reduce
from typing import Union, List, Dict, Optional, Tuple, Any, Callable, TypeVar, Generic

JSON = Union[str, float, bool, List["JSON"], Dict[str, "JSON"]]

T = TypeVar['T']


# type class for parser combinators.
# parser combinators are functions that take an input string and return a token and the rest of the string
# parser combinators can be composed via + and (|| or *).
class ParserCombinator(ABC):
    def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
        pass

    # when adding two parsers together it's like parsing one after another
    def __add__(self, other: "ParserCombinator") -> "ParserCombinator":
        origin = self

        class Result(ParserCombinator):
            def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
                first = origin.parse(input_str)
                if first is not None:
                    first_token, rest = first
                    second = other.parse(rest)
                    if second is None:
                        return None
                    else:
                        second_token, second_rest = second
                        return first_token + second_token, second_rest
                else:
                    return None

        return Result()

    # when multiplying two parsers it's parsing with the first parser then if that fails parse with
    # with the second parser only one parser is executed.
    def __mul__(self, other: "ParserCombinator") -> "ParserCombinator":
        origin = self

        class Result(ParserCombinator):
            def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
                first = origin.parse(input_str)
                if first is not None:
                    return first
                else:
                    return other.parse(input_str)

        return Result()

    def __or__(self, other: "ParserCombinator") -> "ParserCombinator":
        return self * other


# attempts to parse a single letter


class LetterParser(ParserCombinator):
    def __init__(self, letter: str):
        if len(letter) > 1:
            raise Exception("letter must be one character or less(identity)")
        self.letter = letter

    def parse(self, input_str: str) -> Optional[Tuple[List[str], str]]:
        if len(input_str) == 0:
            return None
        if input_str[0] == self.letter:
            return [self.letter], input_str[1:]
        else:
            return None


# Takes in a parser on construction and returns a new parser that repeatedly applies the parser
# until an error occurs. Then returns the tokens and consumed string before the error occured.
# If First attempt at parsing returns an error then the parser will return None
class RepeatParser(ParserCombinator):
    def __init__(self, other_parser: ParserCombinator):
        self.parser = other_parser

    def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
        result = self.parser.parse(input_str)
        if result is None:
            return None
        else:
            tokens, rest = result
            next_result = self.parse(rest)
            if next_result is None:
                return tokens, rest
            else:
                next_tokens, next_rests = next_result
                return tokens + next_tokens, next_rests


# Eliminates token from the return result, it only returns the rest of consumed string and an empty token list
# turns a regular parser into a parser such that no token is returned but the string is consumed.
class IgnoreParser(ParserCombinator):
    def __init__(self, other_parser: ParserCombinator):
        self.parser = other_parser

    def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
        result = self.parser.parse(input_str)
        if result is None:
            return None
        else:
            tokens, rest = result
            return [], rest


# takes the results of another parser and attempts to convert the tokens returned into another token.
# you supply into a constructor a function that takes a list of tokens and converts those tokens into a new token.
class ConvertToType(ParserCombinator):
    def __init__(
            self, other_parser: ParserCombinator, conversion: Callable[[List[Any]], Any]
    ):
        self.converter = conversion
        self.parser = other_parser

    def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
        result = self.parser.parse(input_str)
        if result is None:
            return None
        else:
            tokens, rest = result
            tokens = [self.converter(tokens)]
            return tokens, rest


# optional parser will take a parser and transform it into a parser that does what the original parser does
# with the change that if the original parser returns a parse error (None) this parser will just return
# empty tokens and the original input_str
# ex: OptionalParser(LetterParser('A')).parse("B")
# letter parser results in an error because it can't parse B into A so you get None
# but optional parser turns that error into ([], "B")
class OptionalParser(ParserCombinator):
    def __init__(self, other_parser: ParserCombinator):
        self.parser = other_parser

    def parse(self, input_str: str) -> Optional[Tuple[List[Any], str]]:
        result = self.parser.parse(input_str)
        if result is None:
            return [], input_str
        else:
            return result


# LazyParser creates a parser that defers parser creation to parse time,
# initialize it by creating your parser expression and placing it in a function,
# then load it into the LazyParser constructor as a parameter (see example below)
# this defers creation of the parser until it comes time to actually Parse the values
# this is useful for parsing recursive types.
# for example:
# parserA = parserB + parserC
# parserC = parserM + parserA
# above will result in parserC undefined error.
# parserA = lambda :parserB + parserC
# parserC = parserM + parserA()
# attempting to fix the above by placing parserA in a lambda to defer the definition results in max recursion error
# fix:
# parserA = LazyParser(lambda: parserB + parserC)
# parserC = parserM + parserA
#
class LazyParser(ParserCombinator):
    def __init__(self, other_parser_function: Callable[[], ParserCombinator]):
        self.parser_creator = other_parser_function

    def parse(self, input_str: str):
        parser = self.parser_creator()
        return parser.parse(input_str)


# below are functions that convert a list of tokens to a token.
# the most primitive parser combinator: LetterParser returns a token that is one letter.
# When you begin composing the LetterParser with other LetterParsers you begin to get
# parsers that return lists of letters. You can use these functions with ConvertToType
# to turn those lists of letters

def tokens_to_dict(input_tokens: List[JSON]) -> Dict[str, JSON]:
    if len(input_tokens) % 2 != 0:
        raise Exception("Must have an even number of tokens to convert to Dict")
    i = 0
    acc = {}
    while i < len(input_tokens):
        key = input_tokens[i]
        if not isinstance(key, str):
            raise Exception("every even index of token must be a string")
        value = input_tokens[i + 1]
        acc[key] = value
        i += 2
    return acc


def string_to_bool(input_tokens: List[str]) -> bool:
    if len(input_tokens) != 1:
        raise Exception("This conversion function is designed to convert one token")
    input_str = input_tokens[0]
    if input_str == "true":
        return True
    elif input_str == "false":
        return False
    else:
        raise Exception(
            f"Invalid bool conversion cannot convert {input_str} to boolean"
        )


def serialize_string_in_string(input_tokens: List[str]) -> str:
    if input_tokens[0] == input_tokens[-1] and input_tokens[0] == '"':
        return "".join(input_tokens[1:-1])
    else:
        raise Exception(
            f"cannot turn {input_tokens} into string, must contain quotes in the string itself"
        )


def null_to_none(input_tokens: List[str]) -> None:
    if len(input_tokens) != 1:
        raise Exception("this function can only convert 1 token")
    input_str = input_tokens[0]
    if input_str == "null":
        return None
    else:
        raise Exception(f"Cannot convert {input_str} to None")

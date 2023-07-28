from functools import reduce

from lib import (
    LetterParser,
    RepeatParser,
    IgnoreParser,
    ConvertToType,
    OptionalParser,
    LazyParser,
    tokens_to_dict,  # parser tokens default to strings. By using these conversion functions with ConvertToType you can change a collection of tokens to another value.
    string_to_bool,
    serialize_string_in_string,
    null_to_none,
)

WordParser = lambda word: ConvertToType(
    reduce(lambda acc, x: acc + x, [LetterParser(letter) for letter in word]),
    lambda tokens: reduce(lambda acc, x: acc + x, tokens),
)
numbers = "1234567890"
a_bunch_of_number_parsers = [LetterParser(i) for i in numbers]
any_number_parser = reduce(lambda acc, x: acc * x, a_bunch_of_number_parsers)
whole_number_parser = RepeatParser(any_number_parser)
dot_parser = OptionalParser(LetterParser("."))
space_parser = OptionalParser(IgnoreParser(RepeatParser(LetterParser(" "))))
float_parser = ConvertToType(
    space_parser
    + whole_number_parser
    + dot_parser
    + OptionalParser(whole_number_parser)
    + space_parser,
    lambda x: float("".join(x)),
)
bool_parser = ConvertToType(
    space_parser + (WordParser("true") * WordParser("false")) + space_parser,
    string_to_bool,
)
letters = "abcdefghijklmnopqrstuvwxyz"
upper_case = letters.upper()
symbols = "!@#$%^&*()-+[]{};'<>,./? "
string_content_letter_parsers = [
    LetterParser(i) for i in letters + upper_case + symbols
]
string_content_parser = WordParser('\\"') * reduce(
    lambda acc, x: x * acc, string_content_letter_parsers
)
quote_parser = LetterParser('"')
string_parser = ConvertToType(
    space_parser
    + quote_parser
    + OptionalParser(RepeatParser(string_content_parser))
    + quote_parser
    + space_parser,
    serialize_string_in_string,
)
null_parser = ConvertToType(
    space_parser + WordParser("null") + space_parser, null_to_none
)
json_parser = LazyParser(
    lambda: space_parser
    + (
        float_parser
        * bool_parser
        * string_parser
        * array_parser
        * object_parser
        * null_parser
    )
    + space_parser
)
array_element_parser = OptionalParser(
    RepeatParser(json_parser + IgnoreParser(LetterParser(",")))
) + OptionalParser(json_parser)
array_parser = ConvertToType(
    space_parser
    + IgnoreParser(LetterParser("["))
    + space_parser
    + array_element_parser
    + space_parser
    + IgnoreParser(LetterParser("]"))
    + space_parser,
    lambda x: x,
)
object_element_parser = (
    string_parser
    + space_parser
    + IgnoreParser(LetterParser(":"))
    + space_parser
    + json_parser
    + space_parser
)
object_element_parser_with_comma = (
    object_element_parser + IgnoreParser(LetterParser(",")) + space_parser
)
full_object_element_parser = (
    RepeatParser(object_element_parser_with_comma) + object_element_parser
) * object_element_parser
object_parser = ConvertToType(
    space_parser
    + IgnoreParser(LetterParser("{"))
    + space_parser
    + full_object_element_parser
    + space_parser
    + IgnoreParser(LetterParser("}"))
    + space_parser,
    tokens_to_dict,
)

print(bool_parser.parse("true"))
print(bool_parser.parse("    false    "))
print(float_parser.parse("10123.1  asdsdas "))
print(null_parser.parse("     null     "))
print(string_parser.parse('     "hello world"'))
print(string_parser.parse('   ""    '))
print(
    array_parser.parse('    [ true, 21.222, false,     "hello world     "    ]      ')
)
print(array_parser.parse("    [1]      "))
print(array_parser.parse("    [    ]      "))
print(
    object_parser.parse(
        '   { "hello"   :      1, "world"   :2, "boom": [1,2,3, {"bam": "wam"}]    }   '
    )
)
print(
    json_parser.parse(
        '{"hello": [[[[{"hello": "world", "test": null, "more": 1.2334234, "bam": [[["hello"], 1]]}]]]]}'
    )
)
print(json_parser.parse("null"))
print(json_parser.parse("true"))
print(json_parser.parse("1.2334544"))
print(json_parser.parse('[1,2,3,4,5, {"whateve": true}]'))

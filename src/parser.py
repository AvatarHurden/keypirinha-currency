from .parsy import regex, generate, alt, string, seq, Parser, Result
import operator

# Grammar
#
# prog := sources (to_key? destinations)? extra?
#
# to_key := 'to' | 'in' | ':'
#
# destinations := cur_code sep destinations | cur_code
#
# sep := ',' | '&' | 'and'
# cur_code := ([^0-9\s+-/*^()]+)\b(?<!to|in|:)
#
# extra := ('+' | '-' | '*' | '/' | '**' | '^' ) expr
#
# sources := source ('+' | '-') sources | source
# source := '(' source ')'
#        | cur_code expr
#        | expr (cur_code?)
#
# expr := add_expr
# add_expr := mult_expr | add_expr ('+' | '-') mult_expr
# mult_expr := exp_expr | mult_expr ('*' | '/') exp_expr
# exp_expr := unary_expr | exp_expr ('^' | '**') unary_expr
# unary_expr := operand | ('-' | '+') unary_expr
# operand := number | '(' expr ')'
#
# number := (0|[1-9][0-9]*)([.,][0-9]+)?([eE][+-]?[0-9]+)?


class ParserProperties(object):

    to_keywords = ['to', 'in', ':']
    sep_keywords = [',', '&', 'and']

    def __init__(self):
        pass


def make_parser(properties):
    whitespace = regex(r'\s*')
    lexeme = lambda p: p << whitespace

    s = lambda p: lexeme(string(p))
    numberRegex = r'(0|[1-9][0-9]*)([.,][0-9]+)?([eE][+-]?[0-9]+)?'
    number = lexeme(regex(numberRegex)
                    .map(lambda x: x.replace(',', '.'))
                    .map(float).desc('a number'))

    lparen = lexeme(string('('))
    rparen = lexeme(string(')'))

    math_symbols = '+-/*^(),&:'

    def to_parser():
        return alt(*[s(keyword) for keyword in properties.to_keywords])

    def sep_parser():
        return alt(*[s(keyword) for keyword in properties.sep_keywords])

    @generate
    def code():
        @Parser
        def code(stream, index):
            origIndex = index
            word = ''
            while index < len(stream):
                item = stream[index]
                if item.isdigit() or item.isspace() or item in math_symbols:
                    break
                word += item
                index += 1
            else:
                if len(word) == 0:
                    return Result.failure(index, 'currency code')
                return Result.success(index, word)

            if len(word) == 0:
                return Result.failure(index, 'currency code')

            if word in properties.to_keywords or word in properties.sep_keywords:
                return Result.failure(origIndex, word + ' is a reserved keyword')
            return Result.success(index, word)

        return (yield lexeme(code))

    def left_binary_parser(operators, left):
        @generate
        def parser():
            add_op = alt(*[lexeme(string(p)) for p in operators.keys()])

            def combine(op1, op, op2):
                if op in operators:
                    return operators[op](op1, op2)
                return op1

            def recurse(first):
                @generate
                def rec():
                    op = yield add_op
                    op2 = yield left
                    ret = combine(first, op, op2)
                    rec2 = yield recurse(ret)
                    if rec2 is not None:
                        return rec2
                    return ret
                return rec.optional()

            op1 = yield left
            ret = yield recurse(op1)
            if ret is not None:
                return ret
            return op1
        return parser

    @generate
    def expression():
        return (yield add_expr)

    @generate
    def add_expr():
        return (yield left_binary_parser({'+': operator.add, '-': operator.sub}, mult_expr))

    @generate
    def mult_expr():
        return (yield left_binary_parser({'*': operator.mul, '/': operator.truediv}, exp_expr))

    @generate
    def exp_expr():
        return (yield left_binary_parser({'^': operator.pow, '**': operator.pow}, unary_expr))

    @generate
    def unary_expr():
        @generate
        def unary():
            operation = yield s('-') | s('+')
            value = yield unary_expr
            if operation == '-':
                return -value
            else:
                return value
        return (yield operand | unary)

    @generate
    def operand():
        return (yield (number | (lparen >> expression << rparen)))

    @generate
    def source():
        amount_first = seq(expression, code.optional())
        curr_first = seq(code, expression.optional()).map(lambda a: a[::-1])
        pure = (amount_first | curr_first).map(lambda a: {
            'amount': a[0],
            'currency': a[1]
        })
        ret = yield pure | lparen >> source << rparen
        return ret

    @generate
    def sources():
        first = yield lexeme(source)

        @generate
        def more_sources():
            op = yield (s('+') | s('-'))
            rest = yield sources
            return op, rest

        more = yield more_sources.optional()
        rest = None
        if more:
            op, rest = more
            if op == '-':
                rest[0]['amount'] *= -1
        return [first] + (rest if rest else [])

    @generate
    def destinations():
        first = yield lexeme(code)
        rest = yield (sep_parser() >> destinations).optional()
        return [{'currency': first}] + (rest if rest else [])

    @generate
    def extra():
        operations = {'+': operator.add,
                      '-': operator.sub,
                      '**': operator.pow,
                      '*': operator.mul,
                      '/': operator.truediv,
                      '^': operator.pow}
        op = yield alt(*[s(k).result(v) for (k, v) in operations.items()])
        expr = yield expression
        return {
            'operation': op,
            'value': expr
        }

    @generate
    def parser():
        source = yield sources
        destination = yield (to_parser().optional() >> destinations).optional()
        extras = yield extra.optional()
        if extras:
            op = extras['operation']
            value = extras['value']
            for s in source:
                s['amount'] = op(s['amount'], value)
        return {
            'sources': source,
            'destinations': destination
        }

    return parser

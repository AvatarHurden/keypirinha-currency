from .parsy import regex, letter, generate, alt, string
import operator

# Grammar
#
# prog := sources (to_key cur_code)?
#
# to_key := 'to' | 'in' | ':'
# cur_code := ([^0-9\s+-/*^()]+)\b(?<!to|in|:)
#
# sources := source (+-) sources | source
# source := '(' source ')'
#        | cur_code expr
#        | expr (cur_code?)
#
# expr := math

toPrint = None

whitespace = regex(r'\s*')
lexeme = lambda p: p << whitespace

s = lambda p: lexeme(string(p))
numberRegex = r'-?(0|[1-9][0-9]*)([.,][0-9]+)?([eE][+-]?[0-9]+)?'
number = lexeme(regex(numberRegex).map(lambda x: x.replace(',', '.')).map(float))

lparen = lexeme(string('('))
rparen = lexeme(string(')'))

math_symbols = '+-/*^()'
to_keywords = ['to', 'in', ':']

conversion = alt(*[s(keyword) for keyword in to_keywords])


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
            return Result.success(index, word)

        if word in to_keywords:
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


expression = add_expr


parser = expression

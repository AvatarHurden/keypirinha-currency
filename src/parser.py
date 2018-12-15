from .parsy import regex, letter, generate, alt, string
import operator

toPrint = None

whitespace = regex(r'\s*')
lexeme = lambda p: p << whitespace

numberRegex = r'-?(0|[1-9][0-9]*)([.,][0-9]+)?([eE][+-]?[0-9]+)?'
number = lexeme(regex(numberRegex).map(float))

lparen = lexeme(string('('))
rparen = lexeme(string(')'))


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
    return (yield left_binary_parser({'^': operator.pow, '**': operator.pow}, operand))


@generate
def operand():
    return (yield (number | (lparen >> expression << rparen)))


expression = add_expr

code = lexeme(letter.many().concat())

parser = expression

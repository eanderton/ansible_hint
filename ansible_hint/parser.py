# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
import json
from collections import OrderedDict


class UnicodeRepr(object):
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return self.__unicode__()


class ParseError(Exception, UnicodeRepr):
    def __init__(self, position, msg):
        self.position = position
        self.msg = msg

    def __unicode__(self):
        return '({}, {}): {}'.format(
                self.position[0] + 1, self.position[1] + 1, self.msg)


class AstNode(UnicodeRepr):
    def __init__(self, name, text, pos, *children):
        self.name = name
        self.text = text
        self.pos = pos
        self.children = children

    def to_dict(self):
        result = OrderedDict()
        result.update(name=self.name)
        result.update(text=self.text)
        result.update(pos=self.pos)
        if self.children:
            result.update(children=map(lambda x: x.to_dict(), self.children))
        return result

    def to_json(self, indent=4):
        return json.dumps(self.to_dict(), indent=indent)

    def __unicode__(self):
        return json.dumps(self.to_dict())


class AstResult(UnicodeRepr):
    def __init__(self, value=True):
        if isinstance(value, list):
            self._state = True
            self._data = value
        elif isinstance(value, AstNode):
            self._state = True
            self._data = [value]
        else:
            self._state = bool(value)
            self._data = []

    def __bool__(self):
        return self._state

    def __nonzero__(self):
        return self._state

    def __unicode__(self):
        return json.dumps(map(lambda x: x.to_dict(), self._data))

    def append(self, *items):
        self._data.extend(items)

    def combine(self, other):
        self._data.extend(other._data)

    def to_json(self, indent=4):
        return json.dumps(map(lambda x: x.to_dict(), self._data), indent=indent)

    @property
    def items(self):
        return self._data


class ParseCtx(object):
    def __init__(self, declarations=None):
        self.reset('')
        self.declarations = {}
        if declarations is not None:
            for decl in declarations:
                self.add_decl(decl)

    def reset(self, text):
        self.text = text
        self.pos = 0
        self.col = 0
        self.line = 0

    def eof(self, num=1):
        end = self.pos + num - 1
        return end >= len(self.text)

    def peek(self, num=1):
        end = self.pos + num
        return self.text[self.pos:end]

    def next(self, num=1):
        start = self.pos
        end = self.pos + num
        next_text = self.text[start:end]
        for ch in next_text:
            if ch == '\n':
                self.line += 1
                self.col = 0
            else:
                self.col += 1
        self.pos = end
        return next_text

    def clone(self):
        other = ParseCtx()
        other.update(self)
        return other

    def update(self, other):
        self.text = other.text
        self.pos = other.pos
        self.line = other.line
        self.col = other.col
        self.declarations = other.declarations

    def position(self):
        return (self.line, self.col)

    def get_decl(self, name):
        return self.declarations[name]

    def add_decl(self, decl):
        self.declarations[decl.name] = decl

    def get_text(self, terminating_ctx):
        start = self.pos
        end = terminating_ctx.pos
        return self.text[start:end]


class ProductionBase(UnicodeRepr):
    def __init__(self):
        self.on_fail_msg = None

    def eval_impl(self, ctx):
        """ To be overridden """
        return AstResult(False)

    def evaluate(self, ctx):
        result = self.eval_impl(ctx)
        if not result and self.has_fail_msg():
            raise ParseError(ctx.position(), self.on_fail_msg)
        return result

    def has_fail_msg(self):
        return self.on_fail_msg is not None

    def on_fail(self, msg):
        self.on_fail_msg = msg
        return self  # allow chain call

    def to_unicode(self):
        """ To be overridden """
        return 'ProductionBase()'

    def __unicode__(self):
        result = self.to_unicode()
        if self.has_fail_msg():
            result += '.on_fail("{}")'.format(self.on_fail_msg)
        return result


class Eof(ProductionBase):
    def __init__(self):
        ProductionBase.__init__(self)

    def eval_impl(self, ctx):
        return AstResult(ctx.eof())

    def to_unicode(self):
        return 'Eof()'


class Any(ProductionBase):
    def __init__(self):
        ProductionBase.__init__(self)

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(False)
        ctx.next()
        return AstResult(True)

    def to_unicode(self):
        return 'Any()'


class CharRange(ProductionBase):
    def __init__(self, start_ch, end_ch=None):
        ProductionBase.__init__(self)
        self.start_ch = start_ch
        if not end_ch:
            self.end_ch = start_ch
        else:
            self.end_ch = end_ch

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(False)
        ch = ctx.peek()
        if ch >= self.start_ch and ch <= self.end_ch:
            ctx.next()
            return AstResult(True)
        return AstResult(False)

    def to_unicode(self):
        return 'CharRange("{}","{}")'.format(self.start_ch, self.end_ch)


class Literal(ProductionBase):
    def __init__(self, text):
        ProductionBase.__init__(self)
        self.text = text

    def eval_impl(self, ctx):
        ll = len(self.text)
        if ctx.eof(ll):
            return AstResult(False)
        if ctx.peek(ll) == self.text:
            ctx.next(ll)
            return AstResult(True)
        return AstResult(False)

    def to_unicode(self):
        return 'Literal("{}")'.format(self.text)


class Negate(ProductionBase):
    def __init__(self, production):
        """ matches next char if production is false """
        ProductionBase.__init__(self)
        self.production = production

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(False)
        eval_ctx = ctx.clone()
        if not self.production.evaluate(eval_ctx):
            ctx.next()
            return AstResult(True)
        return AstResult(False)

    def to_unicode(self):
        return 'Negate({})'.format(self.production)


class Optional(ProductionBase):
    def __init__(self, production):
        ProductionBase.__init__(self)
        self.production = production

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(True)
        eval_ctx = ctx.clone()
        result = self.production.evaluate(eval_ctx)
        if result:
            ctx.update(eval_ctx)
            return result
        return AstResult(True)

    def to_unicode(self):
        return 'Optional({})'.format(self.production)


class OneOf(ProductionBase):
    def __init__(self, text):
        ProductionBase.__init__(self)
        self.text = text

    def eval_impl(self, ctx):
        for ch in self.text:
            if ctx.peek() == ch:
                ctx.next()
                return AstResult(True)
        return AstResult(False)

    def to_unicode(self):
        return 'OneOf("{}")'.format(self.text)


class Sequence(ProductionBase):
    def __init__(self, *items):
        ProductionBase.__init__(self)
        self.items = items

    def eval_impl(self, ctx):
        eval_ctx = ctx.clone()
        result = AstResult()
        for item in self.items:
            eval_result = item.evaluate(eval_ctx)
            if not eval_result:
                return AstResult(False)
            result.combine(eval_result)
        ctx.update(eval_ctx)
        return result

    def to_unicode(self):
        return 'Sequence({})'.format(','.join(map(unicode, self.items)))


class OrGroup(ProductionBase):
    def __init__(self, *items):
        ProductionBase.__init__(self)
        self.items = items

    def eval_impl(self, ctx):
        for item in self.items:
            eval_ctx = ctx.clone()
            result = item.evaluate(eval_ctx)
            if result:
                ctx.update(eval_ctx)
                return result
        return AstResult(False)

    def to_unicode(self):
        return 'OrGroup({})'.format(','.join(map(unicode, self.items)))


class OneOrMore(ProductionBase):
    def __init__(self, production):
        ProductionBase.__init__(self)
        self.production = production

    def eval_impl(self, ctx):
        if ctx.eof(): return AstResult(False)
        eval_ctx = ctx.clone()
        result = self.production.evaluate(eval_ctx)
        if not result:
            return AstResult(False)
        ctx.update(eval_ctx)
        while not ctx.eof():
            eval_ctx = eval_ctx.clone()
            eval_result = self.production.evaluate(eval_ctx)
            if not eval_result:
                break
            ctx.update(eval_ctx)
            result.combine(eval_result)
        return result

    def to_unicode(self):
        return 'OneOrMore({})'.format(self.production)


class OneOrMoreUntil(ProductionBase):
    def __init__(self, term):
        ProductionBase.__init__(self)
        self.term = term

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(False)
        eval_ctx = ctx.clone()
        if self.term.evaluate(eval_ctx):
            return AstResult(False)
        while True:
            ctx.next()
            eval_ctx = ctx.clone()
            if self.term.evaluate(eval_ctx):
                break
            elif eval_ctx.eof():
                return AstResult(False)
        return AstResult(True)

    def to_unicode(self):
        return 'OneOrMoreUntil({})'.format(self.term)



class ZeroOrMore(ProductionBase):
    def __init__(self, production):
        ProductionBase.__init__(self)
        self.production = production

    def eval_impl(self, ctx):
        result = AstResult()
        while not ctx.eof():
            eval_ctx = ctx.clone()
            eval_result = self.production.evaluate(eval_ctx)
            if not eval_result:
                break
            ctx.update(eval_ctx)
            result.combine(eval_result)
        return result

    def to_unicode(self):
        return 'ZeroOrMore({})'.format(self.production)


class ZeroOrMoreUntil(ProductionBase):
    def __init__(self, term):
        ProductionBase.__init__(self)
        self.term = term

    def eval_impl(self, ctx):
        if ctx.eof():
            return AstResult(True)
        eval_ctx = ctx.clone()
        while True:
            if self.term.evaluate(eval_ctx):
                break
            elif eval_ctx.eof():
                return AstResult(False)
            ctx.next()
            eval_ctx = ctx.clone()
        return AstResult(True)

    def to_unicode(self):
        return 'ZeroOrMoreUntil({})'.format(self.term)


class Decl(ProductionBase):
    def __init__(self, name, *sequence_items):
        ProductionBase.__init__(self)
        self.name = name
        if len(sequence_items) == 1:
            self.prod = sequence_items[0]
        else:
            self.prod = Sequence(*sequence_items)

    def eval_impl(self, ctx):
        eval_ctx = ctx.clone()
        eval_result = self.prod.evaluate(eval_ctx)
        if eval_result:
            ast = AstNode(self.name, ctx.get_text(eval_ctx), ctx.position(), *eval_result.items)
            ctx.update(eval_ctx)
            return AstResult(ast)
        return AstResult(False)

    def to_unicode(self):
        return 'Decl("{}", {})'.format(self.name, self.prod)


class UnreportedDecl(ProductionBase):
    def __init__(self, name, *sequence_items):
        ProductionBase.__init__(self)
        self.name = name
        if len(sequence_items) == 1:
            self.prod = sequence_items[0]
        else:
            self.prod = Sequence(*sequence_items)

    def eval_impl(self, ctx):
        if self.prod.evaluate(ctx):
            return AstResult(True)
        else:
            return AstResult(False)

    def to_unicode(self):
        return 'UnreportedDecl("{}", {})'.format(self.name, self.prod)


class ExpandedDecl(ProductionBase):
    def __init__(self, name, *sequence_items):
        ProductionBase.__init__(self)
        self.name = name
        if len(sequence_items) == 1:
            self.prod = sequence_items[0]
        else:
            self.prod = Sequence(*sequence_items)

    def eval_impl(self, ctx):
        return self.prod.evaluate(ctx)

    def to_unicode(self):
        return 'ExpandedDecl("{}", {})'.format(self.name, self.prod)


class DeclRef(ProductionBase):
    def __init__(self, name):
        ProductionBase.__init__(self)
        self.name = name

    def eval_impl(self, ctx):
        decl = ctx.get_decl(self.name)
        return decl.evaluate(ctx)

    def to_unicode(self):
        return 'DeclRef("{}")'.format(self.name)

class Lookahead(ProductionBase):
    def __init__(self, item):
        ProductionBase.__init__(self)
        self.item = item

    def eval_impl(self, ctx):
        result = item.evaluate(ctx)
        if result:
            return AstResult(True)
        else:
            return AstResult(False)

    def to_unicode(self):
        return 'Lookahead({})'.format(self.item)

class Debug(ProductionBase):
    def __init__(self, msg, item):
        ProductionBase.__init__(self)
        self.msg = msg
        self.item = item

    def eval_impl(self, ctx):
        result = self.item.evaluate(ctx)
        if result:
            print('DEBUG(pass):', self.msg, result.items[0].text)
        else:
            print('DEBUG(fail):', self.msg, ctx.text[ctx.pos:ctx.pos+10] + '...')
        return result

    def to_unicode(self):
        return 'Debug("{}", {})'.format(self.msg, self.item)


class Fail(ProductionBase):
    def __init__(self, msg):
        ProductionBase.__init__(self)
        self.msg = msg

    def eval_impl(self, ctx):
        raise ParseError(ctx.position(), self.msg)

    def to_unicode(self):
        return 'Fail("{}")'.format(self.msg)


class BasicParser(UnicodeRepr):
    def __init__(self, decls):
        self.decls = decls

    def parse(self, decl, text):
        ctx = ParseCtx(self.decls)
        ctx.reset(text)
        return ctx.get_decl(decl).evaluate(ctx)

    def __unicode__(self):
        return '\n'.join(map(unicode, self.decls))

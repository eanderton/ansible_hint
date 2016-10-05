# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
from unittest import TestCase
from ansible_hint.tests.base import ParserTestBase
import ansible_hint.parser as ahp
import json

class TestAstResult(TestCase):
    def setUp(self):
        self.data = [
                ahp.AstNode('one', 'one', (0,0)),
                ahp.AstNode('two', 'two', (0, 3)),
                ahp.AstNode('three', 'three', (0, 6))
            ]

    def test_init(self):
        result = ahp.AstResult()
        self.assertTrue(result)

        result = ahp.AstResult(False)
        self.assertFalse(result)

        data_str = json.dumps([{
                'name': 'one', 'text': 'one', 'pos': [0, 0]
            },{
                'name': 'two', 'text': 'two', 'pos': [0, 3]
            },{
                'name': 'three', 'text': 'three', 'pos': [0, 6]
            }])
        result = ahp.AstResult(self.data)
        self.assertEquals(unicode(result), data_str)
        self.assertTrue(result)

    def test_data(self):
        result = ahp.AstResult()
        result.append(*self.data)

        for ii, item in enumerate(result.items):
            self.assertIs(item, self.data[ii])


class TestParseCtx(TestCase):
    def test_init(self):
        ctx = ahp.ParseCtx()
        self.assertTrue(ctx.eof())
        self.assertEquals(ctx.pos, 0)
        self.assertEquals(ctx.position(), (0, 0))

    def test_init_with_text(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobarbaz'
        self.assertFalse(ctx.eof())
        self.assertEquals(ctx.pos, 0)
        self.assertEquals(ctx.position(), (0, 0))

    def test_peek(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobarbaz'
        self.assertEquals(ctx.peek(), 'f')
        self.assertEquals(ctx.peek(6), 'foobar')

    def test_next_ch(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobarbaz'
        self.assertEquals(ctx.next(), 'f')
        self.assertFalse(ctx.eof())
        self.assertEquals(ctx.peek(), 'o')

    def test_next_literal(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobarbaz'
        self.assertEquals(ctx.next(6), 'foobar')
        self.assertFalse(ctx.eof())
        self.assertEquals(ctx.peek(3), 'baz')

    def test_position(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'hello\nmultiline\nworld'

        self.assertEquals(ctx.next(5), 'hello')
        self.assertEquals(ctx.position(), (0, 5))
        self.assertEquals(ctx.text[ctx.pos:], '\nmultiline\nworld')
        self.assertEquals(ctx.next(), '\n')
        self.assertEquals(ctx.position(), (1, 0))

        self.assertEquals(ctx.next(9), 'multiline')
        self.assertEquals(ctx.position(), (1, 9))
        self.assertEquals(ctx.next(), '\n')
        self.assertEquals(ctx.position(), (2, 0))

        self.assertEquals(ctx.next(5), 'world')
        self.assertEquals(ctx.position(), (2, 5))
        self.assertTrue(ctx.eof())

    def test_clone(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'hello\nmultiline\nworld'

        other = ctx.clone()
        self.assertEquals(ctx.text, other.text)
        self.assertEquals(ctx.pos, other.pos)
        self.assertEquals(ctx.line, other.line)
        self.assertEquals(ctx.col, other.col)
        self.assertIs(ctx.declarations, other.declarations)

    def test_clone_mutable(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'hello\nmultiline\nworld'

        other = ctx.clone()
        other.text = 'foobarbaz'
        other.pos = 500
        other.line = 55
        other.col = 99
        other.declarations = {}

        self.assertNotEquals(ctx.text, other.text)
        self.assertNotEquals(ctx.pos, other.pos)
        self.assertNotEquals(ctx.line, other.line)
        self.assertNotEquals(ctx.col, other.col)
        self.assertIsNot(ctx.declarations, other.declarations)

    def test_update(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'hello\nmultiline\nworld'

        other = ctx.clone()
        other.text = 'foobarbaz'
        other.pos = 500
        other.line = 55
        other.col = 99
        other.declarations = {}

        ctx.update(other)
        self.assertEquals(ctx.text, other.text)
        self.assertEquals(ctx.pos, other.pos)
        self.assertEquals(ctx.line, other.line)
        self.assertEquals(ctx.col, other.col)
        self.assertIs(ctx.declarations, other.declarations)


class TestParseProduction(ParserTestBase, TestCase):
    def test_eof(self):
        ctx = ahp.ParseCtx()
        prod = ahp.Eof()
        self.assertTrue(prod.evaluate(self.ctx))

    def test_eof(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'
        prod = ahp.Any()
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

    def test_char_range(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'

        prod = ahp.CharRange('a', 'z')
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

        prod = ahp.CharRange('A', 'Z')
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

    def test_literal(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'

        prod = ahp.Literal('f')
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

        prod = ahp.Literal('x')
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

        prod = ahp.Literal('xxxx')
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

        prod = ahp.Literal('oobar')
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '', (0, 6))
        self.assertTrue(ctx.eof())

    def test_negate(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'

        prod = ahp.Negate(ahp.Literal('f'))
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'f', (0, 0))

        prod = ahp.Negate(ahp.Literal('x'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

    def test_optional(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'

        prod = ahp.Optional(ahp.Literal('x'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'f', (0, 0))

        prod = ahp.Optional(ahp.Literal('f'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

    def test_one_of(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foobar'

        prod = ahp.OneOf('xfyz')
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

        prod = ahp.OneOf('12345')
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'o', (0, 1))

    def test_sequence(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foo\nbar\nbaz'

        newline = ahp.Literal('\n')
        prod = ahp.Sequence(
                ahp.Literal('foo'), newline, ahp.Literal('bar'), newline, ahp.Literal('baz'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '', (2, 3))
        self.assertTrue(ctx.eof())

        ctx = ahp.ParseCtx()
        ctx.text = 'foo\nbar\nbaz'
        prod = ahp.Sequence(
                ahp.Literal('foo'), newline, ahp.Literal('bar'), newline, ahp.Literal('gorf'))
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 'f', (0,0))


    def test_or_group(self):
        ctx = ahp.ParseCtx()
        ctx.text = 'foo\nbar\nbaz'

        newline = ahp.Literal('\n')
        prod = ahp.OrGroup(
                ahp.Literal('foo'), ahp.Literal('bar'), ahp.Literal('baz'), newline)
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '\n', (0, 3))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'b', (1, 0))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '\n', (1, 3))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, 'b', (2, 0))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '', (2, 3))
        self.assertTrue(ctx.eof())

        ctx = ahp.ParseCtx()
        ctx.text = 'shazbot'
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, 's', (0, 0))

    def test_one_or_more(self):
        ctx = ahp.ParseCtx()
        ctx.text = '12345.67890'

        prod = ahp.OneOrMore(ahp.CharRange('0', '9'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 5))
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 5))

    def test_one_or_more_until(self):
        ctx = ahp.ParseCtx()
        ctx.text = '12345.67890'

        prod = ahp.OneOrMoreUntil(ahp.Literal('.'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 5))
        self.assertFalse(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 5))

    def test_zero_or_more(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345.67890'

        prod = ahp.ZeroOrMore(ahp.CharRange('0', '9'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '$', (0, 0))
        ctx.next()
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 6))

    def test_zero_or_more_until(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345.67890'

        prod = ahp.ZeroOrMoreUntil(ahp.Literal('.'))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 6))
        self.assertTrue(prod.evaluate(ctx))
        self.assertPeek(ctx, '.', (0, 6))

    def test_decl(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345 $67890'

        prod = ahp.Decl('money', ahp.Literal('$'), ahp.OneOrMore(ahp.CharRange('0', '9')))
        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, ' ', (0, 6))
        self.assertAst(result, [ahp.AstNode('money', '$12345', (0,0))])

        ctx.next()
        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, '', (0, 13))
        self.assertAst(result, [ahp.AstNode('money', '$67890', (0, 7))])

    def test_unreported_decl(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345 $67890'

        ctx.add_decl(ahp.Decl('digits', ahp.OneOrMore(ahp.CharRange('0', '9'))))
        ctx.add_decl(ahp.UnreportedDecl('money', ahp.Literal('$'), ahp.DeclRef('digits')))
        prod = ctx.get_decl('money')

        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, ' ', (0, 6))
        self.assertAst(result, [])

        ctx.next()
        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, '', (0, 13))
        self.assertAst(result, [])

    def test_expanded_decl(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345 $67890'

        ctx.add_decl(ahp.Decl('digits', ahp.OneOrMore(ahp.CharRange('0', '9'))))
        ctx.add_decl(ahp.ExpandedDecl('money', ahp.Literal('$'), ahp.DeclRef('digits')))
        prod = ctx.get_decl('money')

        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, ' ', (0, 6))
        self.assertAst(result, [ahp.AstNode('digits', '12345', (0,1))])

        ctx.next()
        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, '', (0, 13))
        self.assertAst(result, [ahp.AstNode('digits', '67890', (0,8))])

    def test_decl_ref(self):
        ctx = ahp.ParseCtx()
        ctx.text = '$12345 $67890'

        ctx.add_decl(ahp.Decl('digits', ahp.OneOrMore(ahp.CharRange('0', '9'))))
        ctx.add_decl(ahp.Decl('money', ahp.Literal('$'), ahp.DeclRef('digits')))
        prod = ahp.DeclRef('money')

        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, ' ', (0, 6))
        self.assertAst(result, [
                ahp.AstNode('money', '$12345', (0, 0), ahp.AstNode('digits', '12345', (0, 1)))
            ])

        ctx.next()
        result = prod.evaluate(ctx)
        self.assertTrue(result)
        self.assertPeek(ctx, '', (0, 13))
        self.assertAst(result, [
                    ahp.AstNode('money', '$67890', (0, 7), ahp.AstNode('digits', '67890', (0, 8)))
            ])

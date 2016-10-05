# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
import unittest
from ansible_hint.tests.base import ParserTestBase
from ansible_hint.parser import AstNode, ParseError
from ansible_hint.bnf import bnf_parser_decls, BnfParserGenerator

class TestBnfProductions(ParserTestBase, unittest.TestCase):
    def run_parser(self, *args, **kwargs):
        self.assertParser(bnf_parser_decls, *args, **kwargs)

    def run_parser_fail(self, *args, **kwargs):
        self.assertParserFail(bnf_parser_decls, *args, **kwargs)

    def test_hex(self):
        self.run_parser('1234', 'HEXDIGIT', peek='2', pos=(0, 1))

        self.run_parser('23', 'HEX_ESCAPED_CHAR',
            [AstNode('HEX_ESCAPED_CHAR', '23', (0, 0))])

        self.run_parser('4abc', 'UNICODE_ESCAPED_CHAR_16',
            [AstNode('UNICODE_ESCAPED_CHAR_16', '4abc', (0, 0))])

        self.run_parser('def01234', 'UNICODE_ESCAPED_CHAR_32',
            [AstNode('UNICODE_ESCAPED_CHAR_32', 'def01234', (0, 0))])

    def test_octal(self):
        self.run_parser('01234567', 'OCTAL_ESCAPED_CHAR',
            [AstNode('OCTAL_ESCAPED_CHAR', '012', (0, 0))])

    def test_escaped_char(self):
        self.run_parser('\\x42', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\x42', (0, 0),
                    AstNode('HEX_ESCAPED_CHAR', '42', (0, 2)))
            ])

        self.run_parser('\\u201d', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\u201d', (0, 0),
                    AstNode('UNICODE_ESCAPED_CHAR_16', '201d', (0, 2)))
            ])

        self.run_parser('\\Uabcdef01', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\Uabcdef01', (0, 0),
                    AstNode('UNICODE_ESCAPED_CHAR_32', 'abcdef01', (0, 2)))
            ])

        self.run_parser('\\777', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\777', (0, 0),
                    AstNode('OCTAL_ESCAPED_CHAR', '777', (0, 1)))
            ])

        self.run_parser('\\t', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\t', (0, 0),
                    AstNode('SPECIAL_ESCAPED_CHAR', 't', (0, 1)))
            ])

        self.run_parser('\\n', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\n', (0, 0),
                    AstNode('SPECIAL_ESCAPED_CHAR', 'n', (0, 1)))
            ])

        self.run_parser('\\"', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\"', (0, 0),
                    AstNode('SPECIAL_ESCAPED_CHAR', '"', (0, 1)))
            ])

        self.run_parser('\\\\', 'ESCAPED_CHAR', [
                AstNode('ESCAPED_CHAR', '\\\\', (0, 0),
                    AstNode('SPECIAL_ESCAPED_CHAR', '\\', (0, 1)))
            ])

        self.run_parser_fail('\\x', 'ESCAPED_CHAR',
                '(1, 3): Expected two hex digits following "\\x"')

        self.run_parser_fail('\\u', 'ESCAPED_CHAR',
                '(1, 3): Expected four hex digits following "\\u"')

        self.run_parser_fail('\\U', 'ESCAPED_CHAR',
                '(1, 3): Expected eight hex digits following "\\U"')

        self.run_parser_fail('\\', 'ESCAPED_CHAR',
                '(1, 2): Expected escape sequence following "\\"')

    def test_char_range(self):
        self.run_parser('z-', 'CHARNOBRACE', peek='-', pos=(0, 1), ast=[
                AstNode('CHAR', 'z', (0, 0))
            ])

        self.run_parser('a-z-', 'CHARRANGE', peek='-', pos=(0, 3), ast=[
                AstNode('CHARRANGE', 'a-z', (0, 0),
                    AstNode('CHAR', 'a', (0, 0)), AstNode('CHAR', 'z', (0, 2)))
            ])

    def test_range_special(self):
        self.run_parser('[]]', 'range', [
                AstNode('range', '[]]', (0, 0), AstNode('CHARBRACE', ']', (0, 1)))
            ])

        self.run_parser('[]-]', 'range', [
                AstNode('range', '[]-]', (0, 0),
                    AstNode('CHARBRACE', ']', (0, 1)),
                    AstNode('CHARDASH', '-', (0, 2)))
            ])

        self.run_parser('[]-X]', 'range', [
                AstNode('range', '[]-X]', (0, 0),
                    AstNode('CHARBRACE', ']', (0, 1)),
                    AstNode('CHARDASH', '-', (0, 2)),
                    AstNode('CHAR', 'X', (0, 3)))
            ])

    def test_range(self):
        self.run_parser('[a-z]', 'range', [
                AstNode('range', '[a-z]', (0, 0),
                        AstNode('CHARRANGE', 'a-z', (0, 1),
                                AstNode('CHAR', 'a', (0, 1)),
                                AstNode('CHAR', 'z', (0, 3))
                            )
                    )
            ])

        self.run_parser('[a-z-]', 'range', [
                AstNode('range', '[a-z-]', (0, 0),
                        AstNode('CHARRANGE', 'a-z', (0, 1),
                                AstNode('CHAR', 'a', (0, 1)),
                                AstNode('CHAR', 'z', (0, 3))),
                        AstNode('CHAR', '-', (0, 4))
                    )
            ])

        self.run_parser('[a-zA-Z0-9]', 'range', [
                AstNode('range', '[a-zA-Z0-9]', (0, 0),
                        AstNode('CHARRANGE', 'a-z', (0, 1),
                            AstNode('CHAR', 'a', (0, 1)), AstNode('CHAR', 'z', (0, 3))),
                        AstNode('CHARRANGE', 'A-Z', (0, 4),
                            AstNode('CHAR', 'A', (0, 4)), AstNode('CHAR', 'Z', (0, 6))),
                        AstNode('CHARRANGE', '0-9', (0, 7),
                            AstNode('CHAR', '0', (0, 7)), AstNode('CHAR', '9', (0, 9)))
                    )
            ])

        self.run_parser('[a]', 'range', [
                AstNode('range', '[a]', (0, 0), AstNode('CHAR', 'a', (0, 1)))
            ])

        self.run_parser('[qwerty]', 'range', [
                AstNode('range', '[qwerty]', (0, 0),
                        AstNode('CHAR', 'q', (0, 1)),
                        AstNode('CHAR', 'w', (0, 2)),
                        AstNode('CHAR', 'e', (0, 3)),
                        AstNode('CHAR', 'r', (0, 4)),
                        AstNode('CHAR', 't', (0, 5)),
                        AstNode('CHAR', 'y', (0, 6))
                    )
            ])

        self.run_parser('[a-]', 'range', [
                AstNode('range', '[a-]', (0, 0),
                    AstNode('CHAR', 'a', (0, 1)), AstNode('CHAR', '-', (0, 2)))
            ])

        self.run_parser('[]a-]', 'range', [
                AstNode('range', '[]a-]', (0, 0),
                        AstNode('CHARBRACE', ']', (0, 1)),
                        AstNode('CHAR', 'a', (0, 2)),
                        AstNode('CHAR', '-', (0, 3))
                    )
            ])

        self.run_parser('[]a]', 'range', [
                AstNode('range', '[]a]', (0, 0),
                        AstNode('CHARBRACE', ']', (0, 1)),
                        AstNode('CHAR', 'a', (0, 2))
                    )
            ])

        self.run_parser('[]--]', 'range', [
                AstNode('range', '[]--]', (0, 0),
                        AstNode('CHARBRACE', ']', (0, 1)),
                        AstNode('CHARDASH', '-', (0, 2)),
                        AstNode('CHAR', '-', (0, 3))
                    )
            ])

        self.run_parser('[\\v-\\t]', 'range', [
                AstNode('range', '[\\v-\\t]', (0, 0),
                        AstNode('CHARRANGE', '\\v-\\t', (0, 1),
                                AstNode('ESCAPED_CHAR', '\\v', (0, 1),
                                    AstNode('SPECIAL_ESCAPED_CHAR', 'v', (0, 2))),
                                AstNode('ESCAPED_CHAR', '\\t', (0, 4),
                                    AstNode('SPECIAL_ESCAPED_CHAR', 't', (0, 5)))
                            )
                    )
            ])

        self.run_parser_fail('[foo', 'range', '(1, 5): Expected closing "]"')


    def test_literal(self):
        self.run_parser('c"foo"', 'literal', pos=(0, 6), ast=[
                AstNode('literal', 'c"foo"', (0, 0),
                        AstNode('literalDecorator', 'c', (0, 0)),
                        AstNode('CHAR_NO_DBLQUOTE', 'foo', (0, 2))
                    )
            ])

        self.run_parser("c'foo'", 'literal', pos=(0, 6), ast=[
                AstNode('literal', "c'foo'", (0, 0),
                        AstNode('literalDecorator', 'c', (0, 0)),
                        AstNode('CHAR_NO_SNGLQUOTE', 'foo', (0, 2))
                    )
            ])

        self.run_parser('"foo"', 'literal', pos=(0, 5), ast=[
                AstNode('literal', '"foo"', (0, 0),
                        AstNode('CHAR_NO_DBLQUOTE', 'foo', (0, 1))
                    )
            ])

        self.run_parser("'foo'", 'literal', pos=(0, 5), ast=[
                AstNode('literal', "'foo'", (0, 0),
                        AstNode('CHAR_NO_SNGLQUOTE', 'foo', (0, 1))
                    )
            ])

        self.run_parser('"foo\\nbar\\n"', 'literal', [
                AstNode('literal', '"foo\\nbar\\n"', (0, 0),
                        AstNode('CHAR_NO_DBLQUOTE', 'foo', (0, 1)),
                        AstNode('ESCAPED_CHAR', '\\n', (0, 4),
                            AstNode('SPECIAL_ESCAPED_CHAR', 'n', (0, 5))),
                        AstNode('CHAR_NO_DBLQUOTE', 'bar', (0, 6)),
                        AstNode('ESCAPED_CHAR', '\\n', (0, 9),
                            AstNode('SPECIAL_ESCAPED_CHAR', 'n', (0, 10)))
                    )
            ])

        self.run_parser_fail('"foobar', 'literal',
                '(1, 2): Expected closing double-quote')

        self.run_parser_fail("'foobar", 'literal',
                '(1, 2): Expected closing single-quote')


    def test_eol(self):
        self.run_parser('', 'eol', peek='', pos=(0, 0))
        self.run_parser('\n', 'eol', peek='', pos=(1, 0))


    def test_comment(self):
        self.run_parser('#helloworld', 'comment', peek='', pos=(0, 11), ast=[
                AstNode('comment_text', 'helloworld', (0, 1))
            ])

        self.run_parser('#helloworld\nfoo', 'comment', peek='f', pos=(1, 0), ast=[
                AstNode('comment_text', 'helloworld', (0, 1))
            ])

    def test_ts(self):
        self.run_parser('foo', 'ts', peek='f', pos=(0, 0))
        self.run_parser('    ', 'ts', peek='', pos=(0, 4))
        self.run_parser(' \v\t\r\n', 'ts', peek='', pos=(1, 0))
        self.run_parser(' #helloworld', 'ts', peek='', pos=(0, 12))
        self.run_parser(' #helloworld\nfoo', 'ts', peek='f', pos=(1, 0))

    def test_names(self):
        self.run_parser('foobar', 'name', [AstNode('name', 'foobar', (0, 0))])
        self.run_parser('FOOBAR', 'name', [AstNode('name', 'FOOBAR', (0, 0))])
        self.run_parser('_fooBAR1234', 'name', [AstNode('name', '_fooBAR1234', (0, 0))])

        self.run_parser('>foobar<', 'expandedname', [
                AstNode('expandedname', '>foobar<', (0, 0),
                    AstNode('name', 'foobar', (0, 1)))
            ])

        self.run_parser('<foobar>', 'unreportedname', [
                AstNode('unreportedname', '<foobar>', (0, 0),
                    AstNode('name', 'foobar', (0, 1)))
            ])

    def test_groups(self):
        self.run_parser('/', 'fo_indicator', peek='', pos=(0, 1))
        self.run_parser(',', 'seq_indicator', peek='', pos=(0, 1))

        # TODO: modify fo_group to discard 'ts' like seq_group
        self.run_parser(' hello /foobar / world', 'fo_group', [
                AstNode('fo_group', ' hello /foobar / world', (0, 0),
                        AstNode('element_token', 'hello ', (0, 1),
                            AstNode('name', 'hello', (0, 1))),
                        AstNode('element_token', 'foobar ', (0, 8),
                            AstNode('name', 'foobar', (0, 8))),
                        AstNode('element_token', 'world', (0, 17),
                            AstNode('name', 'world', (0, 17))),
                    )
            ])

        self.run_parser(' hello ,foobar , world', 'seq_group', [
                AstNode('seq_group', ' hello ,foobar , world', (0, 0),
                        AstNode('element_token', 'hello ', (0, 1),
                            AstNode('name', 'hello', (0, 1))),
                        AstNode('element_token', 'foobar ', (0, 8),
                            AstNode('name', 'foobar', (0, 8))),
                        AstNode('element_token', 'world', (0, 17),
                            AstNode('name', 'world', (0, 17))),
                    )
            ])

        self.run_parser('! "fail",  hello, foobar', 'seq_group', [
                AstNode('seq_group', '! "fail",  hello, foobar', (0, 0),
                        AstNode('error_on_fail', '! "fail"', (0, 0),
                                AstNode('literal', '"fail"', (0, 2),
                                    AstNode('CHAR_NO_DBLQUOTE', 'fail', (0, 3)))
                            ),
                        AstNode('element_token', 'hello', (0, 11),
                            AstNode('name', 'hello', (0, 11))),
                        AstNode('element_token', 'foobar', (0, 18),
                            AstNode('name', 'foobar', (0, 18))),
                    )
            ])

        self.run_parser(' hello , foobar/world, !"fail"', 'seq_group', [
                AstNode('seq_group', ' hello , foobar/world, !"fail"', (0, 0),
                        AstNode('element_token', 'hello ', (0, 1),
                            AstNode('name', 'hello', (0, 1))),
                        AstNode('fo_group', 'foobar/world', (0, 9),
                                AstNode('element_token', 'foobar', (0, 9),
                                    AstNode('name', 'foobar', (0, 9))),
                                AstNode('element_token', 'world', (0, 16),
                                    AstNode('name', 'world', (0, 16)))
                            ),
                        AstNode('error_on_fail', '!"fail"', (0, 23),
                                AstNode('literal', '"fail"', (0, 24),
                                    AstNode('CHAR_NO_DBLQUOTE', 'fail', (0, 25)))
                            )
                    )
            ])

        self.run_parser('( hello ,foobar , world)   ', 'group', [
                AstNode('seq_group', ' hello ,foobar , world', (0, 1),
                        AstNode('element_token', 'hello ', (0, 2),
                            AstNode('name', 'hello', (0, 2))),
                        AstNode('element_token', 'foobar ', (0, 9),
                            AstNode('name', 'foobar', (0, 9))),
                        AstNode('element_token', 'world', (0, 18),
                            AstNode('name', 'world', (0, 18))),
                    )
            ])

        self.run_parser_fail('12345', 'seq_group',
                '(1, 1): Expected one or more terms in sequence')

        self.run_parser_fail('(foobar', 'group',
                '(1, 8): Expected closing ")"')



    def test_error_on_fail(self):
        self.run_parser('!', 'error_on_fail', [AstNode('error_on_fail', '!', (0, 0))])

        self.run_parser('!"fail"', 'error_on_fail', [
                AstNode('error_on_fail', '!"fail"', (0, 0),
                        AstNode('literal', '"fail"', (0, 1),
                            AstNode('CHAR_NO_DBLQUOTE', 'fail', (0, 2)))
                    )
            ])

        self.run_parser('!   "fail"', 'error_on_fail', [
                AstNode('error_on_fail', '!   "fail"', (0, 0),
                        AstNode('literal', '"fail"', (0, 4),
                            AstNode('CHAR_NO_DBLQUOTE', 'fail', (0, 5)))
                    )
            ])

    def test_indicators(self):
        self.run_parser('-', 'neg_indicator', [
                AstNode('neg_indicator', '-', (0, 0))
            ])
        self.run_parser('?', 'lookahead_indicator', [
                AstNode('lookahead_indicator', '?', (0, 0))
            ])
        self.run_parser('+', 'occurrence_indicator', [
                AstNode('occurrence_indicator', '+', (0, 0))
            ])
        self.run_parser('*', 'occurrence_indicator', [
                AstNode('occurrence_indicator', '*', (0, 0))
            ])
        self.run_parser('?', 'occurrence_indicator', [
                AstNode('occurrence_indicator', '?', (0, 0))
            ])

    def test_element_token(self):
        self.run_parser('foobar', 'element_token',[
                AstNode('element_token', 'foobar', (0, 0),
                    AstNode('name', 'foobar', (0, 0)))
            ])

        self.run_parser('?foobar', 'element_token',[
                AstNode('element_token', '?foobar', (0, 0),
                        AstNode('lookahead_indicator', '?', (0, 0)),
                        AstNode('name', 'foobar', (0, 1))
                    )
            ])

        self.run_parser('-foobar', 'element_token',[
                AstNode('element_token', '-foobar', (0, 0),
                        AstNode('neg_indicator', '-', (0, 0)),
                        AstNode('name', 'foobar', (0, 1))
                    )
            ])

        self.run_parser('foobar+', 'element_token',[
                AstNode('element_token', 'foobar+', (0, 0),
                        AstNode('name', 'foobar', (0, 0)),
                        AstNode('occurrence_indicator', '+', (0, 6))
                    )
            ])

        self.run_parser('foobar*', 'element_token',[
                AstNode('element_token', 'foobar*', (0, 0),
                        AstNode('name', 'foobar', (0, 0)),
                        AstNode('occurrence_indicator', '*', (0, 6))
                    )
            ])

        self.run_parser('foobar?', 'element_token',[
                AstNode('element_token', 'foobar?', (0, 0),
                        AstNode('name', 'foobar', (0, 0)),
                        AstNode('occurrence_indicator', '?', (0, 6))
                    )
            ])

        self.run_parser('? foobar + !"fail"', 'element_token',[
                AstNode('element_token', '? foobar + !"fail"', (0, 0),
                        AstNode('lookahead_indicator', '?', (0, 0)),
                        AstNode('name', 'foobar', (0, 2)),
                        AstNode('occurrence_indicator', '+', (0, 9)),
                        AstNode('error_on_fail', '!"fail"', (0, 11),
                                AstNode('literal', '"fail"', (0, 12),
                                    AstNode('CHAR_NO_DBLQUOTE', 'fail', (0, 13)))
                            )
                    )
            ])

    def test_declaration(self):
        self.run_parser('myrule ::= foobar', 'declaration', [
                AstNode('declaration', 'myrule ::= foobar', (0, 0),
                        AstNode('name', 'myrule', (0, 0)),
                        AstNode('seq_group', ' foobar', (0, 10),
                                AstNode('element_token', 'foobar', (0, 11),
                                    AstNode('name', 'foobar', (0, 11)))
                            )
                    )
            ])

        self.run_parser('myrule := foobar', 'declaration', [
                AstNode('declaration', 'myrule := foobar', (0, 0),
                        AstNode('name', 'myrule', (0, 0)),
                        AstNode('seq_group', ' foobar', (0, 9),
                                AstNode('element_token', 'foobar', (0, 10),
                                    AstNode('name', 'foobar', (0, 10)))
                            )
                    )
            ])

        self.run_parser(' <myrule> ::= foobar', 'declaration', [
                AstNode('declaration', ' <myrule> ::= foobar', (0, 0),
                        AstNode('unreportedname', '<myrule>', (0, 1),
                            AstNode('name', 'myrule', (0, 2))),
                        AstNode('seq_group', ' foobar', (0, 13),
                                AstNode('element_token', 'foobar', (0, 14),
                                    AstNode('name', 'foobar', (0, 14)))
                            )
                    )
            ])

        self.run_parser(' >myrule< ::= foobar    ', 'declaration', [
                AstNode('declaration', ' >myrule< ::= foobar    ', (0, 0),
                        AstNode('expandedname', '>myrule<', (0, 1),
                            AstNode('name', 'myrule', (0, 2))),
                        AstNode('seq_group', ' foobar    ', (0, 13),
                                AstNode('element_token', 'foobar    ', (0, 14),
                                    AstNode('name', 'foobar', (0, 14)))
                            )
                    )
            ])

        self.run_parser_fail('<foobar := foo', 'declaration',
                '(1, 8): Expected closing ">"')

        self.run_parser_fail('>foobar := foo', 'declaration',
                '(1, 8): Expected closing "<"')

        self.run_parser_fail('!foobar := foo', 'declaration',
                '(1, 1): Expected name, <unreported>, or >expanded< declaration')

        self.run_parser_fail('foobar << foo', 'declaration',
                '(1, 8): Expected := or ::= operator')



    def test_declaration_set(self):
        text = 'myrule := foobar\notherrule := baz #comments'
        self.run_parser(text, 'declaration_set', [
                AstNode('declaration_set', text, (0, 0),
                        AstNode('declaration', 'myrule := foobar\n', (0, 0),
                                AstNode('name', 'myrule', (0, 0)),
                                AstNode('seq_group', ' foobar\n', (0, 9),
                                        AstNode('element_token', 'foobar\n', (0, 10),
                                            AstNode('name', 'foobar', (0, 10)))
                                    )
                            ),
                        AstNode('declaration', 'otherrule := baz #comments', (1, 0),
                                AstNode('name', 'otherrule', (1, 0)),
                                AstNode('seq_group', ' baz #comments', (1, 12),
                                        AstNode('element_token', 'baz #comments', (1, 13),
                                            AstNode('name', 'baz', (1, 13)))
                                    )
                            )
                    )
            ])

BNF_GRAMMAR_DUMP = """Decl("declarationset", OneOrMore(DeclRef("declaration")))
Decl("declaration", Sequence(DeclRef("ts"),OrGroup(DeclRef("unreportedname"),DeclRef("expandedname"),DeclRef("name")),DeclRef("ts"),Literal(":"),Optional(Literal(":")),Literal("="),DeclRef("seq_group")))
Decl("element_token", Sequence(Optional(DeclRef("lookahead_indicator")),DeclRef("ts"),Optional(DeclRef("negpos_indicator")),DeclRef("ts"),OrGroup(DeclRef("literal"),DeclRef("range"),DeclRef("group"),DeclRef("name")),DeclRef("ts"),Optional(DeclRef("occurence_indicator")),DeclRef("ts"),Optional(DeclRef("error_on_fail"))))
Decl("negpos_indicator", OneOf("-+"))
Decl("lookahead_indicator", Literal("?"))
Decl("occurence_indicator", OneOf("+*?"))
Decl("error_on_fail", Sequence(Literal("!"),Optional(Sequence(DeclRef("ts"),DeclRef("literal")))))
ExpandedDecl("group", Sequence(Literal("("),DeclRef("seq_group"),Literal(")")))
Decl("seq_group", Sequence(DeclRef("ts"),OrGroup(DeclRef("error_on_fail"),DeclRef("fo_group"),DeclRef("element_token")),ZeroOrMore(Sequence(DeclRef("ts"),DeclRef("seq_indicator"),DeclRef("ts"),OrGroup(DeclRef("error_on_fail"),DeclRef("fo_group"),DeclRef("element_token")))),DeclRef("ts")))
Decl("fo_group", Sequence(DeclRef("element_token"),OneOrMore(Sequence(DeclRef("ts"),DeclRef("fo_indicator"),DeclRef("ts"),DeclRef("element_token")))))
UnreportedDecl("fo_indicator", Literal("/"))
UnreportedDecl("seq_indicator", Literal(","))
Decl("unreportedname", Sequence(Literal("<"),DeclRef("name"),Literal(">")))
Decl("expandedname", Sequence(Literal(">"),DeclRef("name"),Literal("<")))
Decl("name", Sequence(OrGroup(CharRange("a","z"),CharRange("A","Z"),Literal("_")),ZeroOrMore(OrGroup(CharRange("a","z"),CharRange("A","Z"),CharRange("0","9"),Literal("_")))))
UnreportedDecl("ts", ZeroOrMore(OrGroup(OneOrMore(OrGroup(CharRange("\\011","\\015"),Literal(" "))),DeclRef("comment"))))
Decl("comment", Sequence(Literal("#"),ZeroOrMoreUntil(Literal("
")),Literal("
")))
Decl("literal", Sequence(Optional(DeclRef("literalDecorator")),OrGroup(Sequence(Literal("'"),ZeroOrMore(OrGroup(DeclRef("CHARNOSNGLQUOTE"),DeclRef("ESCAPEDCHAR"))),Literal("'")),Sequence(Literal("\""),ZeroOrMore(OrGroup(DeclRef("CHARNODBLQUOTE"),DeclRef("ESCAPEDCHAR"))),Literal("\"")))))
Decl("literalDecorator", Literal("c"))
Decl("range", Sequence(Literal("["),Optional(DeclRef("CHARBRACE")),Optional(DeclRef("CHARDASH")),ZeroOrMore(OrGroup(DeclRef("CHARRANGE"),DeclRef("CHARNOBRACE"))),Optional(DeclRef("CHARDASH")),Literal("]")))
Decl("CHARBRACE", Literal("]"))
Decl("CHARDASH", Literal("-"))
Decl("CHARRANGE", Sequence(DeclRef("CHARNOBRACE"),Literal("-"),DeclRef("CHARNOBRACE")))
Decl("CHARNOBRACE", OrGroup(DeclRef("ESCAPEDCHAR"),DeclRef("CHAR")))
Decl("CHAR", Negate(Literal("]")))
Decl("ESCAPEDCHAR", Sequence(Literal("\\"),OrGroup(DeclRef("SPECIALESCAPEDCHAR"),Sequence(Literal("x"),DeclRef("HEXESCAPEDCHAR")),Sequence(Literal("u"),DeclRef("UNICODEESCAPEDCHAR_16")),Sequence(Literal("U"),DeclRef("UNICODEESCAPEDCHAR_32")),DeclRef("OCTALESCAPEDCHAR"))))
Decl("SPECIALESCAPEDCHAR", OneOf("\\\\abfnrtv"'"))
Decl("OCTALESCAPEDCHAR", Sequence(CharRange("0","7"),Optional(CharRange("0","7")),Optional(CharRange("0","7"))))
Decl("HEXESCAPEDCHAR", Sequence(OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F"))))
Decl("CHARNODBLQUOTE", OneOrMoreUntil(OneOf("\\\\"")))
Decl("CHARNOSNGLQUOTE", OneOrMoreUntil(OneOf("\\\\'")))
Decl("UNICODEESCAPEDCHAR_16", Sequence(OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F"))))
Decl("UNICODEESCAPEDCHAR_32", Sequence(OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F")),OrGroup(CharRange("0","9"),CharRange("a","f"),CharRange("A","F"))))"""

class TestBnfParserGenerator(ParserTestBase, unittest.TestCase):
    def run_parser_fn(self, text, decl, fn, test):
        parser = BnfParserGenerator()
        parse_result = parser._get_ast(decl, text)
        if len(parse_result.items) != 1:
            raise AssertionError('Length of parse_result is not 1: {}'.format(parse_result))
        ast = parse_result.items[0]
        result = fn(parser, ast)
        if unicode(result) != unicode(test):
            print('AST:', ast)
        self.assertEquals(unicode(result), unicode(test))

    def test_bnf_self_parse(self):
        with open('testfiles/parser.bnf') as f:
            file_str = f.read()
        parser = BnfParserGenerator()
        ast = parser._get_ast('declaration_set', file_str)
        test_str = '\n'.join(map(lambda x: x.text, ast.items))

        if test_str != file_str:
            print('\nTEST:\n', test_str)
            print('\nFILE:\n', file_str)
            print('\nLAST:\n', ast.items[-1].children[-1].to_json())
            raise AssertionError('Parser AST does not match file')

    def test_bnf_parse(self):
        with open('testfiles/parser.bnf') as f:
            file_str = f.read()
        parser = BnfParserGenerator()
        bnf_parser = parser.process(file_str)
        grammar_dump_lines = BNF_GRAMMAR_DUMP.split('\n')
        bnf_parser_lines = unicode(bnf_parser).split('\n')
        for ii, grammar_line in enumerate(grammar_dump_lines):
            bnf_line = bnf_parser_lines[ii]
            if grammar_line != bnf_line:
                print('Line {} doesn\'t match'.format(ii+1))
            self.assertEquals(grammar_line, bnf_line)

    def test_get_literal_value(self):
        fn_lit = BnfParserGenerator._get_literal_value
        self.run_parser_fn('"hello world"', 'literal', fn_lit, 'hello world')
        self.run_parser_fn("'hello world'", 'literal', fn_lit, 'hello world')
        self.run_parser_fn('c"hello world"', 'literal', fn_lit, 'hello world')
        self.run_parser_fn("c'hello world'", 'literal', fn_lit, 'hello world')
        self.run_parser_fn('"[-]"', 'literal', fn_lit, '[-]')
        self.run_parser_fn('"\'"', 'literal', fn_lit, "'")
        self.run_parser_fn("'\"'", 'literal', fn_lit, '"')
        self.run_parser_fn("'\\''", 'literal', fn_lit, "'")
        self.run_parser_fn('"\\""', 'literal', fn_lit, '"')
        self.run_parser_fn('"\\a\\b\\n\\r\\t\\v"', 'literal', fn_lit, '\a\b\n\r\t\v')
        self.run_parser_fn('"\\xAB"', 'literal', fn_lit, '\xAB')
        self.run_parser_fn('"\\uABCD"', 'literal', fn_lit, '\uABCD')
        self.run_parser_fn('"\\U0000ABCD"', 'literal', fn_lit, '\U0000ABCD')

        fn_no_escape = lambda self, x: self._get_literal_value(x, False)
        self.run_parser_fn("c'foo\\r\\nbar'", 'literal', fn_no_escape, 'foo\\r\\nbar')
        self.run_parser_fn("c'foo\\r\\nbar'", 'literal', fn_no_escape, 'foo\\r\\nbar')
        self.run_parser_fn('"\\xAB"', 'literal', fn_no_escape, '\\xAB')
        self.run_parser_fn('"\\uABCD"', 'literal', fn_no_escape, '\\uABCD')
        self.run_parser_fn('"\\U0000ABCD"', 'literal', fn_no_escape, '\\U0000ABCD')

    def test_process_literal(self):
        fn = BnfParserGenerator._process_literal
        self.run_parser_fn('"foobar"', 'literal', fn, 'Literal("foobar")')

    def test_process_element_token(self):
        fn = BnfParserGenerator._process_element_token
        self.run_parser_fn('"foobar"', 'element_token', fn, 'Literal("foobar")')
        self.run_parser_fn('-foobar', 'element_token', fn, 'Negate(DeclRef("foobar"))')
        self.run_parser_fn('?foobar', 'element_token', fn, 'Lookahead(DeclRef("foobar"))')
        self.run_parser_fn('?-foobar', 'element_token', fn, 'Lookahead(Negate(DeclRef("foobar")))')
        self.run_parser_fn('foobar?', 'element_token', fn, 'Optional(DeclRef("foobar"))')
        self.run_parser_fn('foobar*', 'element_token', fn, 'ZeroOrMore(DeclRef("foobar"))')
        self.run_parser_fn('foobar+', 'element_token', fn, 'OneOrMore(DeclRef("foobar"))')

        self.run_parser_fn('?foobar?', 'element_token', fn,
                'Lookahead(Optional(DeclRef("foobar")))')
        self.run_parser_fn('?foobar*', 'element_token', fn,
                'Lookahead(ZeroOrMore(DeclRef("foobar")))')
        self.run_parser_fn('?foobar+', 'element_token', fn,
                'Lookahead(OneOrMore(DeclRef("foobar")))')

        self.run_parser_fn('?-foobar?', 'element_token', fn,
                'Lookahead(Optional(Negate(DeclRef("foobar"))))')
        self.run_parser_fn('?-foobar*', 'element_token', fn,
                'Lookahead(ZeroOrMoreUntil(DeclRef("foobar")))')
        self.run_parser_fn('?-foobar+', 'element_token', fn,
                'Lookahead(OneOrMoreUntil(DeclRef("foobar")))')

        self.run_parser_fn('-foobar?', 'element_token', fn,
                'Optional(Negate(DeclRef("foobar")))')
        self.run_parser_fn('-foobar*', 'element_token', fn,
                'ZeroOrMoreUntil(DeclRef("foobar"))')
        self.run_parser_fn('-foobar+', 'element_token', fn,
                'OneOrMoreUntil(DeclRef("foobar"))')

    def test_process_range(self):
        fn = BnfParserGenerator._process_range
        self.run_parser_fn('[a]', 'range', fn, 'Literal("a")')
        self.run_parser_fn('[-]', 'range', fn, 'Literal("-")')
        self.run_parser_fn('[]]', 'range', fn, 'Literal("]")')

        self.run_parser_fn('[abc]', 'range', fn, 'OneOf("abc")')
        self.run_parser_fn('[a-z]', 'range', fn, 'CharRange("a","z")')
        self.run_parser_fn('[]-]', 'range', fn, 'OneOf("]-")')

        self.run_parser_fn('[a-zA-Z]', 'range', fn,
                'OrGroup(CharRange("a","z"),CharRange("A","Z"))')
        self.run_parser_fn('[-a-zA-Z_]', 'range', fn,
                'OrGroup(CharRange("a","z"),CharRange("A","Z"),OneOf("-_"))')
        self.run_parser_fn('[-a-z.$A-Z_]', 'range', fn,
                'OrGroup(CharRange("a","z"),CharRange("A","Z"),OneOf("-.$_"))')

    def test_process_seq_group(self):
        fn = BnfParserGenerator._process_seq_group
        self.run_parser_fn('foobar', 'seq_group', fn,
                'DeclRef("foobar")')
        self.run_parser_fn('foo, bar, baz', 'seq_group', fn,
                'Sequence(DeclRef("foo"),DeclRef("bar"),DeclRef("baz"))')
        self.run_parser_fn('! "fail", foo, bar', 'seq_group', fn,
                'Sequence(DeclRef("foo").on_fail("fail"),DeclRef("bar").on_fail("fail"))')
        self.run_parser_fn('! "fail", foo, !"baz", bar', 'seq_group', fn,
                'Sequence(DeclRef("foo").on_fail("fail"),DeclRef("bar").on_fail("baz"))')

    def test_process_fo_group(self):
        fn = BnfParserGenerator._process_fo_group
        self.run_parser_fn('foo/ bar/ baz', 'fo_group', fn,
                'OrGroup(DeclRef("foo"),DeclRef("bar"),DeclRef("baz"))')

    def test_declaration(self):
        fn = BnfParserGenerator._process_declaration
        self.run_parser_fn('foo := bar', 'declaration', fn,
                'Decl("foo", DeclRef("bar"))')
        self.run_parser_fn('<foo> := bar', 'declaration', fn,
                'UnreportedDecl("foo", DeclRef("bar"))')
        self.run_parser_fn('>foo< := bar', 'declaration', fn,
                'ExpandedDecl("foo", DeclRef("bar"))')

# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
import ansible_hint.parser as ahp

class ParserTestBase(object):
    def assertPeek(self, ctx, literal, pos):
        ll = len(literal)
        value = ctx.peek(ll)
        current_pos = ctx.position()

        if value != literal:
            raise AssertionError('{}: expected next literal to be "{}", not "{}"'.format(
                    current_pos, literal, value))
        if current_pos != pos:
            raise AssertionError('{}: expected position to be "{}"'.format(
                    current_pos, pos))

    def assertAst(self, result, ast_list):
        result_str = unicode(result)
        test_str = unicode(ahp.AstResult(ast_list))
        if result_str != test_str:
            print('\nCTX:', result_str)
            print('\nTST:', test_str)
            raise AssertionError('Expected AST sets to be equal (see output above for CTX and TST)')

    def assertParser(self, decls, text, decl, ast=[], passfail=True, peek='', pos=None):
        ctx = ahp.ParseCtx(decls)
        ctx.text = text
        result = ctx.get_decl(decl).evaluate(ctx)
        if passfail:
            self.assertTrue(result, 'Production "{}" did not pass'.format(decl))
        else:
            self.assertFalse(result, 'Production "{}" did not fail'.format(decl))
        if pos is not None:
            if peek == '':
                self.assertTrue(ctx.eof())
            self.assertPeek(ctx, peek, pos)
        self.assertAst(result, ast)

    def assertParserFail(self, decls, text, decl, exception_text):
        ctx = ahp.ParseCtx(decls)
        ctx.text = text
        decl = ctx.get_decl(decl)
        with self.assertRaises(ahp.ParseError) as cm:
            decl.evaluate(ctx)
        self.assertEquals(unicode(cm.exception), exception_text)


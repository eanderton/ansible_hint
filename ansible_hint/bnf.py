# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
from ansible_hint.parser import *

# some shorthand to make things more readable
DR = DeclRef
TS = DR('ts')
L = Literal

bnf_parser_decls = [
    # declaration_set      :=  declaration+
    Decl('declaration_set', OneOrMore(DR('declaration'))),

    # declaration         :=  ts, (unreportedname/expandedname/name) ,ts,':',':'?,'=',seq_group
    Decl('declaration',
        TS,
        OrGroup(
            DR('unreportedname'), DR('expandedname'), DR('name')
        ).on_fail('Expected name, <unreported>, or >expanded< declaration'),
        TS,
        OrGroup(L(':='), L('::=')).on_fail('Expected := or ::= operator'),
        DR('seq_group')
    ),

    # element_token       :=  lookahead_indicator?, ts, negpos_indicator?,ts, (literal/range/group/name),ts, occurence_indicator?, ts, error_on_fail?
    Decl('element_token',
        Optional(DR('lookahead_indicator')), TS,
        Optional(DR('neg_indicator')), TS,
        OrGroup(
            DR('literal'), DR('range'), DR('group'), DR('name')
        ),
        TS,
        Optional(DR('occurrence_indicator')), TS,
        Optional(DR('error_on_fail'))
    ),

    # negpos_indicator    :=  [-+]
    Decl('neg_indicator', L('-')),

    # lookahead_indicator :=  "?"
    Decl('lookahead_indicator', L('?')),

    # occurence_indicator :=  [+*?]
    Decl('occurrence_indicator', OneOf('+*?')),

    # error_on_fail       :=  "!", (ts,literal)?
    Decl('error_on_fail', L('!'), Optional(Sequence(TS, DR('literal')))),

    # >group<             :=  '(',seq_group, ')'
    ExpandedDecl('group',
        L('('),
        DR('seq_group'),
        L(')').on_fail('Expected closing ")"')
    ),

    # seq_group           :=  ts,(error_on_fail/fo_group/element_token),
    #                           (ts, seq_indicator, ts,
    #                               (error_on_fail/fo_group/element_token)
    #                           )*, ts
    #
    Decl('seq_group', TS,
        OrGroup(
            DR('error_on_fail'), DR('fo_group'), DR('element_token')
        ).on_fail('Expected one or more terms in sequence'),
        ZeroOrMore(Sequence(
            TS, DR('seq_indicator'), TS,
            OrGroup(
                DR('error_on_fail'), DR('fo_group'), DR('element_token')
            )
        )), TS
    ),

    # fo_group            :=  element_token, (ts, fo_indicator, ts, element_token)+
    Decl('fo_group', TS,
        DR('element_token'),
        OneOrMore(Sequence(
            TS, DR('fo_indicator'), TS, DR('element_token')
        ))
    ),

    # # following two are likely something peoples might want to
    # # replace in many instances...

    # <fo_indicator>      :=  "/"
    UnreportedDecl('fo_indicator', L('/')),

    # <seq_indicator>     :=  ','
    UnreportedDecl('seq_indicator', L(',')),

    # unreportedname      :=  '<', name, '>'
    Decl('unreportedname', L('<'), DR('name'), L('>').on_fail('Expected closing ">"')),

    # expandedname        :=  '>', name, '<'
    Decl('expandedname', L('>'), DR('name'), L('<').on_fail('Expected closing "<"')),

    # name                :=  [a-zA-Z_],[a-zA-Z0-9_]*
    Decl('name', OrGroup(CharRange('a', 'z'), CharRange('A', 'Z'), L('_')),
        ZeroOrMore(OrGroup(
            CharRange('a', 'z'), CharRange('A', 'Z'), CharRange('0', '9'), L('_')
        ))
    ),

    # <ts>                :=  ( [ \011-\015]+ / comment )*
    UnreportedDecl('ts', ZeroOrMore(OrGroup(
        OneOrMore(OrGroup(L(' '), CharRange('\011', '\015'))), DR('comment')
    ))),

    # comment             :=  '#',-'\n'*,'\n'
    ExpandedDecl('comment', DR('comment_start'), DR('comment_text'), DR('eol')),
    Decl('comment_text', ZeroOrMoreUntil(DR('eol'))),
    UnreportedDecl('comment_start', L('#')),
    UnreportedDecl('eol', OrGroup(L('\n'), Eof())),

    # literal             :=  literalDecorator?,("'",(CHAR_NO_SNGLQUOTE/ESCAPED_CHAR)*,"'")  /  ('"',(CHAR_NO_DBLQUOTE/ESCAPED_CHAR)*,'"')

    # TODO: do a raw parse baed on literalDecorator to ease Parser pass
    Decl('literal', Optional(DR('literalDecorator')),
        OrGroup(
            Sequence(L("'"), ZeroOrMore(OrGroup(
                    DR('CHAR_NO_SNGLQUOTE'), DR('ESCAPED_CHAR')
                )), L("'").on_fail('Expected closing single-quote')),
            Sequence(L('"'), ZeroOrMore(OrGroup(
                    DR('CHAR_NO_DBLQUOTE'), DR('ESCAPED_CHAR')
                )), L('"').on_fail('Expected closing double-quote')),
        )
    ),

    # literalDecorator    :=  [c]
    Decl('literalDecorator', L('c')),

    # range               :=  '[',CHARBRACE?,CHARDASH?, (CHARRANGE/CHARNOBRACE)*, CHARDASH?,']'
    Decl('range', L('['),
        Optional(DR('CHARBRACE')), Optional(DR('CHARDASH')),
        ZeroOrMore(OrGroup(DR('CHARRANGE'), DR('CHARNOBRACE'))),
        Optional(DR('CHARDASH')),
        L(']').on_fail('Expected closing "]"')
    ),

    # CHARBRACE           :=  ']'
    Decl('CHARBRACE', L(']')),

    # CHARDASH            :=  '-'
    Decl('CHARDASH', L('-')),

    # CHARRANGE           :=  CHARNOBRACE, '-', CHARNOBRACE
    Decl('CHARRANGE', DR('CHARNOBRACE'), L('-'), DR('CHARNOBRACE')),

    # >CHARNOBRACE<         :=  ESCAPED_CHAR/CHAR
    ExpandedDecl('CHARNOBRACE', OrGroup(DR('ESCAPED_CHAR'), DR('CHAR'))),

    # CHAR                :=  -[]]
    Decl('CHAR', Negate(L(']'))),

    # ESCAPED_CHAR         :=  '\\',( SPECIAL_ESCAPED_CHAR / ('x',HEX_ESCAPED_CHAR) / ("u",UNICODE_ESCAPED_CHAR_16) /("U",UNICODE_ESCAPED_CHAR_32)/OCTAL_ESCAPED_CHAR  )
    Decl('ESCAPED_CHAR', L('\\'), OrGroup(
            DR('SPECIAL_ESCAPED_CHAR'),
            Sequence(
                    L('x'), DR('HEX_ESCAPED_CHAR').on_fail(
                            'Expected two hex digits following "\\x"')
                ),
            Sequence(
                    L('u'), DR('UNICODE_ESCAPED_CHAR_16').on_fail(
                            'Expected four hex digits following "\\u"')
                ),
            Sequence(
                    L('U'), DR('UNICODE_ESCAPED_CHAR_32').on_fail(
                            'Expected eight hex digits following "\\U"')
                ),
            DR('OCTAL_ESCAPED_CHAR'),
            Fail('Expected escape sequence following "\\"')
        ),
    ),

    # SPECIAL_ESCAPED_CHAR  :=  [\\abfnrtv"']
    Decl('SPECIAL_ESCAPED_CHAR', OneOf('\\abfnrtv"\'')),

    # OCTAL_ESCAPED_CHAR    :=  [0-7],[0-7]?,[0-7]?
    Decl('OCTAL_ESCAPED_CHAR',
        CharRange('0', '7'), Optional(CharRange('0', '7')), Optional(CharRange('0', '7'))
    ),

    # HEX_ESCAPED_CHAR      :=  [0-9a-fA-F],[0-9a-fA-F]
    Decl('HEX_ESCAPED_CHAR', DR('HEXDIGIT'), DR('HEXDIGIT')),
    UnreportedDecl('HEXDIGIT', OrGroup(
            CharRange('0', '9'), CharRange('a', 'f'), CharRange('A', 'F'),
        )
    ),

    # CHAR_NO_DBLQUOTE      :=  -[\\"]+
    Decl('CHAR_NO_DBLQUOTE', OneOrMoreUntil(OneOf('\\"'))),

    # CHAR_NO_SNGLQUOTE     :=  -[\\']+
    Decl('CHAR_NO_SNGLQUOTE', OneOrMoreUntil(OneOf("\\'"))),

    # UNICODE_ESCAPED_CHAR_16 := [0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F]
    Decl('UNICODE_ESCAPED_CHAR_16',
        DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT')
    ),

    # UNICODE_ESCAPED_CHAR_32 := [0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F],[0-9a-fA-F]
    Decl('UNICODE_ESCAPED_CHAR_32',
        DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT'),
        DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT'), DR('HEXDIGIT')
    )
]

class SemanticError(Exception):
    pass


class ParserBase(object):
    def _error(self, node, msg):
        raise SemanticError('({}, {}): {}'.format(
                node.pos[0], node.pos[1], msg
            ))

    def _warn(self, node, msg):
        self.warnings.append('({}, {}): {}'.format(
                node.pos[0], node.pos[1], msg
            ))

    def _get_child_token(self, ast, node_name):
        for item in ast.children:
            if item.name == node_name:
                return item
        return None

    def _get_token(self, ast, node_name):
        if ast.name == node_name:
            return ast
        for item in ast.children:
            result = self._get_token(item, node_name)
            if result is not None:
                return result
        return None


class BnfParserGenerator(ParserBase):
    def __init__(self):
        # TODO: set BNF options here (warnings as errors, alternate syntax, etc)
        # TODO: allow factory-creation of ParseCtx
        # TODO: allow factory-creation of BasicParser

        self.default_fail_msg = "Syntax Error"
        self.warnings = []
        self._build_lookups()

    def _build_lookups(self):
        self.ESCAPED_LITERAL_CHAR_LOOKUP = {
            '\\': '\\',
            'a': '\a',
            'b': '\b',
            'n': '\n',
            'r': '\r',
            't': '\t',
            'v': '\v',
            '"': '\"',
            '\'': '\'',
        }

        self.ESCAPED_LITERAL_LOOKUP = {
            'CHAR': lambda x: x.text,
            'CHAR_NO_SNGLQUOTE': lambda x: x.text,
            'CHAR_NO_DBLQUOTE': lambda x: x.text,
            'HEX_ESCAPED_CHAR': lambda x: unichr(int('0x'+x.text, 16)),
            'UNICODE_ESCAPED_CHAR_16': lambda x: unichr(int('0x'+x.text, 16)),
            'UNICODE_ESCAPED_CHAR_32': lambda x: unichr(int('0x'+x.text, 16)),
            'OCTAL_ESCAPED_CHAR': lambda x: unichr(int('0x'+x.text, 16)),
            'SPECIAL_ESCAPED_CHAR': lambda x: \
                    self.ESCAPED_LITERAL_CHAR_LOOKUP[x.text],
        }

        self.LITERAL_LOOKUP = {
            'CHAR': lambda x: x.text,
            'CHAR_NO_SNGLQUOTE': lambda x: x.text,
            'CHAR_NO_DBLQUOTE': lambda x: x.text,
            'ESCAPED_CHAR': lambda x: x.text,
        }

        self.element_prod_lookup = {
            'literal': self._process_literal,
            'range': self._process_range,
            'seq_group': self._process_seq_group,
            'fo_group': self._process_fo_group,
            'name': self._process_decl_ref,
        }

        self.element_negate_occurrence_lookup = {
            '?': lambda x: Optional(Negate(x)),
            '+': lambda x: OneOrMoreUntil(x),
            '*': lambda x: ZeroOrMoreUntil(x),
        }

        self.element_occurrence_lookup = {
            '?': Optional,
            '+': OneOrMore,
            '*': ZeroOrMore,
        }

        self.group_prod_lookup = {
            'seq_group': self._process_seq_group,
            'fo_group': self._process_fo_group,
            'element_token': self._process_element_token,
        }

        self.decl_name_lookup = {
            'name': lambda x: (Decl, x.text),
            'unreportedname': lambda x: (UnreportedDecl, x.children[0].text),
            'expandedname': lambda x: (ExpandedDecl, x.children[0].text),
        }

    def _get_literal_value(self, ast, convert_escapes=True):
        """ Walk AST, gathering text in order """
        parts = []
        if convert_escapes:
            translate_table = self.ESCAPED_LITERAL_LOOKUP
        else:
            translate_table = self.LITERAL_LOOKUP
        next_fn = lambda x: self._get_literal_value(x, convert_escapes)
        for node in ast.children:
            parts.append(translate_table.get(node.name, next_fn)(node))
        return ''.join(parts)

    def _get_error_on_fail_value(self, ast):
        msg = ''
        for node in ast.children:
            msg += self._get_literal_value(node)
        if msg == '':
            msg = self.default_fail_msg
        return msg

    def _process_literal(self, ast):
        convert_escapes =  self._get_child_token(ast, 'literalDecorator') is None
        return Literal(self._get_literal_value(ast, convert_escapes))

    def _process_decl_ref(self, ast):
        name = ast.text.strip()
        return DeclRef(name)

    def _process_char_range(self, ast):
        return

    def _process_range(self, ast):
        productions = []
        explicit_chars = ''

        # iterate children, record explicit chars and build CharRange() instances
        for node in ast.children:
            if node.name == 'CHARRANGE':
                productions.append(CharRange(node.children[0].text, node.children[1].text))
            else:
                explicit_chars += node.text

        # add a Literal() for one char, and OneOf() for multiple
        ll = len(explicit_chars)
        if ll == 1:
            productions.append(Literal(explicit_chars))
        elif ll > 1:
            productions.append(OneOf(explicit_chars))

        # promote expression to OrGroup if more than one char class specified
        if len(productions) == 1:
            return productions[0]
        else:
            return OrGroup(*productions)

    def _process_element_token(self, ast):
        lookahead = False
        negate = False
        occurrence = False
        error_on_fail = None
        prod = None

        # evaluate production and optional flags
        for node in ast.children:
            name = node.name
            # TODO: optimize using dict
            if name == 'lookahead_indicator':
                lookahead = True
            elif name == 'neg_indicator':
                negate = True
            elif name == 'occurrence_indicator':
                occurrence = node.text
            elif name == 'error_on_fail':
                error_on_fail = self._get_child_token(x)
            else:
                prod = self.element_prod_lookup[name](node)

        # process flags and build result
        if negate and occurrence:
            prod = self.element_negate_occurrence_lookup[occurrence](prod)
        elif negate:
            prod = Negate(prod)
        elif occurrence:
            prod = self.element_occurrence_lookup[occurrence](prod)
        if lookahead:
            prod = Lookahead(prod)
        if error_on_fail:
            prod.on_fail(self._get_error_on_fail_value(error_on_fail))

        return prod

    def _process_fo_group(self, ast):
        productions = []
        for node in ast.children:
            if node.name == 'element_token':
                productions.append(self.group_prod_lookup[node.name](node))
        return OrGroup(*productions)

    def _process_seq_group(self, ast):
        productions = []
        error_msg = None

        # NOTE: error message applies to all following productions
        for node in ast.children:
            if node.name == 'error_on_fail':
                error_msg = self._get_error_on_fail_value(node)
            else:
                prod = self.group_prod_lookup[node.name](node)
                prod.on_fail(error_msg)
                productions.append(prod)
        if len(productions) == 1:
            return productions[0]
        else:
            return Sequence(*productions)

    def _process_declaration(self, ast):
        # get the name and type of the decl
        node = ast.children[0]
        ctor, name = self.decl_name_lookup[node.name](node)

        # process the production(s) that make up the decl
        node = self._get_token(ast, 'seq_group')
        prod = self._process_seq_group(node)

        return ctor(name, prod)

    def _process_declaration_set(self, ast):
        decls = []
        for item in ast.children:
            decls.append(self._process_declaration(item))
        return decls

    def _process_ast_result(self, ast_result):
        items = ast_result.items
        if len(items) == 0:
            self._warn('No declarations found')
            return []
        node = items[0]
        if node.name != 'declaration_set':
            self._error(node, 'Expected declaration set')
        return self._process_declaration_set(node)

    def _get_ast(self, decl, bnf_text):
        ctx = ParseCtx(bnf_parser_decls)
        ctx.reset(bnf_text)
        return ctx.get_decl(decl).evaluate(ctx)

    def process(self, bnf_text):
        ast = self._get_ast('declaration_set', bnf_text)
        decl_set = self._process_ast_result(ast)
        return BasicParser(decl_set)


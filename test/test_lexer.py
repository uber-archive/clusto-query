import unittest
import clusto_query.lexer
from clusto_query.exceptions import StringParseError


class LexerTest(unittest.TestCase):
    def test_consume(self):
        self.assertEqual(clusto_query.lexer.consume('nom', 'nomnomnom'),
                         'nomnom')

    def test_lex_string_inner_quoted_basic(self):
        self.assertEqual(clusto_query.lexer.lex_string_inner("'production' and"),
                         ('production', False, ' and'))
        self.assertEqual(clusto_query.lexer.lex_string_inner('"production" and'),
                         ('production', False, ' and'))

    def test_lex_string_inner_quoted_with_spaces(self):
        self.assertEqual(clusto_query.lexer.lex_string_inner("' prod uction ' and"),
                         (' prod uction ', False, ' and'))
        self.assertEqual(clusto_query.lexer.lex_string_inner('" prod uction " and'),
                         (' prod uction ', False, ' and'))

    def test_lex_string_inner_escaped(self):
        self.assertEqual(clusto_query.lexer.lex_string_inner("'foo\\'bar'"),
                         ("foo'bar", False, ''))
        self.assertEqual(clusto_query.lexer.lex_string_inner('"foo\\"bar"'),
                         ('foo"bar', False, ''))

    def test_lex_string_inner_unquoted(self):
        self.assertEqual(clusto_query.lexer.lex_string_inner('1 and'),
                         ('1', True, ' and'))
        self.assertEqual(clusto_query.lexer.lex_string_inner('production and'),
                         ('production', True, ' and'))

    def test_lex_string_inner_invalid(self):
        with self.assertRaises(StringParseError):
            clusto_query.lexer.lex_string_inner("\\")
        with self.assertRaises(StringParseError):
            clusto_query.lexer.lex_string_inner("'unfinished string")

    def test_lex_string_number(self):
        self.assertEqual(clusto_query.lexer.lex_string('1 and'),
                         (1, ' and'))
        self.assertEqual(clusto_query.lexer.lex_string('1.5 and'),
                         (1.5, ' and'))

    def test_lex_string_quoted(self):
        self.assertEqual(clusto_query.lexer.lex_string('"production" and'),
                         ('production', ' and'))
        self.assertEqual(clusto_query.lexer.lex_string('\'production\' and'),
                         ('production', ' and'))

    def test_lex_string_unquoted(self):
        self.assertEqual(clusto_query.lexer.lex_string('production and'),
                         ('production', ' and'))

    def test_lex_string_size(self):
        self.assertEqual(clusto_query.lexer.lex_string('1K and'),
                         (1024, ' and'))
        self.assertEqual(clusto_query.lexer.lex_string('1.5T and'),
                         (1649267441664.0, ' and'))

    def test_lex_string_invalid_size(self):
        self.assertEqual(clusto_query.lexer.lex_string('1.1.1.1K and'),
                         ('1.1.1.1K', ' and'))
        self.assertEqual(clusto_query.lexer.lex_string('1.1.1.1 and'),
                         ('1.1.1.1', ' and'))

    def test_lex(self):
        self.assertEqual(clusto_query.lexer.lex('pool = production and (attr haproxy.enabled = 1)'),
                         ['pool', '=', 'production', 'and', '(', 'attr', 'haproxy.enabled', '=',
                          1, ')'])

import unittest
import clusto_query.lexer


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

    def test_lex_string_inner_unquoted(self):
        self.assertEqual(clusto_query.lexer.lex_string_inner('1 and'),
                         ('1', True, ' and'))

class ExpectedTokenError(StandardError):
    def __init__(self, expected, got):
        self.expected = expected
        self.got = got

    def __str__(self):
        return "Missing expected token (expected '%s', got '%s')" % (self.expected, self.got)


class UnexpectedTokenError(StandardError):
    pass


class StringParseError(StandardError):
    pass

__all__ = ['ExpectedTokenError', 'UnexpectedTokenError', 'StringParseError']

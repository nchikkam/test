import unittest
from commonutils.tools import (
    check_braces
)

def bracer(str, opened, closed, n):
    backup = str
    if opened == n and closed == n :
        yield str

    if opened < n :
        for b in bracer(str+"(", opened+1, closed, n):
            yield b
        str = backup

    if opened > closed:
        for b in bracer(str+ ")", opened, closed+1, n):
            yield b
        str = backup


class BracerGeneratorTest(unittest.TestCase):

    def test_3_order(self):
        l = ["((()))", "(()())", "(())()", "()(())", "()()()"]
        i = 0
        for b in bracer("", 0, 0, 3):
            self.assertEqual(l[i], b)
            i = i + 1

    def test_3_wiout_order(self):
        l = ["((()))", "(()())", "(())()", "()(())", "()()()"]
        for b in bracer("", 0, 0, 3):
            self.assertTrue(b in l)

    def test_3_validity(self):
        for b in bracer("", 0, 0, 8):
            self.assertTrue(check_braces(b))

if __name__ == "__main__":
    unittest.main()

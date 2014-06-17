
def bin_num(x):
    sign = ''
    if x < 0:
        sign = '-'

    x = abs(x)
    bits = []
    while x:
        x, rmost = divmod(x, 2)
        bits.append(rmost)
    return sign + ''.join(str(b) for b in reversed(bits or [0]))


def toStr(n,base):
    convertString = "0123456789ABCDEF"
    if n < base:
        return convertString[n]
    else:
        return toStr(n/base,base) + convertString[n%base]

#print(toStr(1453,16))

import unittest
class TestBinaryNumbers(unittest.TestCase):
    def test_0(self):
        self.assertEqual('0', bin_num(0))

    def test_2(self):
        self.assertEqual('10', bin_num(2))

    def test_748935(self):
        self.assertEqual('10110110110110000111', bin_num(748935))

if __name__ == "__main__":
    unittest.main()

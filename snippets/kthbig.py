def findNthBiggest(sample, n):
    pivot = sample[n]
    below = [s for s in sample if s < pivot]
    above = [s for s in sample if s > pivot]
    i, j = len(below), len(sample)-len(above)
    if n < i:
        return findNthBiggest(below, n)
    elif n >= j:
        return findNthBiggest(above, n-j)
    else:
        return pivot

def findKthBiggest(a, k):
     l = 0
     r = len(a)-1
     pivot = a[k]
     while( l < r):
         pivot = a[k]
         i = l
         j = r
         while( i < j):
             while a[i] < pivot: i = i + 1
             while pivot < a[j]: j = j - 1
             if( i <= j ):
                 a[i], a[j] = a[j], a[i]
                 i = i + 1
                 j = j -1
             if j < k: l = i
             if i > k: r = j
     return pivot

import unittest
class KthBiggestTets(unittest.TestCase):
    def test_0(self):
        self.assertEqual(1, findNthBiggest([6, 7, 8, 9, 1, 2, 3, 4, 4.5], 0))

    def test_1(self):
        self.assertEqual(1, findNthBiggest([1], 0))

    def test_5(self):
        self.assertEqual(5, findNthBiggest([6, 7, 8, 9, 1, 2, 3, 4, 5], 4))

    def test_8(self):
        self.assertEqual(8, findNthBiggest([6, 7, 8], 2))

    #another function
    def test_5_a(self):
        self.assertEqual(5, findKthBiggest([6, 7, 8, 9, 1, 2, 3, 4, 5], 4))

    def test_0_a(self):
        self.assertEqual(1, findKthBiggest([6, 7, 8, 9, 1, 2, 3, 4, 4.5], 0))

    def test_1_a(self):
        self.assertEqual(1, findKthBiggest([1], 0))

    def test_8_a(self):
        self.assertEqual(8, findKthBiggest([6, 7, 8], 2))

if __name__ == "__main__":
    unittest.main()
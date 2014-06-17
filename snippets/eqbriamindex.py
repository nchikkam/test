"""
    Equilibrium index of  an array is an index such that
    the sum of elements at lower indexes is equal to the
    sum of elements at higher indexes
"""
def findEquibriumIndexOfAnArray(l):
   s = sum(l)
   leftsum = 0
   for i in range(len(l)):
      s = s - l[i]
      if leftsum == s:
          return i
      leftsum = leftsum + l[i]
   return -1

import unittest
class EqTest(unittest.TestCase):

    def test_index_3(self):
        l = [-7, 1, 5, 2, -4, 3, 0]
        self.assertEquals(3, findEquibriumIndexOfAnArray(l))

    def test_index_n_3(self):
        l = [1, 1, 1, 4, 1, 1, 1]
        self.assertEquals(3, findEquibriumIndexOfAnArray(l))

    def test_index_n_1(self):
        l = [3, 0, 1, 1, 1]
        self.assertEquals(1, findEquibriumIndexOfAnArray(l))

    def test_index_n_another_3(self):
        l = [1, 1, 1, 0, 3]
        self.assertEquals(3, findEquibriumIndexOfAnArray(l))

    def test_index_n_another_3(self):
        l = [4, 3, 2, 0, 9]
        self.assertEquals(3, findEquibriumIndexOfAnArray(l))

    #if there is only one element, the element itself is equi :)
    def test_index_negative_1(self):
        l = [4]
        self.assertEquals(0, findEquibriumIndexOfAnArray(l))

    #if list has no elements, it must be an error :D
    def test_index_negative_2(self):
        l = []
        self.assertEquals(-1, findEquibriumIndexOfAnArray(l))

if __name__ == "__main__":
    unittest.main()

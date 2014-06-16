import unittest

def searchinMatrixO_N(v, matrix):
   i = 0
   j = len(matrix)-1
   while i < v and j >= 0 :
      if matrix[i][j] == v:
         return (i,j)
      elif matrix[i][j] > v:
        j = j - 1
      else:
        i = i + 1
   return (-1, -1)

def binSearchinList(v, l):
    low = 0
    high = len(l)
    while low < high:
        mid = int((low + high)/2)
        if l[mid] < v:
            high = mid - 1
        elif l[mid] > v:
            low = mid + 1
        else:
            return mid
    return -1

class BinSearchTest(unittest.TestCase):
    def test_index_0(self):
        l = [1]
        expectedIndex = 0
        self.assertEqual(0, binSearchinList(1, l))

    def test_index_1(self):
        l = [1, 2, 3]
        expectedIndex = 1
        self.assertEqual(1, binSearchinList(2, l))

    def test_missing_number(self):
        l = range(100)
        expected = -1
        self.assertEqual(-1, binSearchinList(200, l))

    def test_sortedMatrix_test_33(self):
        n = 0
        l = [[], [], [], [], [], [], [], [], [], []]
        for i in range(10):
            for j in range(10):
                l[i].append(n)
                n = n + 1

        #override the 3rd row
        l[3] = [33, 33, 33, 33, 33, 33, 33, 33, 33 ,33]
        self.assertEquals((-1, -1), searchinMatrixO_N(32, l))

if __name__ == "__main__":
    unittest.main()

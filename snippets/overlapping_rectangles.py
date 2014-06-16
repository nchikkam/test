comment = """

      Y
      ^  A
      |
      |
      |  p(x1,y1)
      |  p(2,5)ul
     5+    +---------+
      |    | q(3,4)ul|
     4+    |   +-+   |        q(x1,y1)
      |    |   | |   |        r(9, 3)ul
     3+    |   +-+   |            +-------------+
      |    | q(4,3)lr|            |             |
     2+    +---------+            |             |
      |            p(5,2)lr       |             |
     1+            p(x2,y2)       +-------------+r(14,1)lr
      |                                          q(x2,y2)
 --+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+-- > X
      |  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
      +
      |
"""

def isOverlap(p, q): # This always assumes (left, top, right, bottom)
    (px1, py1), (px2, py2) = p
    (qx1, qy1), (qx2, qy2) = q

    if px2 < qx1 or px1 > qx2 or qy1 < py2 or qy2 > py1:
        return False
    return True

import unittest
class RectanglesOverlappingTest(unittest.TestCase):

    def test_2_5_5_2_and_3_4_4_3(self):
        p = [(2, 5), (5, 2)]
        q = [(3, 4), (4, 3)]
        self.assertTrue(isOverlap(p, q))
        self.assertTrue(isOverlap(q, p))

    def test_2_5_5_2_and_9_3_14_1(self):
        p = [(2, 5), (5, 2) ]
        r = [(9, 3), (14, 1)]
        self.assertFalse(isOverlap(p, r))
        self.assertFalse(isOverlap(r, p))

    def test_0_10_10_0_and_1_2_2_1(self):
        p = [(0, 10), (10, 0)]
        q = [(1, 2), (2, 1)  ]
        self.assertTrue(isOverlap(p, q))

    def test_check_all_left_top_right_bottom_positive_cases(self):
        p = [(0, 10), (10, 0)]
        for i in range(0, 11):
            q = [(1, i), (i, 1)  ]
            self.assertTrue(isOverlap(p, q))

    """
      Y
      ^  A
      |
      +              p(x1,y1)
      |              p(15,25)ul
    25.                +---------+
     ..                |         |
     ..                |         |
     ..                |         |
     ..                |         |
     ..                +---------+
     ..  +--+--+--+                p(20,2)lr
     ..  +--+--+  |                p(x2,y2)
      |  +--+  |  |
     2+  |  |  |  |
      |  |  |  |  |
     1+  |  |  |  |
      |  +--+--+--+
  -+--+--+--+--+--..........+--+-......-+-- > X
      |  1  2  3  ..........15 .  .  .  20
      +
      |
    """
    def test_check_all_left_top_right_bottom_negative_cases(self):
        p = [(15, 25), (20, 4)]
        for i in range(0, 11):
            q = [(1, i), (i, 1)  ]
            self.assertFalse(isOverlap(p, q))

if __name__ == "__main__":
    unittest.main()

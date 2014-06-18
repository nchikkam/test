class BinaryTree:

    def __init__(self, data=None):
        self.left = None
        self.right = None
        self.data = data

    def insert(self, data):
        if self.data == None:
            self.data = data
        elif self.data < data:
            if self.right == None:
                self.right = BinaryTree(data)
            else:
                self.right.insert(data)
        elif self.data > data:
            if self.left == None:
                self.left = BinaryTree(data)
            else:
                self.left.insert(data)
        else:
            print "Trying to Insert Duplicate key"

    def search(self, data):
        result = False
        if self.data == data:
            return True
        elif self.data < data:
            if self.right is not None:
                result = self.right.search(data)
        else:
            if self.left is not None:
                result = self.left.search(data)
        return result

    def preOrder(self):
        yield self.data
        if self.left:
            for v in self.left.preOrder():
                yield v
        if self.right:
            for v in self.right.preOrder():
                yield v

    def inOrder(self): #lazy mode, iterators :)
        if self.left:
            for v in self.left.inOrder():
                yield v

        yield self.data

        if self.right:
            for v in self.right.inOrder():
                yield v

    def postOrder(self):
        if self.left:
            for v in self.left.postOrder():
                yield v
        if self.right:
            for v in self.right.postOrder():
                yield v
        yield self.data

# Pure TDD
import unittest
class TestBinaryTree(unittest.TestCase):

    def testInit(self):
        expected = 10
        tree = BinaryTree(expected)
        self.assertEqual(tree.left, None)
        self.assertEqual(tree.right, None)
        self.assertEqual(tree.data, expected)

    def testSearchForData(self):
        tree = BinaryTree(100)
        self.assertFalse(tree.search(1))
        self.assertTrue(tree.search(100))


    def testInOrder(self):
        tree = BinaryTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        gen = tree.inOrder()
        l.sort()  # inOrder gives the elements in sorted Order always in BinaryTree
        for i in l:
            self.assertEqual(i, gen.next())

    def testPreOrder(self):
        tree = BinaryTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        for v in tree.preOrder():
            #print v
            pass
            #ToDo: Test the post Order Sequence

    def testPostOrder(self):
        tree = BinaryTree()
        l = [8, 4, 2, 1, 3, 6, 5, 7, 12, 10, 9, 11, 14, 13, 15]
        for d in l:
            tree.insert(d)

        #ToDo: Test the post Order Sequence


if __name__ == "__main__":
    unittest.main()
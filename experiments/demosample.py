'''The Sample classes that support the Sound class and allow manipulation
of individual sample values.'''

class MonoSample(object):
    '''A sample in a single-channeled Sound with a value.'''
    
    def __init__(self, samp_array, i):
        '''Create a MonoSample object at index i from numpy array object 
        samp_array, which has access to the Sound's buffer.'''
        
        # negative indices are supported
        if -len(samp_array) <= i <= len(samp_array) - 1:    
            self.samp_array = samp_array
            self.index = i
        else:
            raise IndexError('Sample index out of bounds.')


    def __str__(self):
        '''Return a str with index and value information.'''
        
        return "Sample at " + str(self.index) + " with value " \
                 + str(self.get_value())
    

    def set_value(self, v):
        '''Set this Sample's value to v.'''
        
        self.samp_array[self.index] = int(v)


    def get_value(self):
        '''Return this Sample's value.'''
        
        return self.samp_array[self.index]


    def get_index(self):
        '''Return this Sample's index.'''
        
        return self.index
    
    def __cmp__ (self, other):
        return cmp(self.samp_array[self.index], other.samp_array[other.index])
        
        
class StereoSample(object):
    '''A sample in a two-channeled Sound with a left and a right value.'''

    
    def __init__(self, samp_array, i):
        '''Create a StereoSample object at index i from numpy array object 
        samp_array, which has access to the Sound's buffer.'''
       
        # negative indices are supported
        if -len(samp_array) <= i <= len(samp_array) - 1:    
            self.samp_array = samp_array
            self.index = i
        else:
            raise IndexError('Sample index out of bounds.')


    def __str__(self):
        '''Return a str with index and value information.'''
        
        return "Sample at " + str(self.index) + " with left value " \
                 + str(self.get_left()) + " and right value " + \
                 str(self.get_right())

    
    def set_values(self, left, right):
        '''Set this StereoSample's left value to left and 
        right value to right.'''
        
        self.samp_array[self.index] = [int(left), int(right)]
    

    def get_values(self):        
        '''Return this StereoSample's left and right values as a tuple 
        (left, right) of two ints.'''
        
        return tuple(self.samp_array[self.index])

    
    def set_left(self, v):
        '''Set this StereoSample's left value to v.'''
        
        self.samp_array[self.index, 0] = int(v)


    def set_right(self, v):
        '''Set this StereoSample's right value to v.'''
        
        self.samp_array[self.index, 1] = int(v)
        
        
    def get_left(self):
        '''Return this StereoSample's left value.'''

        return self.get_values()[0]
    
    
    def get_right(self):
        '''Return this StereoSample's right value.'''

        return self.get_values()[1]


    def get_index(self):
        '''Return this Sample's index.'''
        
        return self.index
        
def __cmp__ (self, other):
  '''The bigger sample is the one with the biggest sample in any channel'''
  
  self_max = max(self.get_values())
  other_max = max(other.get_values())
  return max (self_max, other_max)

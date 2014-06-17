def check_braces_stack(str):
    s = []
    for c in str:
        if c == '(':
            s.append(c)
        elif c == ')':
            if len(s) == 0:
                return False
            top = s.pop()
        else:
            print 'Found some other character!'
    if len(s) > 0:
        return False
    return True

def check_braces(str):
    op = 0
    cl = 0
    for c in str:
        if c == '(':
            op = op + 1
        elif c == ')':
            op = op - 1
            if op < 0:
                return False
        else:
            print 'found some other character!'
    if op > 0:
        return False
    return True

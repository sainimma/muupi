

class Calculator(object):

    @classmethod
    def add(cls, x, y):
        sum = x + y
        return sum

    @classmethod
    def subtract(cls, x, y):
        diff = x - y
        return diff

    @classmethod
    def multiply(cls, x, y):
        product = x * y
        return product

    @classmethod
    def divide(cls, x, y):
        quotient = x / y  # y=0 is a bug
        return quotient


def method_name():
    print 'this is a method'

print Calculator.add(4, 5)
print Calculator.subtract(5, 4)

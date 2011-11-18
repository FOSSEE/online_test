from exam.models import Question

questions = [
Question(
    summary='Factorial',
    points=2,
    description='''
Write a function called "fact" which takes a single integer argument (say "n") 
and returns the factorial of the number.
For example fact(3) -> 6''',
    test='''
assert fact(0) == 1
assert fact(5) == 120
'''),
    
Question(
    summary='Simple function',
    points=1,
    description='''Create a simple function called "sqr" which takes a single 
argument and returns the square of the argument. For example sqr(3) -> 9.''',
    test='''
import math
assert sqr(3) == 9
assert abs(sqr(math.sqrt(2)) - 2.0) < 1e-14 
    '''),
]
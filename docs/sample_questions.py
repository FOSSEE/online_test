from datetime import date

questions = [
Question(
    summary='Factorial',
    points=2,
    language="python",
    description='''
Write a function called <code>fact</code> which takes a single integer argument
(say <code>n</code>) and returns the factorial of the number. 
For example:<br/>
<code>fact(3) -> 6</code>
''',
    test='''
assert fact(0) == 1
assert fact(5) == 120
'''),
    
Question(
    summary='Simple function',
    points=1,
    language="python",
    description='''Create a simple function called <code>sqr</code> which takes a single 
argument and returns the square of the argument. For example: <br/>
<code>sqr(3) -> 9</code>.''',
    test='''
import math
assert sqr(3) == 9
assert abs(sqr(math.sqrt(2)) - 2.0) < 1e-14 
    '''),
Question(
    summary='Bash addition',
    points=2,
    language="bash",
    description='''Write a shell script which takes two arguments on the
    command line and prints the sum of the two on the output.''',
    test='''\
#!/bin/bash
[[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))
#++++++
1 2
2 1
'''),
]

quiz = Quiz(start_date=date.today(),
            duration=10,
            description='Basic Python Quiz 1'
            )

print('hello from foo.py')

import nimporter
print(dir(nimporter))
import bar

print(bar.hello('Pebaz'))

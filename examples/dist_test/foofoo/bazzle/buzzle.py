import nimporter
from bazzle import bar

print(bar.__file__, bar.__loader__)
print(bar.hello('world'))

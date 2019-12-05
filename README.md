# Nimpy

![License](https://img.shields.io/github/license/Pebaz/nimpy)

Compile Nim extensions for Python on import automatically!

With Nimpy for Python, you can simply import Nim source code files *as if they
were Python modules*, and use them seamlessly with Python code.

## Possible Benefits

 * Seamless integration with existing Nim code by using the
   [Nimpy](https://github.com/yglukhov/nimpy) library for Nim.
 * Very low effort to create high-performance Python extensions using Nim.
 * Leverage both language's ecosystems: Python for breadth, Nim for performance.

### Dependencies

 1. Nim Compiler
 2. [Nimpy library for Nim](https://github.com/yglukhov/nimpy)
 3. [Nimpy library for Python](https://github.com/Pebaz/nimpy) (this library).

### Installation

```bash
# Windows
$ pip install git+https://github.com/Pebaz/nimpy  # Nimpy library for Python
$ nimble install nimpy  # Nimpy library for Nim

# Everything Else
$ pip3 install git+https://github.com/Pebaz/nimpy  # Nimpy library for Python
$ nimble install nimpy  # Nimpy library for Nim
```

### Examples



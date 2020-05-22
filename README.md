
<p align="center"><img width=200px src="https://raw.githubusercontent.com/Pebaz/Nimporter/master/nimporter-logo.png"></p>

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![License](https://img.shields.io/github/license/Pebaz/Nimporter)
![Version](https://img.shields.io/pypi/v/nimporter)
![Downloads each Month](https://img.shields.io/pypi/dm/Nimporter)
![Wheel Supported](https://img.shields.io/pypi/wheel/Nimporter)

# Nimporter

Compile [Nim](<https://nim-lang.org/>) extensions for Python on import automatically!

## What is Nimporter

> With Nimporter, you can simply import Nim source code files *as if they
were Python modules*, and use them seamlessly with Python code.

## Possible Benefits

 * Performance: Nim compiles to C
 * Reduce cloud computing costs without writing C
 * Leverage both language's ecosystems: [Python](https://pypi.org/) for breadth,
 [Nim](https://nimble.directory/) for performance.
 * Seamless integration with existing Nim code by using the
   [Nimpy](https://github.com/yglukhov/nimpy) library.
 * Very low effort to create high-performance Python extensions using Nim.
 * 100% transparent to end users (doesn't require Nim compiler).

## Installation

```bash
$ pip install nimporter
```

Dependencies:

 1. [Nim Compiler](<https://nim-lang.org/install.html>) (for compiling Nim
 source files)
 2. [Nimpy library](https://github.com/yglukhov/nimpy) (Installed automatically)
 3. [Nimporter library](https://github.com/Pebaz/nimporter) (distributed
 libraries will need access to Nimporter).

Nimporter can work seamlessly when Nim is installed via
[Choosenim](https://nim-lang.org/install_unix.html#installation-using-choosenim)
or manually. No additional configuration is necessary once installed since
Nimporter can find the Nim standard library and install
[Nimpy library](https://github.com/yglukhov/nimpy) if Nimble is on your path.

## About

Nimporter provides an official way to develop applications and libraries that
make use of Nim code for achieving higher performance.

It does this by providing a way to directly import Nim code and have it be
compiled at runtime. However, unlink Cython, this will not proliferate your
development environment and require adding bunches of exceptions to your
`.gitignore` file.

All artifacts are stored in their respective `__pycache__` directories. Builds
are cached so that subsequent imports do not trigger a rebuild.

Nimporter allows you to treat Nim files exactly like Python modules. This means
that namespacing is maintained for package heirarchies.

Here is a quick example of how to directly import Nim code:

**nim_math.nim**

```nim
import nimpy

proc add(a: int, b: int): int {.exportpy.} =
    return a + b
```

**Python file in same directory**

```python
# Nimporter is needed prior to importing any Nim code
import nimporter, nim_math

print(nim_math.add(2, 4))  # 6
```

Does Nimporter support single-file Nim modules only? No, Nimporter allows you to
treat an entire Nim project as a single module. The project must contain a
`.nimble` file that is used to build the project into a single library. Since
`.nimble` files are supported, this means that they can rely on Nim dependencies
and still be imported and compiled at runtime.

Have a complex build requirement that would normally entail tweaking Nim
compiler switches for each supported platform? Nimporter fully supports adding a
`switches.py` file for libraries that need to customize the CLI flags for any
platform seamlessly for both developing and bundling extensions.

Since Nimporter relies on [Nimpy](https://github.com/yglukhov/nimpy) for Nim <->
Python interaction, it is a required dependency during development for every
module and library. Nimporter ensures that this is installed prior to every
compilation so that users do not have a separate `nimble install nimpy` step.

Additionally, for users who do not have access or are not interested in
installing a Nim compiler, Nimporter makes distribution effortless.

After creating an entire project with many Python and Nim modules/libraries in a
deeply-nested package heirarchy, Nimporter allows you to bundle all of this into
a single wheel just as you would with Python.

To do this, you need to add a single line to your `setup.py`:

```python
from setuptools import setup
import nimporter

setup(
    ...,

    # This is all the effort required to bundle all Nim modules/libraries
    ext_modules=nimporter.build_nim_extensions()
)
```

> Please note that the official distribution mechanism only requires a single
line of code.

Additionally, all namespaces are preserved in the built extensions and end-users
can merely install the resulting wheel containing the binary artifacts without
compiling on the target machine.

In summary, Nimporter is a library that allows you to use Nim along with Python
effortlessly by exposing two very simple APIs:

```python
import nimporter  # Required prior to any Nim module import

# 1. Import Nim code directly
import my_nim_module

# 2. Find, build, and bundle all Nim extensions automatically
nimporter.build_nim_extensions()
```

*How much simpler could it possibly get?*

## Documentation

For tutorials, advanced usage, and more, head over to the
[Wiki](<https://github.com/Pebaz/nimporter/wiki>).

Generated documentation can be found
[here](https://pebaz.github.io/nimporter/index.html).

For a bunch of little examples, look in the `examples/` directory. For more
rigorous examples testing every feature of Nimporter, you can take a look at the
files within the `tests/` directory.

## Distributing Libraries Using Nimporter

Nimporter supports two methods of distribution:

* Source
* Binary (Wheel)

If your library makes use of Nimporter for integrating Nim code, you will need
to include it with your dependency list. Even for binary distributions which
compile each extension to prevent compilation on the end-users machine.

### Binary Distributions

Binary (wheel) distributions allow you to forego compilation of Nim source files
on the end user's machine. This has enormous benefit and can be accomplished
very easily by adding the following line to your `setup.py` file:

```python
...
import nimporter

setup(
    ...,                                          # Keep your existing arguments
    ext_modules=nimporter.build_nim_extensions()  # Recurse+build Nim extensions
)
```

To create the binary distribution:

```bash
$ python setup.py bdist_wheel
```

When installing via Pip, the appropriate wheel version will be selected,
downloaded, and installed, all without requiring users to install a Nim
compiler.

> Special note for Linux users: Unfortunately, PyPi will not allow you to upload
just any Linux wheel. There is a special compilation process that can be
explained [here](https://github.com/pypa/manylinux). Interestingly enough, I got
around this by simply renaming the resulting Linux build according to the
**manylinux1** naming convention. You can see my solution in the
`examples/github_actions_template.yml` file for the `build-linux` job. I expect
that there could be many downsides of using this hack but it worked for me on 2
different Linux platforms.

### Source Distributions

Source distributions allow users to bundle Nim files so that end-users can
compile them upon import just how they would during normal development.

The only supported way of providing a source distribution is to bundle the Nim
files along with the Python source files.

To do this, add these lines to your `setup.py` file:

```python
setup(
    ...,                            # Keep your existing arguments
    package_data={'': ['*.nim']},   # Distribute Nim source files
    include_package_data=True,
    install_requires=['nimporter']  # Depends upon Nimporter
)
```

To create the source distribution:

```bash
$ python setup.py sdist
```

When installing via Pip and a binary distribution (wheel) cannot be found for a
given platform, the source distribution will be installed which will include the
bundled Nim source files. When the library is imported on the end-users's
machine, Nimporter compiles all of the Nim files as they are imported
internally which will cause a small delay to account for compilation. When the
library is subsequently imported, no compilation is necessary so imports are
extremely fast.

### Publish Build Artifacts to PyPi Automatically

Since binary distributions allow Nimporter libraries to be distributed without
requiring a Nim compiler, they are the recommended packaging type. However,
building for each platform can be tedious.

For a dead-simple way to publish Windows, MacOS, and Linux wheels to PyPi
automatically, use the `github_actions_template.yml` template found in the
`examples/` directory. This template integrates with your repository's GitHub
Actions runner to build, package, and deploy your library on Windows, MacOS, and
Linux automatically when you create a new "Release" is created.

### Usage with Docker

Nimporter can easily be used within a Docker container. To prevent the need for
a Nim compiler toolchain to be installed into the container to run Nim code, you
can pre-compile all of your extensions and copy the resulting artifacts into the
container. This process is roughly as follows:

1. Create a project that uses Python and Nim
2. Run `nimporter compile` to recursively-compile all extensions in the project
3. Ensure that in your Dockerfile that the `__pycache__` directories are
   included as they will contain the Nim shared objects as well as the Nimporter
   hash files to prevent a recompilation.

## Nimporter Command Line Interface

Nimporter provides a CLI that you can use to easily clean all cached build and
hash files from your project recursively. This can be very useful for debugging
situations arising from stale builds.

Usage example:

```bash
# Recursively removes all hashes and cached builds
$ nimporter clean
```

Additionally, the CLI can also be used like a compiler to produce a binary
extension (`.pyd` and `.so`) from a given Nim file.

```bash
# Stores build in __pycache__
# Can be imported by first importing nimporter
$ nimporter build file.nim

# Stores build in current dir
$ nimporter build file.nim --dest .

# Same 2 examples but for Nim libraries
$ nimporter build mylib
$ nimporter build mylib --dest .

# Although you can specify a Nim library's source file, please don't
$ nimporter build mylib/mylib.nim
```

The Nimporter CLI can also precompile all extensions within a project without
needing to run the project. This is useful in situations where you do not want
to package your application using a `setup.py` (such as a zip file) or for use
within Docker containers.

```bash
# Recursively compile all Nim extension modules and libraries:
$ nimporter compile
```

Finally, the CLI has provisions for quickly bundling your project into a source
or binary distribution:

```bash
# Bundles your code into a wheel (look in dist/)
$ nimporter bundle bin

# Bundles your code into a source archive (look in dist/)
$ nimporter bundle src
```

If you do not have a `setup.py` in your current directory, the CLI will generate
one for you but you will have to edit it to make sure that all of your code is
included in the resulting package. You can look
[here](https://github.com/navdeep-G/setup.py) for an excellent tutorial on how
to use `setup.py`.

## Code Quality

There are ***44 unit tests*** and ***5 integration tests*** to make sure that
Nimporter performs as advertised.

In addition, Nimporter has ***94% code coverage*** so a host of bugs have already been
caught and dealt with in a manner befitting their wretched existence.

Lastly, it has been tested and fully supported on these platforms:

* **Windows 10**
* **MacOS Mojave**
* **Linux**

> Just for fun, I got out my Windows laptop, Mac, and SSHed into a Linux box on
AWS. I then ran the test suite on all 3 platforms simultaneously. ;)

Nimporter likely works on a bunch of other platforms but I cannot justify the
time required to test them at this point.

### Running The Tests

To run these on your local machine, you will need to install a Nim compiler.

This example will assume you are cloning the GitHub reposotory.

```bash
$ git clone https://github.com/Pebaz/Nimporter
$ cd Nimporter
$ pip install -r requirements.txt
$ pip install .  # Nimporter is needed for the integration tests
$ pytest --cov=. --cov-report=html tests
```

## How Does Nimporter Work?

Nimporter provides essentially two capabilities:

* The ability to directly import Nim code
* The ability to bundle Python-compatible extensions for any supported platform

The way it accomplishes the ability to import Nim code is by adding two custom
importers to the Python import machinery. This is why it is required to import
Nimporter before importing any Nim code because the Python import machinery must
be amended with the custom importers.

The first one is for the ability to search and import Nim modules. When a Nim
module is found, Nimporter first looks in the `__pycache__` directory to see if
there is already a built version of the module. If there is not, it builds a new
one and stores it in the `__pycache__` directory.

If one is found, it could be stale meaning the Nim file could have been modified
since it was built. To keep track of this, a hash of the source file is also
kept in the `__pycache__` directory and is consulted whenever there is a
possibility that a stale build could be imported.

When a Nim module and a Python module have the same name and reside in the same
folder, the Python module is given precedence. *Please don't do this.*

The second custom importer has the exact same purpose of the first one except it
is used to import Nim extension libraries. A library is any folder within a
Python project that contains a `<lib name>.nim` and a `<lib name>.nimble` file.

These files mark that the folder should be treated as one unit. It also makes it
so that Nimble dependencies can be installed.

As for the second capability, Nimporter helps you bundle and distribute Nim code
as part of a binary distribution extremely easily.

The way it works is by iterating through your entire project and identifying any
Nim module and Nim library that it finds and compiling them to C using a feature
of Nim that specifically supports this.

Why compile to C? Because Python already has extensive infrastructure to support
the compilation and distribution of C extensions.

Once each Nim module and library is compiled to C, Python deals with them the
exact same way as a typical C extension. These extensions are then bundled into
the resulting binary distribution and can be uploaded to PyPi or similar.

Are source distributions supported? Yes and no. They are officially supported
for bundling the Nim source files themselves into the archive, but not the C
source files. Although the C source files would be a better alternative, the C
files generated by Nim are platform specific, so they would only be of use to
users on the same exact platform and architecture. This is why the official way
of distributing Nimporter libraries is by creating binary wheels.

## State Of The Project

I have implemented all of the features that I wanted to add at this time. I made
sure to validate the effectiveness of each feature with the unit and integration
tests. This project should be considered "done" and will receive no further
enhancements except for bug fixes and patches. You can submit a bug report on
Nimporter's [GitHub Issues](https://github.com/Pebaz/nimporter/issues) page.

## Contributing

Although I would not seek to add any new features to Nimporter, there may exist
certain modifications that would enhance the effectiveness of Nimporter's core
features. Pull requests are welcome, especially for fixing bugs.

## Special Thanks

Nimporter would not be possible without
[Nimpy](https://github.com/yglukhov/nimpy). Thank you
[Yuriy Glukhov](https://github.com/yglukhov) for making this project possible!

## Stargazers Over Time

[![Stargazers Over Time](https://starchart.cc/Pebaz/nimporter.svg)](https://starchart.cc/Pebaz/nimporter)

> Made using <https://starchart.cc/>

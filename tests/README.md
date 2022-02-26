# Tests

### Build Artifact Cache Problem

There is a need for a bit of explaination for the structure of these unit and
integration tests.

Initially, I had each and every test run `nimporter_cli.clean()` to remove any
previous build artifacts and hashes in order to make sure that they didn't use
a cached version which would make the test essentially meaningless.

This works great on Unix platforms. Unfortunately, on Windows, PYDs loaded by
Python's process cannot be unloaded. There is actually no way to unload these
files during runtime. I thought that Pytest launched a new process for each
test but that is not the case.

The significance of this is that Windows blocks anyone from deleting the file
while Python is using it, meaning that `nimporter_cli.clean()` cannot be run in
any capacity to delete the cached build artifacts.

### My Solution

In order for unit tests to be able to compile a new version of the artifact
they need each and every time the tests are run, I did 2 things:

1. Run `nimporter_cli.clean()` before any tests are run using a `conftest.py`
   hook.
2. Ensure all tests build modules and libraries that are unique to them. Make
   sure no two tests are importing the same module.

As portable as Python code is, there are still some concessions to be made when
writing cross-platform code.

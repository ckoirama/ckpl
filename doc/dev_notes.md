Dev notes
=========

FAQ
===

Q. Why you used `importlib` instead of `from . import <module>`?

A. Because for pedagogical purporses, the modules show their sequential
nature using an ordinal number as prefix. `from . import <module>` do not
support numerical prefix, but `ìmportlib` does. `imporlib`
is a native Python function with exactly the same result. 
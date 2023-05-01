# hb

Hierarchical decentralized build system based on ninja.

A build system that uses distributed build description (in hb.py files),

Targets can be built in any directory containing a hb.py file.  Other hb.py
files are automatically and recursively scanned based on paths used by the
rules in the hb.py in the current directory.

## Key concepts

- Path Set

  An ordered set of file paths.  A typical path set contains the source files
  needed to build a target, e.g. the C-files needed to compile and link a
  C-program.

  Path sets are programmatically created and aggregated in hb.py files.

- Rule

  A function that builds targets. Each call to a rule function creates one or
  more targets in the resulting ninja build.



## Examples

### hb.py

```Python

def build(hb):

    csrc = hb.pathset(
        "foo.c",  # plain files
        "bar.c",
        "special/*.c",  # globbing can be used to collect files.
                        # Should it use git ls-files?
        "../rel/path/@csrc",  # path set "csrc" in hb.py in path relative
                              # to this hb.py file
        "$root/path/to/@csrc",  # path set "csrc" in hb.py in path relative
                                # to root of build tree
    )

    # Compile baz.c, return path set with resulting object file
    baz = hb.gcc("baz.c", cflags="-DFIX_THAT_BUG")

    csrc += ["main.c", baz]  # Add to existing path set

    hb.export("csrc", csrc)  # Export path to make it available to
                             # other hb.py files

    hb.gcc(csrc, link="prog")  # Call rule function to build C program
                               # into executable "prog"
```

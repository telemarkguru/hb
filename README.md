# hb
Hierarchical build system based on ninja.

A build system that uses distributed build description (in hb.py files),
and list files (xxx.list).

Targets can be built in any directory containing a hb.py file.  Other hb.py
files are automatically and recursively scanned based on paths used by the
rules in the hb.py in the current diretory.

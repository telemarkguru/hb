from os.path import basename, splitext


def _callback(hb):
    gen_h_files = hb.filter(hb.targets, r"\.h$")
    return {}, gen_h_files


def build(hb):
    @hb.rule(
        "gcc -MMD -MF $depfile $fix $cflags $incp -c $in -o $out",
        callback=_callback,
    )
    def gcc(src="gcc.list", link=None, lib=None, **vars):
        """
        Compile C code using GCC.
        """
        src = hb.pathset(src)
        hfiles, cfiles, ofiles, afiles, cffiles, ldffiles, ldsc = hb.filter(
            src,
            r"\.h$",
            r"\.(c|S|s|cc|cpp)$",
            r"\.o$",
            r"\.a$",
            r"\.cflags$",
            r"\.ldflags$",
            r"\.ld$",
        )
        dirs = hb.directories(src)
        incp = " ".join(f"-I{p}" for p in hb.relative(dirs))
        opath = hb.root + "/build/gcc"
        for cfile in cfiles:
            ofile = f"{opath}/{splitext(basename(cfile))[0]}.o"
            hb.build(gcc, ofile, cfile, oodeps=hfiles, incp=incp, **vars)
            ofiles.append(ofile)

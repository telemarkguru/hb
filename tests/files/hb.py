name = "foo.bar.x"


def build(hb):
    hb.floppydisk = 3
    global name
    name = "foo.bar.y"

    test1 = hb.export(
        "test1",
        "foo.bar",
        "subdir/@test2",
        "bar.foo",
        "subdir/@test2",  # duplicate OK
        "subdir2/bar/@files",
    )

    hb.export(
        "test2",
        test1,
        "nonexistent/directory/file.txt",
    )

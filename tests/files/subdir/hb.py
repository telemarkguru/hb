def build(hb):
    hb.subdir = True
    hb.export(
        "test2",
        "../foo.bar",
        "foo.bar",
    )

# CMPCT project releases

Every material CMPCT milestone receives a unique project version and a release note in this directory. Project versioning is independent from the on-disk format revision: an encoder/research/portability milestone can advance the project version without changing archive grammar. Reader-visible storage semantics require both a project-version bump and the appropriate format-revision bump.

The CI version-discipline gate rejects material code/benchmark/integration changes that reuse the previous project version.

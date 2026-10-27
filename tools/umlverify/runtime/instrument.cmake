# The traced build of the sequence-diagram flow.
#
# The verifier configures a second build of impl/ with -DCMAKE_PROJECT_INCLUDE=<this file>, so
# it runs right after the project's own project() call: every source is compiled with function
# entry/exit hooks, nothing is optimised away, and the trace runtime (uml_trace.cpp, compiled by
# the verifier into ${UML_TRACE_RUNTIME}) is linked into every executable. The project's own
# CMakeLists.txt is used unchanged.
add_compile_options(-finstrument-functions -g -O0)
add_link_options("${UML_TRACE_RUNTIME}")

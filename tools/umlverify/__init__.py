"""umlverify — check an implementation against a UML design drawn in draw.io.

Each kind of UML diagram has its own *flow*: a subpackage with

    NAME    the input file name it handles, without .drawio ("class" -> class.drawio)
    FILE    that file name as shown to people ("class.drawio", "state-<class>.drawio")
    SUBJECT set when the file name carries a subject after a dash: state-door.drawio
            is the state machine of the class Door
    TITLE   a human-readable name
    run(ctx: core.project.Context) -> core.compare.Result
            reads ctx.input, writes ctx.output(...) and ctx.report; raises
            core.project.FlowFailed when it cannot produce a report, or its
            subclass NotReady when the project has not got that far yet

The input file's name picks the flow. To add a diagram type, write the subpackage
and register it in FLOWS below; see docs/README.md.
"""
from pathlib import Path

from . import class_diagram, sequence_diagram, state_diagram

FLOWS = {flow.NAME: flow for flow in (class_diagram, state_diagram, sequence_diagram)}


def flow_for(input_path):
    """The flow for diagrams/input/<name>.drawio, or None if the type is not supported."""
    head, dash, subject = Path(input_path).stem.partition("-")
    flow = FLOWS.get(head)
    if flow is None:
        return None
    needs_subject = bool(getattr(flow, "SUBJECT", None))
    return flow if needs_subject == bool(dash and subject) else None


def supported():
    return [FLOWS[name].FILE for name in sorted(FLOWS)]

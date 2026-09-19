"""Declarative Stage D roles; these are potential roles, not authority grants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    role: str
    description: str
    potential_operations: tuple[str, ...]


ROLE_DEFINITIONS = {
    item.role: item for item in (
        RoleDefinition("CONVERSATIONAL", "Human-facing conversation; no project mutation.", ("REQUEST_CLARIFICATION",)),
        RoleDefinition("PLANNER", "Proposes planning artifacts.", ("CREATE_ARTIFACT", "REQUEST_REPLAN")),
        RoleDefinition("GRAPH_EVALUATOR", "Evaluates execution graphs.", ("CREATE_ARTIFACT",)),
        RoleDefinition("SCOUT", "Searches and reads project material.", ("READ", "REQUEST_CONTEXT")),
        RoleDefinition("CONTEXT_COMPILER", "Constructs context artifacts.", ("READ", "CREATE_ARTIFACT", "REQUEST_CONTEXT")),
        RoleDefinition("BUILDER", "Performs narrowly scoped implementation work.", ("READ", "WRITE", "EXECUTE", "CREATE_ARTIFACT")),
        RoleDefinition("SPEC_VERIFIER", "Tests against the approved specification.", ("READ", "EXECUTE", "CREATE_ARTIFACT")),
        RoleDefinition("STANDARDS_REVIEWER", "Reviews standards compliance.", ("READ", "EXECUTE", "CREATE_ARTIFACT")),
        RoleDefinition("INTEGRATOR", "Performs explicitly scoped integration work.", ("READ", "WRITE", "EXECUTE", "CREATE_ARTIFACT")),
        RoleDefinition("INTEGRATION_VERIFIER", "Tests integration results.", ("READ", "EXECUTE", "CREATE_ARTIFACT")),
        RoleDefinition("PROMOTER", "Performs an explicitly authorized promotion.", ("STATE_TRANSITION",)),
        RoleDefinition("CONTROLLER", "Validates and transitions lifecycle state.", ("STATE_TRANSITION", "APPEND_EVENT")),
    )
}

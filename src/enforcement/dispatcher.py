"""
Sovereignty Control System — Enforcement Dispatcher (v0.9)

This module introduces a *routing layer* between governance decisions and
enforcement effectors.

Key guarantees:

- The dispatcher does NOT:
  - make governance decisions
  - infer policy
  - log anything by itself
  - talk to external systems

- The dispatcher DOES:
  - accept an explicit enforcement request
  - route each declared action to a matching effector
  - return a structured, auditable result describing what happened

This keeps the separation:
    decision ≠ enforcement ≠ logging

Logging for enforcement events (e.g. to data/enforcement_log.jsonl) is expected
to be handled by a separate component that consumes the dispatcher results.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Protocol


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------


class EnforcementOutcome(str, Enum):
    """
    Outcome of an individual enforcement action.

    - SUCCESS          → effector executed and reported success
    - NOOP             → effector executed but decided nothing needed to change
    - NOT_APPLICABLE   → action not applicable given the decision/context
    - NOT_IMPLEMENTED  → no effector registered for this action_type
    - FAILED           → effector attempted execution and failed
    """

    SUCCESS = "SUCCESS"
    NOOP = "NOOP"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class EnforcementAction:
    """
    Declarative description of a single enforcement effect to be attempted.

    This is intentionally generic. The governance / CLI layer is responsible for
    constructing these actions explicitly; the dispatcher does not infer them.
    """

    action_type: str  # e.g. "lockdown_state", "send_notification"
    target: Optional[str] = None  # e.g. "system", "tenant:abc", "user:alice"
    parameters: Dict[str, Any] = None  # additional structured parameters

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Ensure parameters is always a dict in the representation
        if data["parameters"] is None:
            data["parameters"] = {}
        return data


@dataclass(frozen=True)
class EnforcementContext:
    """
    Context for enforcement, derived from the decision and its environment.

    This is deliberately treated as an opaque blob by the dispatcher; the schema
    can evolve without changing the dispatcher itself.

    Example fields (non-exhaustive, all optional):
      - decision_outcome: "ALLOW" | "DENY" | "REQUIRE_ADDITIONAL_APPROVAL"
      - decision_id: str
      - principal_id: str
      - principal_labels: List[str]
      - delegate_id: Optional[str]
      - delegation_ids: List[str]
      - scenario: Dict[str, Any]  (e.g. inputs to the decision)
    """

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data or {})


@dataclass(frozen=True)
class EffectorResult:
    """
    Result of a single effector handling a single EnforcementAction.
    """

    outcome: EnforcementOutcome
    action: EnforcementAction
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "outcome": self.outcome.value,
            "action": self.action.to_dict(),
            "details": dict(self.details or {}),
        }
        return data


@dataclass(frozen=True)
class EnforcementRequest:
    """
    A complete enforcement request for a single decision.

    The dispatcher does not create EnforcementRequests; it merely consumes them.
    They must be constructed explicitly by the caller (e.g. CLI or orchestration
    layer) to preserve the separation between decision and enforcement.
    """

    decision_reference: Dict[str, Any]
    context: EnforcementContext
    actions: List[EnforcementAction]
    dry_run: bool = False  # when True, effectors must not cause real-world effects

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_reference": dict(self.decision_reference or {}),
            "context": self.context.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
            "dry_run": self.dry_run,
        }


@dataclass(frozen=True)
class EnforcementResult:
    """
    Aggregate result of dispatching a batch of actions for a single decision.
    """

    decision_reference: Dict[str, Any]
    context: Dict[str, Any]
    dry_run: bool
    action_results: List[EffectorResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_reference": dict(self.decision_reference or {}),
            "context": dict(self.context or {}),
            "dry_run": self.dry_run,
            "action_results": [r.to_dict() for r in self.action_results],
        }


# ---------------------------------------------------------------------------
# Effector interface
# ---------------------------------------------------------------------------


class Effector(Protocol):
    """
    Protocol for effectors that can be registered with the dispatcher.

    Implementations MUST:
      - be local-only and side-effect constrained
      - respect dry_run=True (no external effects)
      - avoid any direct logging; they should return structured details instead
    """

    @property
    def action_type(self) -> str:
        """
        The action_type this effector is responsible for.
        Example: "lockdown_state", "send_notification".
        """
        ...

    def execute(
        self,
        action: EnforcementAction,
        context: EnforcementContext,
        dry_run: bool = False,
    ) -> EffectorResult:
        """
        Execute the given enforcement action.

        Effectors MUST:
          - return EffectorResult with an appropriate EnforcementOutcome
          - never raise unhandled exceptions; any internal error must be wrapped
            as outcome=FAILED with diagnostic details
          - treat dry_run=True as: "compute what you WOULD do, but do not
            actually do it"
        """
        ...


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class EnforcementDispatcher:
    """
    Routes explicit EnforcementAction instances to registered effectors.

    Design principles:

      - No implicit behavior:
        The dispatcher NEVER invents actions. If no actions are supplied,
        it returns a result with zero action_results.

      - No logging:
        The dispatcher returns structured data; a separate component is
        responsible for persisting that data (e.g., to enforcement_log.jsonl).

      - No external integrations:
        Any interaction with external systems must be encapsulated inside
        effectors that are carefully controlled and auditable.
    """

    def __init__(self, effectors: Optional[Iterable[Effector]] = None) -> None:
        self._effectors: Dict[str, Effector] = {}
        if effectors:
            for eff in effectors:
                self.register_effector(eff)

    # -------------------------
    # Effector registration
    # -------------------------

    def register_effector(self, effector: Effector) -> None:
        """
        Register an effector for its declared action_type.

        If an effector is already registered for that action_type, it will
        be replaced. This makes wiring explicit and testable.
        """
        action_type = effector.action_type
        if not action_type or not isinstance(action_type, str):
            raise ValueError("Effector.action_type must be a non-empty string")
        self._effectors[action_type] = effector

    def get_registered_action_types(self) -> List[str]:
        """
        List of all action_type values for which an effector is registered.
        """
        return sorted(self._effectors.keys())

    # -------------------------
    # Dispatch
    # -------------------------

    def dispatch(self, request: EnforcementRequest) -> EnforcementResult:
        """
        Execute all declared actions using the registered effectors.

        Behavior:
          - For each action, look up an effector by action.action_type.
          - If none exists, return outcome=NOT_IMPLEMENTED for that action.
          - If an effector exists, invoke effector.execute(...) and capture
            its EffectorResult.
          - Any exception raised by an effector is caught and converted to
            outcome=FAILED with diagnostic details.

        This method is the single entry point for enforcement at this layer.
        """
        action_results: List[EffectorResult] = []

        for action in request.actions:
            effector = self._effectors.get(action.action_type)

            if effector is None:
                # No effector registered → explicit NOT_IMPLEMENTED
                result = EffectorResult(
                    outcome=EnforcementOutcome.NOT_IMPLEMENTED,
                    action=action,
                    details={
                        "reason": "No effector registered for action_type",
                        "action_type": action.action_type,
                    },
                )
                action_results.append(result)
                continue

            try:
                eff_result = effector.execute(
                    action=action,
                    context=request.context,
                    dry_run=request.dry_run,
                )
            except Exception as exc:  # noqa: BLE001
                # Hard guardrail: effectors must not bring down the dispatcher.
                eff_result = EffectorResult(
                    outcome=EnforcementOutcome.FAILED,
                    action=action,
                    details={
                        "reason": "Unhandled exception in effector",
                        "action_type": action.action_type,
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    },
                )

            action_results.append(eff_result)

        return EnforcementResult(
            decision_reference=request.decision_reference,
            context=request.context.to_dict(),
            dry_run=request.dry_run,
            action_results=action_results,
        )


# ---------------------------------------------------------------------------
# Convenience helpers (optional, non-invasive)
# ---------------------------------------------------------------------------


def summarize_enforcement_result(result: EnforcementResult) -> Dict[str, Any]:
    """
    Produce a compact, human-oriented summary suitable for CLI output.

    This does NOT replace the full structured result; it merely offers a
    convenient, non-lossy view that can be rendered in text.

    The structure is intentionally simple and stable.
    """
    summary: Dict[str, Any] = {
        "dry_run": result.dry_run,
        "decision_reference": dict(result.decision_reference or {}),
        "context": dict(result.context or {}),
        "actions": [],
    }

    for r in result.action_results:
        summary["actions"].append(
            {
                "outcome": r.outcome.value,
                "action_type": r.action.action_type,
                "target": r.action.target,
                "details": dict(r.details or {}),
            }
        )

    return summary

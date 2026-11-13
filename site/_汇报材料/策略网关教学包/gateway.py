"""Standard-library policy fixture. It authorizes mock actions; it executes none.

This is not an authentication service, OS sandbox, durable quota system or
production filesystem boundary. ApprovalAuthority represents a trusted control
plane inside one Python process. Untrusted Python in that process can defeat it.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
import hashlib
import json
import math
import time
import uuid

POLICY_VERSION = 'policy-fixture-v1'
REGISTRY_VERSION = 'scientific-operation-fixture-v1'


class PolicyError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Action:
    operation: str
    parameters: dict


@dataclass(frozen=True)
class RunScope:
    run_id: str
    output_root: Path
    allowed_operations: frozenset
    object_ids: frozenset
    artifact_ids: frozenset
    destination_ids: frozenset
    hard_units: int = 12
    approval_units_threshold: int = 5
    principal_id: str = 'principal-demo'
    tenant_id: str = 'tenant-demo'

    def fingerprint(self):
        return digest({'run_id': self.run_id,
                       'principal_id': self.principal_id, 'tenant_id': self.tenant_id,
                       'output_root': str(self.output_root.resolve(strict=True)),
                       'allowed_operations': sorted(self.allowed_operations),
                       'object_ids': sorted(self.object_ids),
                       'artifact_ids': sorted(self.artifact_ids),
                       'destination_ids': sorted(self.destination_ids),
                       'hard_units': self.hard_units,
                       'approval_units_threshold': self.approval_units_threshold})


@dataclass(frozen=True)
class Decision:
    status: str
    reason: str
    layer: str
    run_id: str
    operation: str
    action_digest: str | None
    reserved_units: int
    remaining_units: int
    actual_execution: bool = False


def digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def exact_keys(parameters, expected):
    if not isinstance(parameters, dict) or set(parameters) != set(expected):
        raise PolicyError('PARAMETER_SCHEMA')


def member(value, allowed, code):
    if not isinstance(value, str) or value not in allowed:
        raise PolicyError(code)
    return value


def output_relative(raw, root):
    """One-process check only; a real executor must avoid TOCTOU at open time."""
    if not isinstance(raw, str) or not raw or len(raw) > 512 or '\0' in raw:
        raise PolicyError('OUTPUT_PATH_SCHEMA')
    p = Path(raw)
    if '..' in p.parts:
        raise PolicyError('PATH_TRAVERSAL')
    try:
        root = root.resolve(strict=True)
        candidate = p if p.is_absolute() else root / p
        # Deny symlinks even if they currently resolve back inside the root.
        for parent in [*reversed(candidate.parents), candidate]:
            if parent.is_symlink():
                raise PolicyError('SYMLINK_COMPONENT')
        resolved = candidate.resolve(strict=False)
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            raise PolicyError('OUTPUT_OUTSIDE_SCOPE') from None
        if not rel.parts or resolved.suffix not in {'.json', '.txt'}:
            raise PolicyError('OUTPUT_TYPE')
        if resolved.exists():
            raise PolicyError('OUTPUT_EXISTS')
    except PolicyError:
        raise
    except (OSError, RuntimeError, ValueError):
        # is_symlink/exists can also fail (for example NAME_MAX or encoding),
        # not only resolve. Preserve a DENY decision and its audit receipt.
        raise PolicyError('PATH_CHECK_FAILED') from None
    return rel.as_posix()


def prepare(action, scope, policy_version=POLICY_VERSION):
    """Resolve a finite registered action; documents cannot extend this registry."""
    if not isinstance(action, Action) or not isinstance(action.operation, str):
        raise PolicyError('ACTION_SCHEMA')
    p = action.parameters
    if action.operation == 'inspect_structure':
        exact_keys(p, {'object_id'})
        normalized = {'object_id': member(p['object_id'], scope.object_ids, 'OBJECT_OUTSIDE_SCOPE')}
        units, high_impact = 1, False
    elif action.operation == 'rmsd':
        exact_keys(p, {'reference_id', 'moving_id', 'fit_region', 'units'})
        normalized = {
            'reference_id': member(p['reference_id'], scope.object_ids, 'OBJECT_OUTSIDE_SCOPE'),
            'moving_id': member(p['moving_id'], scope.object_ids, 'OBJECT_OUTSIDE_SCOPE'),
            'fit_region': member(p['fit_region'], {'ALL', 'CORE'}, 'UNSUPPORTED_SELECTION'),
            'units': member(p['units'], {'angstrom'}, 'UNSUPPORTED_UNITS')}
        units, high_impact = 4, False
    elif action.operation == 'contacts':
        exact_keys(p, {'object_id', 'cutoff_A'})
        cutoff = p['cutoff_A']
        try:
            valid_cutoff = not isinstance(cutoff, bool) and isinstance(cutoff, (int, float)) and math.isfinite(cutoff) and cutoff > 0
        except OverflowError:
            valid_cutoff = False
        if not valid_cutoff:
            raise PolicyError('NONFINITE_OR_INVALID_PARAMETER')
        normalized = {'object_id': member(p['object_id'], scope.object_ids, 'OBJECT_OUTSIDE_SCOPE'), 'cutoff_A': float(cutoff)}
        units, high_impact = 4, False
    elif action.operation == 'analyze_batch':
        exact_keys(p, {'object_ids'})
        ids = p['object_ids']
        if not isinstance(ids, list) or not 1 <= len(ids) <= 3 or any(not isinstance(v, str) for v in ids) or len(set(ids)) != len(ids):
            raise PolicyError('BATCH_SCHEMA')
        normalized = {'object_ids': sorted(member(v, scope.object_ids, 'OBJECT_OUTSIDE_SCOPE') for v in ids)}
        # Cost is derived by trusted operation policy, never supplied by the model.
        units, high_impact = 4 * len(ids), False
    elif action.operation == 'write_report':
        exact_keys(p, {'artifact_id', 'output_path'})
        normalized = {'artifact_id': member(p['artifact_id'], scope.artifact_ids, 'ARTIFACT_OUTSIDE_SCOPE'),
                      'output_relative': output_relative(p['output_path'], scope.output_root)}
        units, high_impact = 1, True
    elif action.operation == 'export_report':
        exact_keys(p, {'artifact_id', 'destination_id'})
        normalized = {'artifact_id': member(p['artifact_id'], scope.artifact_ids, 'ARTIFACT_OUTSIDE_SCOPE'),
                      'destination_id': member(p['destination_id'], scope.destination_ids, 'DESTINATION_OUTSIDE_SCOPE')}
        units, high_impact = 1, True
    else:
        raise PolicyError('UNKNOWN_OPERATION')
    if action.operation not in scope.allowed_operations:
        raise PolicyError('OPERATION_NOT_GRANTED')
    payload = {'run_id': scope.run_id, 'scope_digest': scope.fingerprint(),
               'policy_version': policy_version, 'registry_version': REGISTRY_VERSION,
               'operation': action.operation, 'parameters': normalized,
               'reserved_units': units}
    return payload, digest(payload), units, high_impact


class ApprovalAuthority:
    """Trusted in-process approval fixture, with exact binding and single use.

    No identity proof or remote token signing is implemented. A production
    authority must authenticate the reviewer and protect this store separately.
    """
    def __init__(self, clock=time.time):
        self.clock, self.records, self.lock = clock, {}, Lock()

    def issue(self, action, scope, ttl_seconds=60, policy_version=POLICY_VERSION):
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float)) or not math.isfinite(ttl_seconds) or not 0 < ttl_seconds <= 3600:
            raise ValueError('Approval TTL must be positive')
        _, action_digest, _, _ = prepare(action, scope, policy_version)
        token = uuid.uuid4().hex
        with self.lock:
            self.records[token] = {'action_digest': action_digest,
                                   'expires': self.clock()+ttl_seconds, 'used': False}
        return token

    def consume(self, token, action_digest):
        if not isinstance(token, str) or len(token) > 128:
            return 'APPROVAL_UNKNOWN'
        with self.lock:
            record = self.records.get(token)
            if record is None:
                return 'APPROVAL_UNKNOWN'
            if record['used']:
                return 'APPROVAL_ALREADY_USED'
            if record['expires'] <= self.clock():
                return 'APPROVAL_EXPIRED'
            if record['action_digest'] != action_digest:
                return 'APPROVAL_MISMATCH'
            record['used'] = True
        return None


class Gateway:
    def __init__(self, scope, approvals, policy_version=POLICY_VERSION):
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in [scope.hard_units, scope.approval_units_threshold]):
            raise ValueError('Invalid budgets')
        self.scope, self.approvals, self.policy_version = scope, approvals, policy_version
        self.used_units, self.audit, self.lock = 0, [], Lock()

    def authorize(self, action, approval_token=None, untrusted_document=None):
        """Reserve quota and return a mock permit. No file/tool/network action runs."""
        with self.lock:
            action_digest, units = None, 0
            registered = {'inspect_structure', 'rmsd', 'contacts', 'analyze_batch', 'write_report', 'export_report'}
            operation = action.operation if isinstance(action, Action) and isinstance(action.operation, str) and action.operation in registered else '<unregistered>'
            try:
                _, action_digest, units, high_impact = prepare(action, self.scope, self.policy_version)
                if self.used_units + units > self.scope.hard_units:
                    raise PolicyError('HARD_BUDGET_EXCEEDED')
                needs_approval = high_impact or units > self.scope.approval_units_threshold
                if needs_approval and approval_token is None:
                    status, reason = 'NEEDS_APPROVAL', 'EXACT_APPROVAL_REQUIRED'
                elif needs_approval:
                    reason = self.approvals.consume(approval_token, action_digest)
                    if reason:
                        raise PolicyError(reason)
                    self.used_units += units
                    status, reason = 'ALLOW', 'MOCK_PERMIT_RESERVED'
                else:
                    self.used_units += units
                    status, reason = 'ALLOW', 'MOCK_PERMIT_RESERVED'
            except PolicyError as exc:
                status, reason = 'DENY', exc.code
            decision = Decision(status, reason, 'POLICY', self.scope.run_id, operation,
                                action_digest, units if status == 'ALLOW' else 0,
                                self.scope.hard_units-self.used_units)
            # Allowlisted audit fields: never raw parameters, approval token or document.
            event = {'sequence': len(self.audit)+1, **asdict(decision)}
            if isinstance(untrusted_document, str):
                # Hash any Python text without losing an already-reserved decision
                # if an isolated fixture contains an unpaired Unicode surrogate.
                # surrogatepass is for local hashing only, never an outbound payload.
                event['untrusted_document_digest'] = hashlib.sha256(
                    untrusted_document.encode('utf-8', errors='surrogatepass')).hexdigest()
            self.audit.append(event)
            return decision


def redact_synthetic_record(value):
    """Teaching helper for structured fields, not a universal secret detector."""
    secret_fields = {'token', 'api_key', 'authorization', 'password', 'secret'}
    if isinstance(value, dict):
        return {k: '[REDACTED]' if k.lower() in secret_fields else redact_synthetic_record(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_synthetic_record(v) for v in value]
    return value

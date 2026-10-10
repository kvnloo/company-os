export type EvidenceStatus = 'unknown' | 'observed' | 'stale' | 'conflict' | 'pending-proof' | 'verified';
export interface SourceBinding<T> {
  readonly mode: 'source-bound';
  readonly status: EvidenceStatus;
  readonly value: T | null;
  readonly sourceRefs: readonly string[];
  readonly observedAt: string;
  readonly unit: string;
  readonly denominator: number | null;
}
export interface IssueBinding {
  readonly id: 'rings' | 'metrics' | 'lanes' | 'attention' | 'dependency' | 'evidence' | 'hypothesis';
  readonly widget: string;
  readonly region: string;
  readonly meaning: string;
  readonly source: string;
  readonly guard: string;
  readonly issueLines: string;
}
export const issueBindings: readonly IssueBinding[];
/** Validates shape/provenance presence only. This is not source authorization or proof of truth. */
export function acceptSourceBinding<T>(id: IssueBinding['id'], binding: SourceBinding<T>): Readonly<SourceBinding<T>>;
export const fixture: Readonly<{
  mode: 'reference-fixture';
  initialFrameSeconds: 0;
  source: string;
  sourceSha256: string;
  metrics: readonly object[];
  totals: readonly (readonly [string, string])[];
  lanes: readonly (readonly (readonly unknown[])[])[];
}>;

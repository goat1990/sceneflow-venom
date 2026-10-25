---
name: cue-time-repair
description: >-
  Diagnoses and repairs corrupted cue timestamps in Screenplay-Sync JSON cue files,
  specifically fixing LLM timecode hallucinations (such as MM:SS colon stripping where 1:10 becomes 110.0s).
  Triggered when cue timings are out of sync after 60s, or when requested to validate and fix cue timing.
---

# Cue Time Repair Workflow (`/cue-time-repair`)

This skill provides a deterministic diagnostic and repair workflow for cue timing files in SceneFlow / Screenplay-Sync where LLM generation produced invalid total-second timestamps.

## 1. Typical Failure Modes

### A. The "Colon-Stripped MMSS" Anomaly
- **Pattern**: Timestamps $< 60$ are normal seconds (e.g., `58.8`, `59.5`). Timestamps $\ge 60$ jump to $\ge 100$ (e.g., `102.0`, `110.5`, `129.0`).
- **Cause**: The LLM outputs `MM:SS.ss` without a colon as `(MM * 100) + SS.ss`.
- **Diagnostic Signature**:
  - No timestamps exist in the $[60.0, 99.99]$ range.
  - Timestamps $T \ge 100$ have $(T \pmod{100}) < 60$.

### B. Inverted Intervals
- **Pattern**: `startTime > endTime`.
- **Cause**: Fragmented cut/dialogue boundaries or independent coordinate generation.

---

## 2. Mathematical Repair Formulas

For each timestamp $T$:

### Single Minute or Multi-Minute MMSS:
$$\text{minutes} = \lfloor T / 100 \rfloor$$
$$\text{seconds} = T - (\text{minutes} \times 100)$$
$$\text{true\_seconds} = \text{round}(\text{minutes} \times 60 + \text{seconds}, 2)$$

*Example*:
- $102.0 \implies 1 \times 60 + 2.0 = 62.0\text{s}$
- $113.8 \implies 1 \times 60 + 13.8 = 73.8\text{s}$
- $205.4 \implies 2 \times 60 + 5.4 = 125.4\text{s}$

---

## 3. Repair Execution Steps

1. **Locate Target File**: Confirm target file path (e.g., `public/failed_cue.json`).
2. **Run Diagnostics & Repair**:
   Execute the bundled script:
   ```bash
   python .agents/skills/cue-time-repair/scripts/repair_cue_timing.py <input_json> [--output <output_json>] [--in-place]
   ```
3. **Verify Continuity**:
   - Ensure maximum timestamp matches video length.
   - Verify all cuts are strictly monotonic and sequential.
   - Cross-reference dialogue timestamps with scene screenplay table if available.

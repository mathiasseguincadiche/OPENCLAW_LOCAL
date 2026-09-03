from __future__ import annotations

import benchmark_qualification_40m as hard40

QWEN_NATIVE_MAX_OUTPUT_TOKENS = 1024


def main() -> int:
    # Preserve the validated HARD-40M runner while giving the three native-Qwen
    # probes enough output headroom to complete on measured B580 runs. The
    # global 2400s qualification deadline and 210s per-case timeout remain
    # authoritative, and reaching this bound still fails closed as truncation.
    hard40.QWEN_NATIVE_MAX_OUTPUT_TOKENS = QWEN_NATIVE_MAX_OUTPUT_TOKENS
    return hard40.main()


if __name__ == "__main__":
    raise SystemExit(main())

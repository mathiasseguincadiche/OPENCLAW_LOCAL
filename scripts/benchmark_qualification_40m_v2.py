from __future__ import annotations

import benchmark_qualification_40m as hard40

QWEN_NATIVE_MAX_OUTPUT_TOKENS = 768


def main() -> int:
    # Preserve the validated HARD-40M runner while giving the three native-Qwen
    # probes enough output headroom to complete. The global 2400s qualification
    # deadline remains authoritative.
    hard40.QWEN_NATIVE_MAX_OUTPUT_TOKENS = QWEN_NATIVE_MAX_OUTPUT_TOKENS
    return hard40.main()


if __name__ == "__main__":
    raise SystemExit(main())

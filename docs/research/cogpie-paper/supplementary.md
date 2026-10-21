# CogPIE: Supplementary Materials

## S1. Complete Layer 1 Expansion Statistics

For the benchmark profiles, Layer 1 semantic expansion produced:

| Profile | Raw Tokens | Expanded Variants | Expansion Factor |
|---------|-----------|-------------------|-----------------|
| Carlos Eduardo Silva | 15 | 312 | 20.8x |
| Maria Fernanda Costa | 12 | 268 | 22.3x |
| Joao Pedro Almeida | 14 | 295 | 21.1x |
| Ana Beatriz Santos | 11 | 241 | 21.9x |
| Roberto Nascimento | 13 | 278 | 21.4x |

Average expansion factor: 21.5x per raw token.

## S2. Layer 2 Transform Distribution

Analysis of generated candidates by transform type:

| Transform Category | Avg. Candidates per Token | % of Total Output |
|-------------------|--------------------------|------------------|
| Capitalization variants | 7 | 2.1% |
| Numeric suffixes (single digit) | 13 | 3.9% |
| Numeric suffixes (year range) | 134 | 40.1% |
| Special char suffixes | 15 | 4.5% |
| Prefix transforms | 7 | 2.1% |
| Partial leet | 12 | 3.6% |
| Keyboard mutations | 4 | 1.2% |
| Pair combinations | ~142,000 (total) | 42.5% |

## S3. Hybrid Scoring Sensitivity Analysis

Impact of alpha (Markov weight) and beta (frequency weight) on hit rate:

| alpha | beta | Hit Rate (no corpus) |
|-------|------|---------------------|
| 0.2   | 0.1  | 59.8% |
| 0.3   | 0.15 | 60.2% |
| 0.4   | 0.2  | 60.9% |
| 0.5   | 0.2  | 60.5% |
| 0.6   | 0.1  | 59.1% |
| 0.8   | 0.1  | 57.3% |

Default parameters (alpha=0.4, beta=0.2) are near-optimal for untrained operation.

## S4. Performance Profiling

Execution time breakdown per layer (averaged over 5 profiles):

| Layer | Avg. Time (s) | % of Total |
|-------|--------------|-----------|
| Layer 1: Semantic Expansion | 0.002 | 0.2% |
| Layer 2: Cognitive Transforms | 0.310 | 25.4% |
| Layer 3: Probabilistic Ranking | 0.850 | 69.7% |
| Layer 4+5: Scoring + Filtering | 0.057 | 4.7% |
| **Total** | **1.219** | **100%** |

Layer 3 (ranking) dominates execution time due to the O(C * log C) sorting step.

## S5. Memory Usage Profile

| Component | Estimated Memory |
|-----------|-----------------|
| Candidate strings (avg 120k) | 12 MB |
| CRC32 dedup set | 0.5 MB |
| Markov tables (untrained) | 0.1 MB |
| PCFG grammar (untrained) | 0.1 MB |
| Scoring metadata | 15 MB |
| **Total peak** | **~28 MB** |

## S6. Missed Password Analysis

Passwords not found by CogPIE in benchmark:

| Pattern | Example | Reason |
|---------|---------|--------|
| Short token + "!" (< 4 chars) | "rex!" | Tokens < 2 chars filtered in Layer 2 |
| Name@Year with separator | "Carlos@1990" | Now covered after pair transform fix |
| Old PW symbol swap not in map | "Carlos90@" | "@" not in default swap rules for "!" |
| Complex multi-token concat | "CarlosFlamengo!" | Covered by pair transforms |

## S7. Comparison with TarGuess Models

Theoretical comparison (CogPIE was not directly benchmarked against TarGuess):

| Feature | TarGuess | CogPIE |
|---------|----------|--------|
| PII types supported | 7 (name, birthday, email, phone, account, ID, NID) | 9 (+ keywords, pets, old passwords) |
| Probabilistic model | Markov-based | Markov + PCFG hybrid |
| Cultural adaptation | Chinese-focused | Brazilian Portuguese (extensible) |
| Cognitive bias modeling | Implicit | Explicit 5-layer model |
| Semantic expansion | No | Yes (Layer 1) |
| Policy awareness | No | Yes (Layer 5) |
| Open source | Partially | Fully |

## S8. Ethical Use Guidelines

CogPIE is intended exclusively for:

1. **Authorized penetration testing** within contracted engagement scope
2. **Security awareness training** to demonstrate password vulnerability
3. **Academic research** on password security patterns
4. **Password policy evaluation** to assess organizational password strength

CogPIE must NOT be used for:
- Unauthorized access to accounts or systems
- Harvesting or compromising real user credentials
- Stalking or surveillance of individuals
- Any activity without explicit authorization from the system owner

## S9. Reproduction Instructions

```bash
cd WordlistXPL-Forge/

# Install dependencies
python -m pip install -e ".[dev]"

# Run unit tests
PYTHONPATH=. python -m pytest tests/test_cogpie.py -v

# Run benchmarks
PYTHONPATH=. python tests/benchmark_cogpie.py

# Generate candidates for a profile
PYTHONPATH=. python -m wlf_modules.cogpie.cli \
    --profile path/to/profile.json \
    --output candidates.txt \
    --max 100000 \
    --stats
```

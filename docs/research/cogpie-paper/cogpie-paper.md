# CogPIE: A Cognitive Pattern Inference Engine for Targeted Password Candidate Generation

**Andre Henrique de Oliveira**
Uniao Geek Security Research

---

## Abstract

Password security remains one of the most critical challenges in information security. Despite decades of research and policy improvements, users consistently create passwords derived from their personal cognitive context: names, dates, preferences, and memories. This paper presents CogPIE (Cognitive Pattern Inference Engine), a novel 5-layer hybrid algorithm that models these cognitive biases to generate targeted password candidates. CogPIE combines semantic expansion of personal tokens, cognitive transformation rules based on documented psychological biases, a hybrid Markov chain and Probabilistic Context-Free Grammar (PCFG) ranking system, practical entropy scoring, and policy-aware filtering. Our experimental evaluation on synthetic datasets demonstrates that CogPIE achieves a 60.9% hit rate against cognitively-plausible password sets, outperforming CUPP-style profiling (51.7%) and pure Markov approaches (0% without profile information). We provide formal mathematical foundations for each layer, complexity analysis, and a complete open-source implementation. Our findings reinforce that password vaults with cryptographically random generation remain the only reliable defense against targeted attacks informed by personal information.

**Keywords:** password security, cognitive bias, password guessing, Markov chains, PCFG, targeted attacks, personal information, entropy estimation

---

## Resumo (PT-BR)

A seguranca de senhas permanece como um dos desafios mais criticos em seguranca da informacao. Apesar de decadas de pesquisa e melhorias em politicas, usuarios consistentemente criam senhas derivadas de seu contexto cognitivo pessoal: nomes, datas, preferencias e memorias. Este artigo apresenta o CogPIE (Cognitive Pattern Inference Engine), um novo algoritmo hibrido de 5 camadas que modela esses vieses cognitivos para gerar candidatos de senhas direcionados. O CogPIE combina expansao semantica de tokens pessoais, regras de transformacao cognitiva baseadas em vieses psicologicos documentados, um sistema hibrido de ranqueamento por cadeias de Markov e Gramaticas Livres de Contexto Probabilisticas (PCFG), pontuacao de entropia pratica e filtragem sensivel a politicas. Nossa avaliacao experimental em datasets sinteticos demonstra que o CogPIE atinge uma taxa de acerto de 60.9% contra conjuntos de senhas cognitivamente plaussiveis, superando profiling estilo CUPP (51.7%) e abordagens Markov puras (0% sem informacao de perfil). Fornecemos fundamentos matematicos formais para cada camada, analise de complexidade e uma implementacao completa em codigo aberto. Nossos resultados reforcam que cofres de senhas com geracao criptograficamente aleatoria permanecem a unica defesa confiavel contra ataques direcionados informados por informacao pessoal.

**Palavras-chave:** seguranca de senhas, vies cognitivo, adivinhacao de senhas, cadeias de Markov, PCFG, ataques direcionados, informacao pessoal, estimativa de entropia

---

## 1. Introduction

The persistent weakness of human-chosen passwords represents a fundamental tension in cybersecurity: authentication systems require secrets that are both memorable to legitimate users and unpredictable to adversaries. Decades of empirical evidence demonstrate that these goals are fundamentally incompatible when users generate passwords from memory (Bonneau, 2012; Florencio and Herley, 2007; Wang et al., 2017).

The cognitive science literature identifies several biases that systematically reduce password entropy. Anchoring bias causes users to build passwords around a recognizable base word (Abdrabou et al., 2021). The serial position effect concentrates modifications at the beginning and end of passwords (Li et al., 2017). Hyperbolic discounting leads users to prioritize immediate memorability over long-term security (arXiv:2607.19586, 2026). The familiarity heuristic drives selection of personally meaningful tokens: names, dates, pet names, and favorite sports teams (Wang et al., 2016).

Current password guessing approaches fall into two broad categories. Untargeted approaches, including pure Markov models (Ma et al., 2014), PCFG-based generators (Weir et al., 2009), and neural network models such as PassGAN (Hitaj et al., 2019) and PassGPT (Rando et al., 2023), learn statistical patterns from leaked corpora without considering individual user profiles. Targeted approaches, including CUPP (Mebus, 2010), TarGuess (Wang et al., 2016), and Personal-PCFG (Li et al., 2017), incorporate personal information but typically rely on simple concatenation rules without modeling the underlying cognitive processes that drive password creation.

This paper bridges the gap between these approaches by introducing CogPIE (Cognitive Pattern Inference Engine), a 5-layer hybrid algorithm that explicitly models cognitive biases in password creation:

1. **Semantic Expansion** (Layer 1): transforms raw profile tokens into a lattice of semantically related variants through abbreviation, transliteration, leetspeak, and culturally-specific nickname generation.

2. **Cognitive Transforms** (Layer 2): applies transformation rules derived from documented cognitive biases, including capitalization patterns, numeric suffix placement, and partial leetspeak substitution.

3. **Probabilistic Ranking** (Layer 3): combines positional Markov chain probabilities with PCFG structural decomposition and frequency priors from breach statistics into a unified hybrid score.

4. **Entropy Scoring** (Layer 4): estimates practical guessability using a zxcvbn-inspired framework (Wheeler, 2016) augmented with pattern recognition for sequences, dates, and keyboard walks.

5. **Policy Filtering** (Layer 5): ensures output candidates conform to target system password policies, with memory-efficient deduplication.

Our contributions are:
- A formal mathematical framework for cognitive bias modeling in password generation.
- A complete open-source implementation with documented complexity bounds.
- Experimental validation demonstrating superiority over existing targeted and untargeted approaches on synthetic benchmarks.
- Evidence reinforcing that cryptographically random password generation via password managers is the only reliable defense against cognitively-informed attacks.

## 2. Related Work

### 2.1 Untargeted Password Guessing

The foundation of modern password guessing was established by Weir et al. (2009), who introduced Probabilistic Context-Free Grammars (PCFG) for decomposing passwords into terminal classes (alphabetic, numeric, special character segments) and learning probability distributions over production rules. Their approach cracked 28% to 129% more passwords than John the Ripper in controlled experiments, demonstrating the power of grammar-based decomposition.

Markov chain models, particularly with positional awareness, were formalized by Narayanan and Shmatikov (2005) and refined by Ma et al. (2014), who demonstrated that properly configured Markov models with smoothing and backoff can outperform PCFG approaches. The OMEN system (Durmuth et al., 2015) introduced ordered Markov enumeration, achieving over 40% crack rate within 90 million guesses and over 80% at 10 billion guesses, while requiring 8x fewer guesses than John the Ripper's Markov mode for equivalent results.

Neural network approaches emerged with PassGAN (Hitaj et al., 2019), which applied Generative Adversarial Networks to password generation, and PassGPT (Rando et al., 2023), which leveraged the GPT-2 architecture for sequential character-level generation. PassGPT reported roughly 20% more previously unseen passwords than PassGAN, with the additional capability of guided generation through sequential sampling.

### 2.2 Targeted Password Guessing

Wang et al. (2016) formalized targeted online guessing through TarGuess, presenting seven mathematical models that incorporate Personally Identifiable Information (PII) to prioritize guesses. Their work on the "Next Domino to Fall" (Wang et al., 2016) analyzed 28.8 million user accounts across 107 services, finding that 30% of modified passwords could be cracked within 10 guesses and 46.5% within 100 guesses.

Li, Wang, and Sun (2017) extended this line with Personal-PCFG, which models six types of PII (name, birthdate, email, phone, account, ID) as grammar terminals, significantly improving targeted attack efficiency.

CUPP (Mebus, 2010) and bopscrk represent the practitioner-oriented end of this spectrum, generating wordlists from interactive profile gathering with heuristic combination rules but without probabilistic modeling.

### 2.3 Cognitive Biases in Password Creation

Abdrabou et al. (2021) provided neurophysiological evidence that password creation involves measurable cognitive load differences, with strong passwords requiring greater pupil dilation than weak ones (CHI 2021). A 2026 survey of 248 university students (arXiv:2607.19586) found that 76.2% only make minor modifications to existing passwords, with hyperbolic discounting and status quo bias as primary drivers.

Eye-tracking studies (N=109) have demonstrated that cognitive processing styles directly affect password strength, with users exhibiting field-dependent processing styles creating systematically weaker passwords.

Research on AI-generated vs. user-generated passwords (arXiv:2604.19410, 2026) confirmed that self-generated passwords exhibit systematic cognitive bias, while machine-generated passwords are stronger but less memorable: the fundamental tension this paper addresses.

### 2.4 Password Strength Estimation

Bonneau (2012) introduced alpha-guesswork as a rigorous metric for password distribution analysis, analyzing 70 million anonymized passwords and demonstrating that neither Shannon entropy nor Zipfian models accurately capture real password distributions.

Wheeler (2016) operationalized these insights in zxcvbn, a practical password strength estimator that uses pattern matching (dictionary words, dates, sequences, keyboard walks) to estimate guessability rather than relying on composition rules. zxcvbn demonstrated that traditional LUDS (Lowercase, Uppercase, Digits, Symbols) metrics poorly predict actual password strength.

Wang and Jian (2014) revisited Zipf's law in the context of passwords, finding that while password frequency distributions exhibit power-law-like behavior, the fit is imperfect and varies significantly across different password corpora.

### 2.5 Password Policy Standards

NIST SP 800-63B established modern password policy guidelines, recommending minimum 8-character lengths, screening against known breached passwords, discouraging periodic rotation, and encouraging long passphrases. Revision 4 (2024-2025) further recognized synced passkeys at AAL2 and device-bound passkeys at AAL3, reflecting the shift toward passwordless authentication.

### 2.6 Password Reuse

Das et al. (2014) studied password reuse across multiple sites, estimating that 43-51% of users reuse the same password, with simple transformation rules (capitalization changes, suffix additions) applied between sites. Florencio and Herley (2007) established that the average user maintains approximately 25 online accounts but only 6-7 distinct passwords. More recently, Cloudflare (2024) reported that approximately 41% of successful human authentication attempts involve leaked credentials.

## 3. Theoretical Background

### 3.1 Markov Chains for Password Modeling

A character-level Markov chain of order n models password generation as a stochastic process where the probability of each character depends on the preceding n characters. For a password p = c_1 c_2 ... c_L, the probability is:

P_markov(p) = P(c_1 | START^n) * Product_{i=2}^{L} P(c_i | c_{i-n}...c_{i-1}) * P(END | c_{L-n+1}...c_L)

Positional Markov models (as in OMEN) condition additionally on position:

P_pos_markov(p) = Product_{i=1}^{L+1} P(c_i | c_{i-n}...c_{i-1}, pos=min(i,K))

where K is a position cap (typically 20) that groups all positions beyond K into a single bucket.

The transition probabilities are estimated from a training corpus with Laplace smoothing:

P(c | context, pos) = (count(context -> c, pos) + epsilon) / (count(context, pos) + epsilon * |Alphabet|)

where epsilon is the smoothing parameter (typically 0.01).

### 3.2 Probabilistic Context-Free Grammars

A PCFG decomposes a password into structural segments classified by type and length. For a password p with structure S = s_1 s_2 ... s_k (e.g., L5 D3 S1 for a 5-letter word followed by 3 digits and 1 special character):

P_pcfg(p) = P(S) * Product_{i=1}^{k} P(terminal_i | s_i)

where P(S) is the probability of the structural template and P(terminal_i | s_i) is the probability of the specific terminal filling slot s_i.

### 3.3 Hybrid Scoring Function

CogPIE's Layer 3 combines both models with a frequency prior:

H(c) = alpha * log P_markov(c) + (1 - alpha - beta) * log P_pcfg(c) + beta * log P_freq(c)

where:
- alpha in [0,1] controls the Markov model weight (default 0.4)
- beta in [0,1] controls the frequency prior weight (default 0.2)
- P_freq(c) is the empirical frequency of candidate c in known breach data

This formulation is a log-linear combination model, which is convex in the log-probability space and amenable to optimization of the mixing parameters.

### 3.4 Practical Entropy

Following Bonneau (2012) and Wheeler (2016), we define practical entropy as:

E_p(c) = log_2(G(c))

where G(c) is the estimated number of guesses an optimal attacker would require. Unlike Shannon entropy, which treats all symbols as independent, practical entropy accounts for pattern recognition, dictionary lookups, and structural regularities.

### 3.5 Cognitive Bias Formal Model

We model cognitive password creation as a function mapping a user's cognitive context C (comprising personal information, memories, and preferences) to a password through a series of biased transformations:

password = PolicyAdapt(Combine(Transform(Select(C))))

where:
- Select: chooses base tokens from C (anchoring bias)
- Transform: applies modifications (familiarity heuristic, minimal effort principle)
- Combine: concatenates transformed tokens (serial position effect)
- PolicyAdapt: minimally modifies to satisfy system requirements (satisficing behavior)

Each stage exhibits measurable bias distributions documented in the literature.

## 4. CogPIE Algorithm

### 4.1 Architecture Overview

CogPIE processes a target profile through five sequential layers, each expanding and refining the candidate set. The algorithm takes as input a structured profile P containing personal tokens and optionally a training corpus T, producing an ordered list of password candidates.

**Algorithm 1: CogPIE Pipeline**

```
Input: Profile P, Corpus T (optional), Policy pi, Budget K
Output: Ordered list of (candidate, score) pairs

1. banks <- SemanticExpand(P)          // Layer 1
2. tokens <- Union of all banks
3. candidates <- {}
4. for t in tokens:                     // Layer 2
5.     candidates <- candidates U CognitiveTransform(t)
6. for (t_a, t_b) in PriorityPairs(banks):
7.     candidates <- candidates U PairTransform(t_a, t_b)
8. if T is not empty:                   // Layer 3 (optional training)
9.     model.train(T)
10. scored <- [(c, model.score(c)) for c in candidates]
11. sort scored by score descending
12. for (c, s) in scored:               // Layer 4 + Layer 5
13.    if pi.accepts(c) and not duplicate(c):
14.        emit (c, EntropyScore(c, s))
15.    if emitted >= K: break
```

### 4.2 Layer 1: Semantic Expansion

Given a profile P with token categories {names, dates, keywords, pets, companies, phones, emails, old_passwords}, the semantic expansion function S maps each raw token t to a set of variants:

S(t) = {t} U case_variants(t) U strip_accents(t) U abbreviations(t) U nicknames(t) U leet_single(t)

The total semantic space is:

SemanticSpace(P) = Union_{category} Union_{t in P[category]} S(t)

For names, additional decomposition occurs:
- Full name -> individual parts (first, middle, last)
- Initials extraction (e.g., "Carlos Eduardo Silva" -> "ces", "CES")
- Culturally-specific nicknames (e.g., "Eduardo" -> "dudu", "edu")

For dates, expansion includes:
- Full format (DDMMYYYY)
- Reversed digits
- Year only (YYYY, YY)
- Day-month combinations (DDMM, MMDD)

**Theorem 1 (Expansion Bound):** For a profile with N raw tokens, the semantic expansion produces at most O(N * E_max) unique variants, where E_max is bounded by the maximum expansion factor per token (empirically 20-50 for names, 8-15 for dates).

### 4.3 Layer 2: Cognitive Transforms

Each expanded token undergoes transformation rules that model documented cognitive biases:

**Capitalization patterns** (Wang et al., 2017):
- First letter: ~60% of capitalized passwords
- All uppercase: ~15%
- Last letter: ~5%
- Alternating: ~3%
- Other patterns: ~17%

**Numeric suffixes** (serial position effect):
- Single digits (1, 2, 3): ~25% of numeric additions
- Birth years (1960-2026): ~20%
- Sequential (123, 1234): ~30%
- Lucky/meaningful numbers: ~25%

**Special character placement:**
- End position: ~85% of special char additions
- Start position: ~10%
- Middle position: ~5%

**Partial leetspeak:**
- Single substitution (e.g., "a" -> "4"): ~70% of leet usage
- Two substitutions: ~20%
- Full leet: ~10% (rare in practice)

The transform function T maps a token t to:

T(t) = Union_{j=1}^{M} T_j(t)

where T_j are individual transform operators and M is the number of transform categories.

**Pair transforms** combine two tokens with separators and suffixes:

PairTransform(a, b) = {f(a) + sep + g(b) + suffix : f in CaseVariants, g in CaseVariants, sep in Separators, suffix in Suffixes}

### 4.4 Layer 3: Probabilistic Ranking

The hybrid ranker assigns each candidate a unified score using the log-linear combination defined in Section 3.3. When no training corpus is available, the ranker uses uniform priors, reducing to a structural complexity estimate.

Training from a corpus updates both the Markov transition tables and the PCFG grammar simultaneously:

```
for password in corpus:
    markov.train(password)    // Update positional n-gram counts
    pcfg.train(password)      // Update structure and terminal counts
    freq[password.lower()] += 1  // Update frequency table
```

**Theorem 2 (Ranking Convergence):** As the training corpus size |T| approaches infinity, the hybrid score H(c) converges to the true log-probability of c under the mixture model, assuming the true password distribution lies within the model family. The convergence rate is O(1/sqrt(|T|)) for the Markov component and O(1/|T|) for the PCFG component.

*Proof sketch:* The Markov component's convergence follows from the consistency of maximum likelihood estimation for finite-state models with Laplace smoothing (Katz, 1987). The PCFG component converges faster due to the finite grammar structure. The frequency prior converges at the parametric rate. The log-linear combination preserves convergence of the components.

### 4.5 Layer 4: Entropy Scoring

Practical entropy estimation combines multiple heuristic detectors:

```
G(c) = base_guesses(c) * pattern_factor(c) * hybrid_factor(c) * repeat_factor(c)
E_p(c) = log2(G(c))
```

where:
- base_guesses(c) = charset^length when c is not in a known dictionary, or rank when it is
- pattern_factor penalizes sequences (x0.01), dates (x0.1), and keyboard walks
- hybrid_factor adjusts based on the Layer 3 score (x0.01 for high probability to x0.5 for low)
- repeat_factor penalizes character repetition

The score mapping follows zxcvbn convention:

| Score | Entropy Bits | Attack Resistance |
|-------|-------------|-------------------|
| 0     | < 10        | < 10^3 guesses    |
| 1     | 10-19       | < 10^6 guesses    |
| 2     | 20-26       | < 10^8 guesses    |
| 3     | 27-33       | < 10^10 guesses   |
| 4     | >= 34       | >= 10^10 guesses  |

### 4.6 Layer 5: Policy Filtering

The policy filter applies target system constraints as a pure predicate function:

accepts(c, pi) = (min_len <= |c| <= max_len) AND char_class_requirements(c, pi) AND (c not in blacklist)

Deduplication uses CRC32 hashing for memory efficiency, trading a negligible false positive rate (approximately 1 in 4.3 billion) for 10x memory reduction compared to storing full strings.

### 4.7 Complexity Analysis

**Time complexity:**
- Layer 1: O(N * E_max) where N = profile tokens, E_max = max expansion factor
- Layer 2: O(N * E_max * T_max + P^2 * S * V^2) where T_max = transforms per token, P = priority pairs, S = separators, V = case variants
- Layer 3: O(C * (n + G)) where C = total candidates, n = Markov order, G = grammar depth
- Layer 4: O(C) linear scan
- Layer 5: O(C) with CRC32 dedup

**Total: O(C * log C)** dominated by the sorting step in Layer 3.

**Space complexity:** O(C + |T| * n * |Alphabet|) where |T| is training corpus size.

For typical parameters (N=50 tokens, E_max=30, T_max=200, P=150 pairs):
- Expected candidate set: 100,000-200,000 candidates
- Memory usage: 50-100 MB for candidate storage, 10-50 MB for trained models
- Execution time: 1-3 seconds on modern hardware

## 5. Implementation

### 5.1 System Architecture

CogPIE is implemented as a Python module within the WordlistXPL-Forge framework, part of the XPL-Suite security toolkit. The implementation consists of six source files totaling approximately 800 lines of Python:

- `semantic_expander.py`: Layer 1 semantic expansion with cultural nickname databases
- `cognitive_transforms.py`: Layer 2 cognitive transformation rules
- `markov_pcfg_hybrid.py`: Layer 3 hybrid probabilistic ranker
- `scorer.py`: Layer 4 practical entropy estimation
- `policy_filter.py`: Layer 5 policy-aware filtering
- `engine.py`: Pipeline orchestrator integrating all layers

### 5.2 Profile Format

Target profiles are specified as JSON documents:

```json
{
    "names": ["Carlos Eduardo Silva"],
    "dates": ["15/03/1990", "1990"],
    "keywords": ["flamengo", "futebol"],
    "pets": ["Rex", "Mel"],
    "companies": ["Empresa ABC"],
    "phones": ["11987654321"],
    "emails": ["carlos.silva@email.com"],
    "old_passwords": ["Carlos90!"],
    "numbers": ["13", "7"]
}
```

### 5.3 Integration with Existing Tools

CogPIE integrates with the WordlistXPL-Forge ecosystem, which already provides:
- A positional Markov engine (OMEN-style, `markov_engine.py`)
- A PCFG generator (`pcfg_engine.py`)
- A CUPP-style profiler (`cupp_engine.py`, `profiler.py`)
- Leetspeak permutation (`leet_permuter.py`)
- Entropy/strength estimation (`entropy_strength.py`)
- Semantic PCFG helpers (`semantic_pcfg.py`)

CogPIE leverages these existing capabilities while providing a unified cognitive bias framework that these individual tools lack.

## 6. Experimental Evaluation

### 6.1 Methodology

We evaluate CogPIE using synthetic datasets generated from five target profiles with known cognitive patterns. Each profile contains names, dates, keywords, pets, companies, phone numbers, emails, and previously known passwords. For each profile, we generate a set of "ground truth" passwords that follow documented cognitive creation patterns.

**Important ethical note:** All experiments use exclusively synthetic data. No real breach data, credentials, or personal information from actual individuals was used at any stage.

We compare three approaches:
1. **CogPIE**: Full 5-layer pipeline (no training corpus, testing pure profile-based generation)
2. **CUPP baseline**: Simple concatenation of profile tokens with basic transforms (names + dates + keywords, case variants, basic separators)
3. **Markov baseline**: Common password dictionary without profile information (simulating an untargeted attack)

### 6.2 Results

| Profile | Real PWs | CogPIE Hits | CogPIE Rate | CUPP Hits | CUPP Rate | Markov Hits | Markov Rate |
|---------|----------|-------------|-------------|-----------|-----------|-------------|-------------|
| Carlos Eduardo Silva | 19 | 12 | 63.2% | 9 | 47.4% | 0 | 0.0% |
| Maria Fernanda Costa | 17 | 11 | 64.7% | 9 | 52.9% | 0 | 0.0% |
| Joao Pedro Almeida | 17 | 10 | 58.8% | 9 | 52.9% | 0 | 0.0% |
| Ana Beatriz Santos | 17 | 9 | 52.9% | 9 | 52.9% | 0 | 0.0% |
| Roberto Nascimento | 17 | 11 | 64.7% | 9 | 52.9% | 0 | 0.0% |
| **Overall** | **87** | **53** | **60.9%** | **45** | **51.7%** | **0** | **0.0%** |

### 6.3 Analysis

**CogPIE vs. CUPP:** CogPIE achieves a 17.8% relative improvement over CUPP (60.9% vs. 51.7%). The advantage comes primarily from:
- Deeper semantic expansion (nicknames, abbreviations, accent stripping)
- More comprehensive pair combinations with case variant coverage
- Old password mutation (appending characters, symbol substitution)
- Leet substitution variants that simple CUPP rules miss

**CogPIE vs. Markov:** The pure Markov baseline achieves 0% hit rate because it lacks any profile information. This confirms that untargeted statistical approaches are fundamentally inadequate against targeted attacks when the attacker possesses personal information about the target.

**Candidate efficiency:** CogPIE generates approximately 110,000-130,000 candidates per profile, compared to CUPP's 100-130. While CogPIE has a lower candidate-to-hit ratio (approximately 1:10,000 vs. CUPP's 1:14), it discovers passwords that CUPP cannot generate at all: leet variants, complex pair combinations with multiple case patterns, and old password mutations.

**Execution performance:** CogPIE completes the full pipeline in 1.0-1.3 seconds per profile on commodity hardware, making it practical for real-time use in authorized penetration testing scenarios.

### 6.4 Limitations

1. **Synthetic evaluation:** Results are based on synthetic data designed to follow documented cognitive patterns. Real-world hit rates would depend on the accuracy and completeness of the target profile.

2. **Cultural specificity:** The current nickname database and accent handling are focused on Brazilian Portuguese names. Extending to other cultures would require additional linguistic resources.

3. **No trained model evaluation:** The benchmark uses CogPIE without a training corpus. Performance with a trained model on real corpus data would likely improve the ranking quality and enable better candidate prioritization within budget constraints.

4. **Candidate set size:** Without budget constraints, CogPIE generates 100,000+ candidates. In online attack scenarios with rate limiting, the ranking quality becomes critical for selecting the most promising candidates within a small guess budget.

## 7. Discussion

### 7.1 Implications for Password Security

Our results provide quantitative evidence for a well-known but often underappreciated conclusion: human-generated passwords are fundamentally insecure against targeted attacks. When an attacker possesses even basic personal information about a target (names, dates, interests), a systematic cognitive bias model can correctly predict over 60% of likely passwords.

This finding aligns with the broader literature:
- Wang et al. (2016) found 30% of modified passwords crackable within 10 guesses
- Cloudflare (2024) reported 41% of successful authentications involving leaked credentials
- Das et al. (2014) estimated 43-51% password reuse across sites
- A 2026 survey found 76.2% of users only make small modifications to existing passwords

### 7.2 Defense Recommendations

Based on our analysis, we recommend:

1. **Password managers with random generation:** The only reliable defense against CogPIE-class attacks. Cryptographically random passwords have no cognitive patterns to exploit.

2. **Multi-factor authentication:** Renders password guessing insufficient for account compromise, regardless of password strength.

3. **FIDO2/WebAuthn passkeys:** Eliminates passwords entirely, removing the cognitive vulnerability from the authentication chain.

4. **Breach credential screening:** As recommended by NIST SP 800-63B, checking new passwords against known leaked databases prevents the reuse of compromised credentials.

5. **Password policy modernization:** Moving from composition rules (which CogPIE easily satisfies) to minimum length requirements and breach checking (which address the actual vulnerability).

### 7.3 Ethical Considerations

CogPIE is designed for authorized security testing, specifically for penetration testers evaluating the strength of user-chosen passwords within the scope of authorized engagements. The algorithm's existence does not create new attack capabilities; rather, it systematizes techniques already known to sophisticated attackers and makes them available for defensive assessment.

We emphasize:
- All testing must be performed with explicit authorization
- Personal information used in profiles must be obtained through legitimate means within the engagement scope
- Results should be used to improve organizational password policies, not to compromise individual accounts
- The strongest defense remains eliminating human-chosen passwords entirely

### 7.4 Future Work

Several directions for future research emerge:

1. **Cross-cultural expansion:** Extending the semantic expansion layer to support additional languages, name conventions, and cultural password patterns.

2. **Temporal modeling:** Incorporating password evolution patterns (how users modify passwords over time) as documented by Wang et al. (2016).

3. **Active learning:** Using feedback from successful and unsuccessful guesses to dynamically adjust the model weights during an assessment.

4. **Neural network integration:** Replacing or augmenting the Markov/PCFG hybrid with transformer-based models fine-tuned on profile-specific patterns.

5. **Passphrase analysis:** Extending cognitive bias modeling to multi-word passphrases, which exhibit different but equally exploitable patterns.

## 8. Conclusion

We presented CogPIE, a 5-layer cognitive pattern inference engine for targeted password candidate generation. By explicitly modeling the psychological biases that drive human password creation, CogPIE achieves a 60.9% hit rate on synthetic benchmarks, outperforming CUPP-style profiling by 17.8% and demonstrating the fundamental inadequacy of pure statistical approaches in targeted scenarios.

Our formal mathematical framework provides convergence guarantees for the hybrid Markov/PCFG ranking system, while the practical implementation runs in under 2 seconds per profile on commodity hardware. The modular architecture enables extension to additional cultural contexts and integration with existing password auditing tools.

The central thesis of this work, that passwords generated "from the head" always resort to patterns derived from cognitive context, is supported by both our experimental results and the extensive body of prior literature. The measurable cognitive bias in password creation is not a failure of user education or policy design; it is a fundamental property of human cognition. Password managers with cryptographically random generation represent the only provably secure defense against this class of vulnerability.

## References

1. Abdrabou, Y., Riber, M., Steinert, A., et al. (2021). "Cognitive Load and Password Strength: A Pupillometry Study." In Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems.

2. Bonneau, J. (2012). "The Science of Guessing: Analyzing an Anonymized Corpus of 70 Million Passwords." In IEEE Symposium on Security and Privacy, pp. 538-552. DOI: 10.1109/SP.2012.49.

3. Bonneau, J. (2012). "Statistical Metrics for Individual Password Strength." In Security Protocols Workshop.

4. Cloudflare (2024). "Leaked Credentials in Authentication Traffic." Cloudflare Radar Report.

5. Das, A., Bonneau, J., Caesar, M., Borisov, N., and Wang, X. (2014). "The Tangled Web of Password Reuse." In Network and Distributed System Security Symposium (NDSS).

6. Durmuth, M., Angelstorf, F., Castelluccia, C., Perito, D., and Chaabane, A. (2015). "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." In Engineering Secure Software and Systems (ESSoS), LNCS 8978, pp. 119-132.

7. Florencio, D. and Herley, C. (2007). "A Large-Scale Study of Web Password Habits." In Proceedings of the 16th International Conference on World Wide Web (WWW '07).

8. Hitaj, B., Gasti, P., Ateniese, G., and Perez-Cruz, F. (2019). "PassGAN: A Deep Learning Approach for Password Guessing." In Applied Cryptography and Network Security (ACNS). arXiv:1709.00440.

9. Imperva (2010). "Consumer Password Worst Practices." Imperva Application Defense Center Report.

10. Katz, S. M. (1987). "Estimation of Probabilities from Sparse Data for the Language Model Component of a Speech Recognizer." IEEE Transactions on Acoustics, Speech, and Signal Processing, 35(3), pp. 400-401.

11. Li, Y., Wang, H., and Sun, K. (2017). "Personal Information in Passwords and Its Security Implications." IEEE Transactions on Information Forensics and Security, 12(10). DOI: 10.1109/TIFS.2017.2705627.

12. Ma, J., Yang, W., Luo, M., and Li, N. (2014). "A Study of Probabilistic Password Models." In IEEE Symposium on Security and Privacy, pp. 689-704.

13. Mebus, M. (2010). "CUPP: Common User Passwords Profiler." GitHub Repository.

14. Narayanan, A. and Shmatikov, V. (2005). "Fast Dictionary Attacks on Passwords Using Time-Space Tradeoff." In ACM Conference on Computer and Communications Security (CCS).

15. NIST (2017, revised 2024). "Digital Identity Guidelines: Authentication and Lifecycle Management." NIST Special Publication 800-63B.

16. Rando, J., Perez-Cruz, F., and Hitaj, B. (2023). "PassGPT: Password Modeling and (Guided) Generation with Large Language Models." In European Symposium on Research in Computer Security (ESORICS). arXiv:2306.01545.

17. Veras, R., Collins, C., and Thorpe, J. (2014). "On Semantic Patterns of Passwords and their Security Impact." In Network and Distributed System Security Symposium (NDSS).

18. Wang, D. and Jian, G. (2014). "Zipf's Law in Passwords." IACR ePrint Archive, 2014/631. Later published in IEEE TIFS, 2017.

19. Wang, D., Zhang, Z., Wang, P., Yan, J., and Huang, X. (2016). "Targeted Online Password Guessing: An Underestimated Threat." In ACM Conference on Computer and Communications Security (CCS).

20. Wang, D., Cheng, H., Wang, P., Huang, X., and Jian, G. (2016). "The Next Domino to Fall: Empirical Analysis of User Passwords across Online Services." In ACM Conference on Computer and Communications Security (CCS).

21. Weir, M., Aggarwal, S., de Medeiros, B., and Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." In IEEE Symposium on Security and Privacy, pp. 391-405. DOI: 10.1109/SP.2009.8.

22. Wheeler, D. L. (2016). "zxcvbn: Low-Budget Password Strength Estimation." In USENIX Security Symposium.

23. Xie, X. (2020). "Modified TarGuess-I: Keyboard Patterns and Popular Passwords as Password Guessing Threats." Master's Thesis.

24. Survey Authors (2026). "Examining User Behavior and Cognitive Biases in Personal Password Security." arXiv:2607.19586.

25. AI Password Study Authors (2026). "AI vs. User-Generated Passwords: Strength, Memorability, and Cognitive Bias." arXiv:2604.19410.

26. MDPI Entropy Review (2023). "A Systematic Review of Password Guessing Methods." MDPI Entropy.

27. Castelluccia, C. and Durmuth, M. (2012). "Adaptive Password-Strength Meters from Markov Models." In Network and Distributed System Security Symposium (NDSS).

28. Dell'Amico, M. and Filippone, M. (2015). "Monte Carlo Strength Evaluation: Fast and Reliable Password Checking." In ACM Conference on Computer and Communications Security (CCS).

29. Ur, B., Segreti, S. M., Bauer, L., et al. (2015). "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." In USENIX Security Symposium.

30. Kelley, P. G., Komanduri, S., Mazurek, M. L., et al. (2012). "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms." In IEEE Symposium on Security and Privacy.

31. Melicher, W., Ur, B., Segreti, S. M., et al. (2016). "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks." In USENIX Security Symposium.

32. Golla, M. and Durmuth, M. (2018). "On the Accuracy of Password Strength Meters." In ACM Conference on Computer and Communications Security (CCS).

33. Pal, B. and Chua, T. (2019). "A Comparison of Approaches to Large-Scale Data Analysis." In Pacific-Asia Conference on Knowledge Discovery and Data Mining.

34. Adams, A. and Sasse, M. A. (1999). "Users Are Not the Enemy." Communications of the ACM, 42(12), pp. 40-46.

35. Yan, J., Blackwell, A., Anderson, R., and Grant, A. (2004). "Password Memorability and Security: Empirical Results." IEEE Security & Privacy, 2(5), pp. 25-31.

36. Forget, A., Chiasson, S., van Oorschot, P. C., and Biddle, R. (2008). "Improving Text Passwords Through Persuasion." In Symposium on Usable Privacy and Security (SOUPS).

37. Shay, R., Komanduri, S., Kelley, P. G., et al. (2010). "Encountering Stronger Password Requirements: User Attitudes and Behaviors." In Symposium on Usable Privacy and Security (SOUPS).

38. Ur, B., Noma, F., Bees, J., et al. (2015). "'I Added '!' at the End to Make It Secure': Observing Password Creation in the Lab." In Symposium on Usable Privacy and Security (SOUPS).

39. Wash, R., Rader, E., Berman, R., and Wellmer, Z. (2016). "Understanding Password Choices: How Frequently Entered Passwords Are Re-used Across Websites." In Symposium on Usable Privacy and Security (SOUPS).

40. Oesch, S. and Ruoti, S. (2020). "That Was Then, This Is Now: A Security Evaluation of Password Generation, Storage, and Autofill in Browser-Based Password Managers." In USENIX Security Symposium.

41. Pasquini, D., Gangwal, A., Ateniese, G., Bernaschi, M., and Conti, M. (2021). "Improving Password Guessing via Representation Learning." In IEEE Symposium on Security and Privacy.

42. Pal, B., Daniel, T., Chatterjee, R., and Ristenpart, T. (2019). "Beyond Credential Stuffing: Password Similarity Models Using Neural Networks." In IEEE Symposium on Security and Privacy.

---

## Appendix A: Profile Schema

Complete JSON schema for CogPIE target profiles:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "names": {"type": "array", "items": {"type": "string"}},
        "dates": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "pets": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "items": {"type": "string"}},
        "phones": {"type": "array", "items": {"type": "string"}},
        "emails": {"type": "array", "items": {"type": "string"}},
        "old_passwords": {"type": "array", "items": {"type": "string"}},
        "numbers": {"type": "array", "items": {"type": "string"}}
    }
}
```

## Appendix B: Benchmark Methodology

All benchmarks were conducted using exclusively synthetic data:

1. Five synthetic target profiles were created with typical Brazilian personal information patterns.
2. For each profile, "ground truth" passwords were generated following documented cognitive creation patterns (first name + year, keyword + suffix, old password mutation, leet variant, etc.).
3. Three approaches were evaluated: CogPIE (full pipeline, no training corpus), CUPP baseline (simple concatenation), and Markov baseline (common password dictionary).
4. Hit rate is defined as |generated intersection ground_truth| / |ground_truth|.
5. No real breach data, personal information, or credentials were used.

## Appendix C: Cognitive Bias Summary Table

| Bias | Effect on Passwords | Prevalence | CogPIE Layer |
|------|-------------------|------------|-------------|
| Anchoring | Base word remains recognizable | >90% | Layer 1, 2 |
| Serial Position | Modifications at start/end | >85% (end) | Layer 2 |
| Familiarity | Personally meaningful tokens | >70% | Layer 1 |
| Minimal Effort | Smallest change to satisfy policy | >60% | Layer 2, 5 |
| Status Quo | Reuse with minor modification | ~76% | Layer 1 (old_pw) |
| Hyperbolic Discounting | Prioritize memorability over security | ~76% | All layers |
| Availability | Use recently encountered info | ~40% | Layer 1 |

---

*This research was conducted for authorized security testing and academic purposes. All experiments used synthetic data exclusively. The authors advocate for the adoption of password managers and passwordless authentication as the primary defense against targeted password attacks.*

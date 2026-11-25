# Knowledge graph

Papers: primary (10.0000/synthetic.demo.a), secondary (10.0000/synthetic.demo.b)

## Nodes (11)

| node_id | name | type | aliases | sources |
|-|-|-|-|-|
| N_0056131e04 | mesoporous TiO2 | material | TiO2; titanium dioxide (TiO2); titanium dioxide | primary: p1; secondary: s1 |
| N_03b8c9892b | perovskite solar cells | task |  | primary: p1; secondary: s1 |
| N_2bc78419ad | AM 1.5G illumination at 100 mW cm-2 | condition |  | primary: p2 |
| N_52204a1c2a | SnO2 | material |  | secondary: s1 |
| N_58c12ca383 | spin-coating | method |  | primary: p1; secondary: s3 |
| N_68568c6fe6 | power conversion efficiency (PCE) | metric | PCE | primary: p2; secondary: s2 |
| N_704ede7e33 | PCE of 21.1% (champion device, paper A) | value |  | primary: p2 |
| N_88b2753f0c | Chen et al. | researcher |  | primary: p3 |
| N_90dc13f5c1 | damp-heat ageing at 85 C and 85% relative humidity | condition |  | secondary: s1 |
| N_b6e43000d1 | PCE retention after 500 h: SnO2 92%, TiO2 74% (paper B) | value |  | secondary: s2 |
| N_f72da9bb16 | TiO2-based devices degrade under ultraviolet illumination | conclusion |  | primary: p3 |

## Edges (11)

| edge_id | subject | predicate | object | conditions | strength | evidence |
|-|-|-|-|-|-|-|
| R_c6bf6350e2 | perovskite solar cells | uses | mesoporous TiO2 | as electron transport layer | direct | primary:p1 "perovskite solar cells using a mesoporous TiO2 electron tran..." |
| R_4e77590cf5 | mesoporous TiO2 | uses | spin-coating | deposition of the mesoporous TiO2 layer | direct | primary:p1 "a mesoporous TiO2 electron transport layer deposited by spin..." |
| R_b303a1e6bd | perovskite solar cells | reports_value | PCE of 21.1% (champion device, paper A) | AM 1.5G illumination at 100 mW cm-2 | direct | primary:p2 "The champion device reaches a power conversion efficiency (P..." |
| R_e701e6f4ed | power conversion efficiency (PCE) | measures | perovskite solar cells | champion device | direct | primary:p2 "a power conversion efficiency (PCE) of 21.1%" |
| R_9bfa73cc6e | Chen et al. | supports | TiO2-based devices degrade under ultraviolet illumination | as cited by paper A; original study not included in this corpus | reported | primary:p3 "Chen et al. previously reported that TiO2-based devices degr..." |
| R_b29d098490 | perovskite solar cells | uses | mesoporous TiO2 | as electron transport layer, one arm of the comparison | direct | secondary:s1 "We compare titanium dioxide (TiO2) and SnO2 electron transpo..." |
| R_af89e5f115 | perovskite solar cells | uses | SnO2 | as electron transport layer, one arm of the comparison | direct | secondary:s1 "We compare titanium dioxide (TiO2) and SnO2 electron transpo..." |
| R_516f8d4912 | mesoporous TiO2 | compares_with | SnO2 | damp-heat ageing at 85 C and 85% relative humidity, 500 hours | direct | secondary:s1 "subjected to damp-heat ageing at 85 C and 85% relative humid..."; secondary:s2 "After 500 hours" |
| R_3a8d5c52a6 | SnO2 | outperforms | mesoporous TiO2 | PCE retention after 500 h damp-heat at 85 C / 85% RH (paper B devices only) | direct | secondary:s2 "the SnO2 devices retain 92% of their initial PCE, whereas th..." |
| R_12337e5f7c | perovskite solar cells | uses | spin-coating | all devices in paper B | direct | secondary:s3 "All devices in this study were prepared by spin-coating" |
| R_e4499dbe2f | power conversion efficiency (PCE) | measures | perovskite solar cells | retention of initial PCE after ageing | direct | secondary:s2 "retain 92% of their initial PCE" |

## Conflicts (kept, not resolved)

- Both are performance numbers involving PCE, but they come from different papers, different devices and different conditions (AM 1.5G initial efficiency vs damp-heat retention). They must NOT be merged into one conclusion. -> kept_separate
- Paper A (citing Chen et al.) reports UV-driven degradation of TiO2 devices; paper B reports damp-heat-driven degradation. Different stressors; neither confirms nor contradicts the other. -> kept_separate

## Uncertainties

- Paper A reports no stability data; paper B's retention results must not be extrapolated to paper A's devices.
- The degree sign in '85 C' (s1) was lost during text linearisation; verify against the publisher XML before reuse.
- Chen et al. (p3) cannot be merged with any researcher outside this corpus: no affiliation or given name is reported.

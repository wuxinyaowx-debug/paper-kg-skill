# Merge / conflict change log

- MERGE e_tio2_primary <- e_tio2_secondary (cross_paper=True, confidence=high): Same chemical concept: 'titanium dioxide (TiO2)' (paper B, s1) is the full name + abbreviation of 'TiO2' (paper A, p1). Concept-level merge only; the physical samples and device conditions differ between the papers and remain per-source in the node's evidence.
- MERGE e_psc_primary <- e_psc_secondary (cross_paper=True, confidence=high): Identical task phrase 'perovskite solar cells' in p1 and s1; device instances are NOT merged, only the task concept.
- MERGE e_pce_primary <- e_pce_secondary (cross_paper=True, confidence=high): 'PCE' (s2) is the abbreviation defined in p2 as 'power conversion efficiency (PCE)'. Metric concept merge; the measured values stay as separate per-paper value nodes.
- MERGE e_spincoating_primary <- e_spincoating_secondary (cross_paper=True, confidence=medium): Identical generic method term 'spin-coating' in p1 and s3. Merged as a method concept with medium confidence because paper B gives no deposition parameters; this merge does NOT imply identical coating conditions.

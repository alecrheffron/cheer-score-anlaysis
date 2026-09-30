# All-Star Cheer Scoring Analysis

A coaching-focused analysis of 2025–26 competition scores: which scoring categories distinguish competitive performances, what strong score profiles look like, and how deductions and round-to-round changes relate to results.

## Project Overview

This project combines cheerleading domain knowledge with Python analysis to turn published score breakdowns into practical reference points for coaches.

The analysis covers 31,151 performances across 160 competitions, 4,408 team IDs, and 294 division IDs. Levels 1, 2, 3, 4, 4.2, 5, and 6 are included.

The primary unit is one team's performance within a competition, level, division, and round. Individual-round scores and published placement are analyzed separately because competition formats and cumulative scoring rules vary.

**Interactive Tableau dashboard:** planned. Benchmark datasets have been exported for dashboard development.

## Questions Examined

- Which scoring categories consistently distinguish competitive placements?
- How do recorded first-place rates vary as teams meet more score benchmarks?
- How do those patterns differ by level and competitive field size?
- Which scoring categories tend to move together?
- How are deductions associated with outcomes and hypothetical score-based position?
- How do the same team's scores change between rounds?
- Do changes in awarded pyramid difficulty coincide with changes in execution and deductions?

## Data and Scoring Context

The source data comes from publicly available Varsity TV competition results and PDF score breakdowns.

Two scorecard formats appear in the dataset:

| Format | Maximum raw score | Performances |
|---|---:|---:|
| Standard scorecard | 50 | 23,232 |
| No-toss scorecard | 46 | 7,919 |

Raw scores from different formats are not directly comparable. Benchmark thresholds are calculated separately by level and scorecard format.

Many difficulty categories show limited variation within a level. The analysis therefore examines score distributions before interpreting category relationships. Zero recorded deductions also do not prove that every intended skill was completed.

Placement analyses generally use fields of at least three teams. This leaves 21,980 eligible performances.

## Findings

### 1. Meeting More Score Benchmarks Is Associated With More First-Place Finishes

### 1. Meeting More Score Benchmarks Is Associated With More First-Place Finishes

Benchmarks were calculated at the 75th and 90th percentiles of training performances, separately by level and scorecard format. Their relationships with first-place finishes were evaluated on other competitions.

#### Level 3 Benchmark Targets — 50-Point Scorecard

| Category | 75th-percentile target | 90th-percentile target |
|---|---:|---:|
| Stunt execution | 3.90 | 3.90 |
| Pyramid execution | 3.90 | 3.90 |
| Standing tumbling execution | 3.90 | 4.00 |
| Running tumbling execution | 3.90 | 4.00 |
| Show | 1.83 | 1.87 |
| Routine composition | 1.83 | 1.90 |

A performance meets a benchmark when its category score is at or above the target. These are reference scores, not minimum requirements for winning. Scores occur in discrete increments, so the 75th and 90th percentiles can produce identical targets.

![Benchmark attainment across levels](reports/figures/benchmark_attainment_by_level.png)

Within fields of three to seven teams, observed first-place rates increased across the groups meeting 0–2, 3–4, and 5–6 benchmarks for every main level/scorecard group shown.

These targets describe strong recorded score profiles. They are not minimum scores required to win, causal effects, or individual win probabilities.

#### Level 3 Detail

![Level 3 benchmarks by field size](reports/figures/level3_benchmarks_by_field_size.png)

For the 75th-percentile targets:

| Benchmarks met | 3–4 team fields | 5–7 team fields |
|---:|---:|---:|
| 0 | 9.3% (75 performances) | 1.5% (66) |
| 1 | 12.8% (78) | 3.6% (56) |
| 2 | 19.8% (101) | 9.1% (55) |
| 3 | 34.5% (84) | 17.0% (47) |
| 4 | 41.7% (60) | 20.5% (44) |
| 5 | 55.6% (54) | 34.1% (41) |
| 6 | 61.5% (39) | 73.1% (26) |

The progression persisted after excluding the event contributing the most Level 3 performances in large fields.

Results for fields of eight or more teams require greater caution: one competition contributed 284 of 372 evaluation performances in that band. High-benchmark rates there were heavily concentrated in that event.

The 90th-percentile targets identify more selective groups, but some have very few performances or competitions.

### 2. Stunt Execution Shows Consistent Relationships With Placement Across Levels

![Category consistency across levels](reports/figures/category_consistency_across_levels.png)

Stunt execution appeared among the five most negative average conditional placement coefficients at all seven levels. Pyramid difficulty appeared at six levels.

The chart measures how consistently categories appeared among the strongest conditional relationships. It does not measure how much a team's placement would improve after increasing a particular score.

### 3. Related Categories Often Move Together

![Level 3 category correlations](reports/figures/level3_category_correlations.png)

Among eligible Level 3 zero-deduction performances, the strongest category-pair Spearman correlations were:

| Category pair | Correlation |
|---|---:|
| Routine composition ↔ Show | 0.71 |
| Pyramid difficulty ↔ Routine composition | 0.59 |
| Standing tumbling execution ↔ Running tumbling execution | 0.55 |
| Stunt execution ↔ Pyramid execution | 0.54 |
| Pyramid difficulty ↔ Show | 0.50 |

These associations help explain why categories can share information in multivariable models. They do not establish that improving one category causes another to improve, or that judges intentionally link the categories.

### 4. Larger Deductions Are Associated With Fewer First-Place Finishes

![Deductions and first-place rates](reports/figures/deductions_and_first_place_rates.png)

Among performances in fields of at least three teams:

- 26.6% of deduction-free performances had recorded rank 1.
- 15.7% of performances with 0.01–0.25 deductions had recorded rank 1.
- Approximately 8.3% with 0.26–0.75 deductions had recorded rank 1.
- 0.8% with more than 1.50 deductions had recorded rank 1.

These comparisons involve different performances. A mistake may affect category scores as well as deductions, so the figures do not isolate the causal effect of a penalty.

Teams can still finish first with deductions: of 882 recorded first-place performances with deductions, 586 competed against at least one deduction-free opponent.

#### Deduction-Only Score Comparison

![Hypothetical deduction-only position impact](reports/figures/deduction_only_position_impact.png)

Among 9,853 performances with deductions, removing only a team's own deductions while holding opponents' scores constant would allow:

- 37.6% to pass at least one opponent.
- Another 2.2% to reach a tie without passing an opponent.

This is a hypothetical comparison of individual-round scores. It does not recalculate official competition placements or restore difficulty and execution points potentially lost through the same mistake.

### 5. Small Category Differences Separate the Top Round Scores

![Top-two round-score category gaps](reports/figures/top_two_round_score_category_gaps.png)

Across 3,988 fields with distinct top-two individual-round scores, the median score margin was 0.717 points.

The largest average raw category-point gaps included stunt execution, pyramid difficulty, pyramid execution, and running tumbling execution. Standing and running tumbling difficulty showed virtually no average gap.

Raw category gaps describe score differences, rather than normalized importance or causal impact. This comparison uses individual-round scores, not published first and second place or cumulative event scores.

### 6. Most Matched Teams Scored Higher in Finals

![Prelims-to-Finals score changes](reports/figures/prelims_to_finals_score_changes.png)

Among 4,665 matched team–competition–division pairs with one Prelims and one Finals performance:

- 70.4% scored higher in Finals.
- The average individual-round score increased by 0.621 points.
- Pre-deduction scores increased by an average of 0.549 points.
- Deductions decreased by an average of 0.071 points.

Only 34.6% had fewer deductions in Finals. Teams with unchanged deductions still had a median round-score increase of 0.507 points.

The observed improvement therefore involved changes in awarded scores as well as penalties. The data cannot establish whether routine changes, performance improvements, judging differences, or other factors caused those changes.

### 7. Awarded Pyramid Difficulty Can Change Alongside Execution and Deductions

![Pyramid difficulty, execution, and deductions](reports/figures/pyramid_difficulty_execution_deductions.png)

Among 217 Level 3 matched team–competition–division pairs whose awarded pyramid difficulty changed between two rounds:

- The higher-difficulty round had higher pyramid execution in 68.7% of cases.
- It had fewer routine-wide deductions in 82.0% of cases.
- The pairs came from 51 competitions.

After excluding the three most represented competitions, the pattern persisted among 160 pairs across 48 competitions: 65.6% had higher pyramid execution and 80.6% had fewer deductions in the higher-difficulty round.

Awarded difficulty describes the recorded performance, not necessarily the routine a team intended to perform. Scorecards alone cannot identify an omitted sequence, an intentional routine change, or the source of a deduction.

## Analytical Approach

The analysis includes:

- Score-distribution and observed-ceiling checks by level.
- Zero-deduction comparisons to examine categories separately from recorded penalties.
- Spearman correlations and category-gap comparisons.
- Within-field standardized predictors and Ridge regression.
- Nested competition-held-out validation and coefficient stability checks.
- Separate deduction and field-size interaction models.
- Percentile benchmarks derived from training competitions.
- Event-coverage and dominant-event sensitivity checks.
- Same-team comparisons within competition and division across rounds.

Category-based models achieved mean held-out R² of approximately 0.57–0.64 for Levels 1–4. Performance was lower and more variable at higher levels, particularly Level 6.

Because placement is derived from scoring, these models describe how recorded category scores distinguish outcomes within the scoring system. Predictive accuracy alone does not establish which coaching intervention would improve a team's results.

Earlier benchmark exploration examined the full dataset. Subsequent competition-split checks provide evidence of robustness, but should not be presented as fully independent prospective validation.

## Limitations

- Published rank can reflect competition-specific formats and may include ties.
- Performances are repeated observations of teams and competitions, not independent teams.
- Score-sheet formats and category applicability differ.
- Some difficulty categories have little variation.
- Zero deductions do not guarantee completion of every intended skill.
- Scores do not capture routine intent, video evidence, judge reasoning, or the cause of each penalty.
- Small or event-concentrated benchmark groups limit generalization.
- Field size affects first-place rates; pooled rates can also reflect differences in field composition.
- Category correlations may reflect shared performance quality and competition context.
- Regional scoring differences and individual judge behavior are not established by this analysis.

## Repository Workflow

| Notebook | Purpose |
|---|---|
| `notebooks/01_scoring_eda.ipynb` | Exploration, modeling, validation, and analytical exports |
| `notebooks/02_findings_visuals.ipynb` | Findings narrative and static figure exports |

The main analytical input is:

`data/processed/season_2026_all_levels_performances.csv`

Run `01` before `02` to generate the derived inputs used by the findings notebook.

### Dashboard Exports

- `tableau_benchmark_performances.csv`: 6,643 evaluation performances with level-specific 75th/90th-percentile benchmark counts.
- `tableau_benchmark_thresholds.csv`: category thresholds by level, scorecard format, and percentile.
- `category_pair_correlations.csv`: category-pair correlation results by level.
- `prelims_finals_changes.csv`: matched Prelims-to-Finals score changes.
- `pyramid_round_changes.csv`: matched Level 3 changes in awarded pyramid difficulty.

Static figures are saved under `reports/figures/`.

## Tools

Python, pandas, NumPy, scikit-learn, statsmodels, and Matplotlib.

Tableau will provide interactive exploration of the validated exports.

## Author

Alec Heffron — cheerleading program director and coach transitioning into data analytics.
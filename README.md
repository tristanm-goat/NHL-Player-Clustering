# NHL Player Clustering

NHL men's advanced stats player clustering and archetype identification project.

Inspired by and adapted from [cmarkey/Player-Clustering](https://github.com/cmarkey/Player-Clustering) (Women's Hockey Player Archetypes by Carleen Markey & Nayan Patel).

## Overview

This project applies unsupervised machine learning (PCA + K-Means clustering) to NHL men's advanced statistics from the **2018-19 through 2025-26 seasons** (regular season and playoffs) to identify player archetypes and quantify player value based on their archetype and dependency profile.

## Data Sources

- **Natural Stat Trick** (naturalstattrick.com) — 5v5 advanced stats: Corsi For%, Fenwick For%, Expected Goals For%, individual Corsi, Fenwick, scoring chances, high-danger chances, zone entries/exits, and more.
- **Money Puck** (moneypuck.com) — supplementary xG and shot quality metrics.
- **NHL API** (api-web.nhle.com) — player biographical data, team rosters, games played, positions.

Seasons covered: 2018-19, 2019-20, 2020-21 (bubble), 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 (regular season + playoffs).

## Metrics Used (per 60 minutes at 5v5)

| Index | Description |
|---|---|
| Corsi Index | On-ice shot attempt share (CF%) relative to peers |
| Fenwick Index | On-ice unblocked shot attempt share (FF%) |
| xG Index | Expected goals for share (xGF%) at 5v5 |
| Scoring Chance Index | On-ice scoring chance share |
| High Danger Index | High-danger shot attempt share |
| Individual Shot Index | Individual shots on goal per 60 |
| Individual xG Index | Individual expected goals per 60 |
| Zone Entry Index | Controlled zone entry rate per 60 |
| Zone Exit Index | Successful zone exit rate per 60 |
| Primary Points Index | Primary points (G + A1) per 60 |
| Takeaway Index | Net takeaway rate per 60 |

## Pipeline

Files are run in the following order:

1. `data_collection.py` — Fetches and merges raw NHL advanced stats for all seasons (2018-19 to 2025-26, regular season + playoffs) from Natural Stat Trick, NHL API, and MoneyPuck.
2. `metric_calculation.py` — Computes per-60 indices, normalizes by position and TOI minimums, and produces forward/defenseman summary CSVs.
3. `pca.py` — Performs Principal Component Analysis on the computed indices to reduce dimensionality for clustering.
4. `kmeanspca.py` — Applies K-Means clustering on PCA-transformed data to identify player archetypes.
5. `player_valuation.py` — Computes Player Value Scores (PVS) based on archetype classification, dependency analysis, and performance relative to cluster centroids.

## Player Archetypes

### Forwards
- **Driver** — high Corsi/xG/HDCF, leads possession and shot generation
- **Shooter** — high individual shot and xG output, finisher profile
- **Playmaker** — high primary assist and zone entry rates, sets up teammates
- **Balanced** — above-average across multiple categories
- **Dependent** — below-average possession, relies on linemates for production

### Defensemen
- **Two-Way** — strong in both offensive and defensive metrics
- **Offensive** — high xG, zone entry, and primary point rates
- **Defensive/Shutdown** — suppresses opponent shots and xG, limited offense

## Player Valuation (Dependency-Based)

The valuation model assigns a value score to each player based on:

1. **Archetype cluster** — role and expected contribution level
2. **Dependency score** — how much the player's metrics degrade without high-end linemates (on-ice vs. individual stat splits)
3. **Relative performance** — distance from cluster centroid (players closer to Driver/Shooter centroids at high TOI are valued higher)
4. **Positional scarcity** — adjustments based on how rare each archetype is league-wide

This produces a single comparable **Player Value Score (PVS)** for all skaters.

## Output Files

| File | Description |
|---|---|
| `Data/forward_summary.csv` | Raw per-60 stats for all forwards |
| `Data/dman_summary.csv` | Raw per-60 stats for all defensemen |
| `Data/f_clustering_metrics.csv` | Normalized indices for forwards |
| `Data/d_clustering_metrics.csv` | Normalized indices for defensemen |
| `Data/f_transformed_metrics.csv` | PCA-transformed data for forwards |
| `Data/d_transformed_metrics.csv` | PCA-transformed data for defensemen |
| `Data/kmeanspca_results_f.csv` | Final cluster assignments + PVS for forwards |
| `Data/kmeanspca_results_d.csv` | Final cluster assignments + PVS for defensemen |

## Requirements

```
pandas>=1.3
numpy>=1.21
scikit-learn>=1.0
matplotlib>=3.4
requests>=2.26
kneed>=0.7
beautifulsoup4>=4.10
```

Install with:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python data_collection.py
python metric_calculation.py
python pca.py
python kmeanspca.py
python player_valuation.py
```

## Credits

Methodology adapted from:
- Carleen Markey & Nayan Patel, *Identifying Player Archetypes in Women's Hockey* (2021) — [cmarkey/Player-Clustering](https://github.com/cmarkey/Player-Clustering)

## License

GNU General Public License v3.0

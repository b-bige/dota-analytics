# Dota 2 Analytics Platform

> An analytics engine for professional Dota 2, combining OpenSkill player ratings with an ensembled LightGBM prediction engine and SHAP-interpreted draft analysis.
> **[Live Demo](https://dotaanalytics.duckdns.org)**
<img width="1897" height="912" alt="image" src="https://github.com/user-attachments/assets/734032f6-652d-45fa-aaf7-9f44e2de6cee" />

---

### 📊 Performance Highlights
* **204k+** matches processed & **73k+** players rated.
* **Production LightGBM Engine** outperforming baseline logistic regression on unseen data.
* **Real-Time Probability Bars** driven by live draft strength and skill differential extraction.

---

### 🛠️ Core Engine
* **ML Pipeline:** Transitioned from baseline Logistic Regression to an ensembled **LightGBM** architecture, optimized for high-dimensional, non-linear interactions between hero synergies and player skill.
* **Model Interpretation:** Leverages **SHAP (SHapley Additive exPlanations)** log-odds to mathematically isolate draft strength variables from team skill differentials, delivering multi-dimensional predictive metrics in real-time.
* **Live Monitor:** `systemd` service executing high-frequency polling against **Valve's Official Steam Web API**, utilizing exponential backoff 
* **Rating System:** **OpenSkill (PlackettLuce)** model tracking global player skill progression.

---

### 🧠 Architecture & Data Integrity
* **Uncertainty Quantification:** Engineered a custom mathematical confidence metric by synthesizing live model win probabilities with OpenSkill uncertainty parameters (σ), adjusting predictive certainty dynamically based on data freshness and account calibration.
* **Data Contracts & Feature Engineering:** Implemented a decoupled, configuration-driven feature extraction pipeline (`features.json`) using Pandas. Ensures strict feature-ordering compliance and prevents runtime shape mismatches between the live monitor and the model binary.
* **Point-in-Time Simulation:** Enforces a strict *Snapshot-then-Update* loop during training data generation. Features for match `N` are computed using exclusively historical context from matches `1` to `N-1`, ensuring zero look-ahead bias or data leakage.
* **In-Memory Streaming:** Migrated high-overhead `O(N^2)` hero synergy and counter matrix calculations from database window functions to native Python streaming dictionaries (`defaultdict`), massively reducing server disk I/O.
* **Hierarchical Cold-Start Handling:** Implemented patch-aware state managers using Bayesian smoothing. The engine dynamically blends current patch data, previous patch data, and global priors to gracefully handle meta shifts on day one of new game updates.

---

### 🚀 Tech Stack
| Layer | Technology |
|---|---|
| **Frontend** | Plotly Dash, Dash Mantine Components (Custom Flexbox UI) |
| **Backend** | Python, SQLAlchemy, httpx, Tenacity |
| **Database** | PostgreSQL (Docker), DiskCache |
| **ML / Math** | LightGBM, SHAP, Scikit-learn, OpenSkill, NumPy, Pandas |
| **DevOps** | Linux (Nginx/Gunicorn), systemd, uv |
| **Integration** | Valve Steam Web API |

---

### Data Sources & Acknowledgments
* **Live Data:** Real-time match statistics provided by Valve's Official [Steam Web API](https://steamcommunity.com/dev).
* **Detailed Match Data:** Detailed match data provided by [STRATZ API](https://stratz.com) and [OpenDota API](https://www.opendota.com).
* **Historical Dataset:** A collection of historical match metadata was derived from https://doi.org/10.34740/kaggle/ds/2832370
* **Asset Imagery:** All hero and item icons are property of Valve Corporation.

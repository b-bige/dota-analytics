# Dota 2 Analytics Platform

> An analytics engine for professional Dota 2, combining PlackettLuce player ratings with real-time draft evaluation.
> **[Live Demo](https://dotaanalytics.duckdns.org)**
<img width="1897" height="912" alt="image" src="https://github.com/user-attachments/assets/734032f6-652d-45fa-aaf7-9f44e2de6cee" />

---

### 📊 Performance Highlights
* **204k+** matches processed
* **73k+** players rated
* **71%** prediction accuracy on unseen data

---

### 🛠️ Core Engine
* **Rating System:** **OpenSkill (PlackettLuce)** model. 
* **Draft Logic:** Scores synergy, counters, and hero win rates.
* **ML Pipeline:** Logistic regression model using draft and player skill differential.
* **Live Monitor:** `systemd` service polling OpenDota every 3 mins with exponential backoff and persistent **DiskCache** for cross-process state.

---

### 🚀 Tech Stack
| Layer | Technology |
|---|---|
| **Frontend** | Plotly Dash, Dash Mantine Components |
| **Backend** | Python, SQLAlchemy, httpx, Tenacity |
| **Database** | PostgreSQL (Docker), DiskCache |
| **ML/Math** | Scikit-learn, OpenSkill, NumPy, Pandas |
| **DevOps** | Linux (Nginx/Gunicorn), systemd, uv |

---

### Data Sources & Acknowledgments
* **Live Data:** Real-time match statistics provided by the [OpenDota API](https://www.opendota.com).
* **Detailed Match Data:** Detailed match data provided by the [STRATZ API](https://stratz.com).
* **Historical Dataset:** A collection of historical match metadata was derived from https://doi.org/10.34740/kaggle/ds/2832370
* **Asset Imagery:** All hero and item icons are property of Valve Corporation.

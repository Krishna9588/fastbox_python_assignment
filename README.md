# FastBox Delivery System

Note: Assignment Round.
```
Name: Krishna Birla
Email: krishnabirla336@gmail.com
Contact: +91 9588620228
```

A Python logistics simulator for the company **FastBox**, built as part of the Nexgensis Technologies Python Developer assignment.

### Project Structure

```
fastbox_delivery/
├── delivery_system.py            # Main script
├── delivery_system_test_cases.py # Script with test_cases support
├── base_case.json                # Default input
├── README.md
├── Python Assignment(Delivery System).pdf
├── requirement.txt
└── test_cases/                   # 10 provided test cases
|   ├── test_case_1.json
|   └── ...
└── output_base_case/             # Output for base_case.json
|   ├── report.json
|   └── top_performer.csv
└── output_test_case/             # Output for test_cases (delivery_system_test_cases.py)
    └── test_case_1/
        ├── report.json
        └── top_performer.csv
```
---
#### Requirements

- Python 3.10 or higher
- No external libraries — uses the standard library only (`json`, `math`, `csv`, `random`)
- *Pre-requisites*:
    ```bash
    pip install -r requirement.txt  
    ```
---
### How to Run

1. Make sure your input data is in `data.json` (or update `INPUT_FILE` in the config section).
2. Open a terminal in the project folder.
3. Run:

```bash
python delivery_system.py
```

The script reads `data.json`, runs the simulation, and produces:
- A printed summary in the terminal
- `report.json` — full per-agent results
- `top_performer.csv` — best agent exported to CSV
- ASCII route maps printed in the terminal


#### Run with all test case files from test_cases/ folder
```bash
python delivery_system_test_cases.py
```
---

### Configuration

All settings are at the top of `delivery_system.py` under the **Configuration** section.  
Edit these variables directly — no command-line arguments needed.

| Variable          | Default          | Description                                              |
|-------------------|------------------|----------------------------------------------------------|
| `INPUT_FILE`      | `"data.json"`    | Path to the input JSON file                              |
| `OUTPUT_FILE`     | `"report.json"`  | Path to save the output report                           |
| `CSV_FILE`        | `"top_performer.csv"` | Path to save the top performer CSV                  |
| `DELAY_CHANCE`    | `0.30`           | Probability of a delay per delivery leg (0.0 to 1.0)    |
| `DELAY_MIN`       | `1`              | Minimum delay in minutes                                 |
| `DELAY_MAX`       | `10`             | Maximum delay in minutes                                 |
| `ENABLE_NEW_AGENT`| `False`          | Set to `True` to activate mid-day agent joining          |
| `NEW_AGENT_ID`    | `"A_NEW"`        | ID for the new agent                                     |
| `NEW_AGENT_POS`   | `[45, 45]`       | Starting position of the new agent                       |

**Example — to use a different test case:**

```python
INPUT_FILE = "../test_cases/test_case_3.json"
```

**Example — to enable the new agent:**
```python
ENABLE_NEW_AGENT = True
NEW_AGENT_ID     = "A_NEW"
NEW_AGENT_POS    = [50, 50]
```

**Example — to disable delays:**
```python
DELAY_CHANCE = 0.0
```
---

### Input Format

The simulator accepts **two JSON formats** (both are supported automatically):

**Format A – dict (used by test cases):**
```json
{
  "warehouses": {"W1": [0, 0], "W2": [50, 75]},
  "agents":     {"A1": [5, 5], "A2": [60, 60]},
  "packages":   [{"id": "P1", "warehouse": "W1", "destination": [30, 40]}]
}
```

**Format B – list (base_case.json):**
```json
{
  "warehouses": [{"id": "W1", "location": [0, 0]}],
  "agents":     [{"id": "A1", "location": [5, 5]}],
  "packages":   [{"id": "P1", "warehouse_id": "W1", "destination": [30, 40]}]
}
```
---
### Output

**Console:** summary table with per agent stats and the best agent. - **report.json:**

```json
{
  "A1": {
    "packages_delivered": 2,
    "packages": ["P1", "P4"],
    "total_distance": 93.13,
    "efficiency": 46.56,
    "total_delay_minutes": 5
  },
  "A3": {
    "packages_delivered": 1,
    "packages": ["P3"],
    "total_distance": 14.14,
    "efficiency": 14.14,
    "total_delay_minutes": 0
  },
  "best_agent": "A3"
}
```
**efficiency** = total_distance ÷ packages_delivered. (Lower is better).

**top_performer.csv:** best agent's stats in CSV format (bonus feature).

**ASCII map:** visualisation of warehouse/agent/destination positions.

---
### Bonus Features Implemented

- **ASCII route visualisation** – printed to console after each run.
- **CSV export of top performer** – saved to `top_performer.csv`.
- **Dual JSON format support** – handles both assignment formats seamlessly.
- **Random delivery delays** – Controlled by `DELAY_CHANCE`, `DELAY_MIN`, `DELAY_MAX` in config.
- **New agent joining mid day** – Set `ENABLE_NEW_AGENT = True` and configure `NEW_AGENT_ID` / `NEW_AGENT_POS`.
---

### Assumptions & Design Decisions

1. Each package is assigned to the nearest agent by Euclidean distance from agent to warehouse.
2. An agent groups packages by warehouse — one warehouse trip collects all packages from that location.
3. Agents with zero deliveries are excluded from the best-agent calculation.
4. Mid day join: the new agent only takes packages from a 2nd+ warehouse stop if it is closer to that warehouse than the original agent's mid-day position. This prevents pointless reassignments.
5. Distances are rounded to 2 decimal places.
---
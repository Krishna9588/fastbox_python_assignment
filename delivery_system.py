"""
FastBox Delivery System Simulator
==================================
Simulates one day of operations for the fictional logistics company FastBox.

Bonus features included:
  1. Export top performer to CSV
  2. Random delivery delays
  3. Visualize routes in ASCII
  4. Handle new agent joining mid-day

Assumptions:
  - Input JSON supports two formats (dict-style and list-style); both are handled.
  - Each package is assigned to the nearest agent by Euclidean distance (agent → warehouse).
  - An agent visits each warehouse once, picks up all packages there, then delivers each.
  - Efficiency = total_distance / packages_delivered (lower is better).
  - Delay: each delivery leg has a DELAY_CHANCE probability of a 1–10 min delay.
  - Mid-day join: new agent takes over packages from the 2nd warehouse stop onward
    of each original agent, but only if the new agent is closer to that warehouse.
"""

import json
import math
import csv
import random
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration  —  edit these to change behaviour
# ---------------------------------------------------------------------------
OUTPUT_DIR  = "output_base_case"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

INPUT_FILE   = f"base_case.json"  # path to input JSON
OUTPUT_FILE  = f"{OUTPUT_DIR}/report.json"     # path to output report
CSV_FILE     = f"{OUTPUT_DIR}/top_performer.csv"

DELAY_CHANCE = 0.30              # probability of a delay on each delivery leg (0.0–1.0)
DELAY_MIN    = 1                 # minimum delay in minutes
DELAY_MAX    = 10                # maximum delay in minutes

# New agent joining mid day.
# Set ENABLE_NEW_AGENT = True and fill in the details below to activate.
ENABLE_NEW_AGENT = False
NEW_AGENT_ID     = "A_NEW"
NEW_AGENT_POS    = [45, 45]      # starting position of the new agent


# ---------------------------------------------------------------------------
# Distance utility
# ---------------------------------------------------------------------------

def euclidean(p1: list, p2: list) -> float:
    """Return Euclidean distance between two 2-D points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# ---------------------------------------------------------------------------
# Input normalisation — handles both JSON formats
# ---------------------------------------------------------------------------

def normalise_input(data: dict) -> tuple[dict, dict, list]:
    """
    Accepts both input formats and returns:
      warehouses -> {id: [x, y]}
      agents     -> {id: [x, y]}
      packages   -> [{"id": str, "warehouse_id": str, "destination": [x, y]}]
    """
    raw_wh = data["warehouses"]
    if isinstance(raw_wh, dict):
        warehouses = {k: list(v) for k, v in raw_wh.items()}
    else:
        warehouses = {w["id"]: list(w["location"]) for w in raw_wh}

    raw_ag = data["agents"]
    if isinstance(raw_ag, dict):
        agents = {k: list(v) for k, v in raw_ag.items()}
    else:
        agents = {a["id"]: list(a["location"]) for a in raw_ag}

    packages = []
    for p in data["packages"]:
        wh_key = p.get("warehouse_id") or p.get("warehouse")
        packages.append({
            "id": p["id"],
            "warehouse_id": wh_key,
            "destination": list(p["destination"]),
        })

    return warehouses, agents, packages


# ---------------------------------------------------------------------------
# Package assignment
# ---------------------------------------------------------------------------

def assign_packages(warehouses: dict, agents: dict, packages: list) -> dict:
    """
    Assign each package to the nearest agent (agent position → warehouse).
    Returns: {agent_id: [package, ...]}
    """
    agent_ids = list(agents.keys())
    assignment = {aid: [] for aid in agent_ids}

    for pkg in packages:
        wh_loc  = warehouses[pkg["warehouse_id"]]
        nearest = min(agent_ids, key=lambda aid: euclidean(agents[aid], wh_loc))
        assignment[nearest].append(pkg)

    return assignment


# ---------------------------------------------------------------------------
# Bonus 4 — New agent joining mid-day
# ---------------------------------------------------------------------------

def join_agent(new_id: str, new_pos: list,
               agents: dict, assignment: dict,
               warehouses: dict) -> tuple[dict, dict]:
    """
    Add a new agent mid-day and reassign eligible packages.

    Packages from the 2nd warehouse stop onward of each original agent are
    candidates. The new agent only takes a package if it is closer to that
    warehouse than the original agent's mid-day position (after their 1st stop).
    """
    print(f"\n[MID-DAY] Agent {new_id} joined at position {new_pos}.")

    agents = dict(agents)
    agents[new_id] = list(new_pos)
    assignment = {k: list(v) for k, v in assignment.items()}
    assignment[new_id] = []

    for aid in list(assignment.keys()):
        if aid == new_id or len(assignment[aid]) <= 1:
            continue

        keep      = assignment[aid][:1]
        candidates = assignment[aid][1:]

        # Original agent's approximate mid-day position: their first warehouse
        midday_pos = warehouses[keep[0]["warehouse_id"]]

        stay    = []
        handoff = []
        for pkg in candidates:
            wh_loc = warehouses[pkg["warehouse_id"]]
            if euclidean(new_pos, wh_loc) < euclidean(midday_pos, wh_loc):
                handoff.append(pkg)
                print(f"  Package {pkg['id']} reassigned from {aid} to {new_id}.")
            else:
                stay.append(pkg)

        assignment[aid]    = keep + stay
        assignment[new_id].extend(handoff)

    if not assignment[new_id]:
        print(f"  No packages reassigned — {new_id} stands by.")

    return agents, assignment


# ---------------------------------------------------------------------------
# Bonus 2 — Random delivery delay
# ---------------------------------------------------------------------------

def maybe_delay() -> int:
    """Return a random delay in minutes with probability DELAY_CHANCE, else 0."""
    if random.random() < DELAY_CHANCE:
        return random.randint(DELAY_MIN, DELAY_MAX)
    return 0


# ---------------------------------------------------------------------------
# Agent simulation
# ---------------------------------------------------------------------------

def simulate_agent(agent_id: str, start: list, packages: list,
                   warehouses: dict) -> tuple[float, list, list, int]:
    """
    Simulate one agent's delivery route.

    Returns:
      total_distance   : float
      delivered_ids    : [package_id, ...]
      waypoints        : [(symbol, [x, y]), ...]  — used for ASCII maps
      total_delay_mins : int
    """
    if not packages:
        return 0.0, [], [("S", list(start))], 0

    total_distance = 0.0
    total_delay    = 0
    delivered_ids  = []
    position       = list(start)
    waypoints      = [("S", list(start))]

    # Group packages by warehouse, preserving input order
    warehouse_groups: dict[str, list] = {}
    for pkg in packages:
        warehouse_groups.setdefault(pkg["warehouse_id"], []).append(pkg)

    for wid, pkgs in warehouse_groups.items():
        wh_loc = warehouses[wid]

        total_distance += euclidean(position, wh_loc)
        position = list(wh_loc)
        waypoints.append(("W", list(wh_loc)))

        for pkg in pkgs:
            total_distance += euclidean(position, pkg["destination"])
            position = list(pkg["destination"])

            # Bonus 2: random delay
            delay = maybe_delay()
            if delay:
                total_delay += delay
                print(f"  [DELAY] Agent {agent_id} — package {pkg['id']} "
                      f"delayed {delay} min at {pkg['destination']}")

            delivered_ids.append(pkg["id"])
            waypoints.append(("D", list(pkg["destination"])))

    return total_distance, delivered_ids, waypoints, total_delay


# ---------------------------------------------------------------------------
# Bonus 3 — ASCII visualisation
# ---------------------------------------------------------------------------

def _to_grid(x, y, max_x, max_y, size):
    gx = round(x / max_x * (size - 1)) if max_x else 0
    gy = round(y / max_y * (size - 1)) if max_y else 0
    return max(0, min(gx, size - 1)), max(0, min(gy, size - 1))


def ascii_route_map(agent_id: str, waypoints: list,
                    all_coords: list, size: int = 22) -> str:
    """Per-agent route map: S=Start  W=Warehouse  D=Destination  *=path."""
    max_x = max(c[0] for c in all_coords) or 1
    max_y = max(c[1] for c in all_coords) or 1

    grid = [['.' for _ in range(size)] for _ in range(size)]

    # Draw path segments between consecutive waypoints
    for i in range(len(waypoints) - 1):
        _, p1 = waypoints[i]
        _, p2 = waypoints[i + 1]
        for step in range(1, 7):
            t  = step / 7
            px = p1[0] + t * (p2[0] - p1[0])
            py = p1[1] + t * (p2[1] - p1[1])
            gx, gy = _to_grid(px, py, max_x, max_y, size)
            if grid[size - 1 - gy][gx] == '.':
                grid[size - 1 - gy][gx] = '*'

    # Draw labelled waypoints on top
    for symbol, coord in waypoints:
        gx, gy = _to_grid(coord[0], coord[1], max_x, max_y, size)
        grid[size - 1 - gy][gx] = symbol

    lines = [f"Route — Agent {agent_id}  (S=Start  W=Warehouse  D=Destination  *=path)"]
    lines.append("+" + "-" * size + "+")
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + "-" * size + "+")
    return "\n".join(lines)


def ascii_overview_map(warehouses: dict, agents: dict,
                       packages: list, size: int = 22) -> str:
    """Overview map: all agents, warehouses, and destinations."""
    all_coords = (list(warehouses.values()) + list(agents.values())
                  + [p["destination"] for p in packages])
    max_x = max(c[0] for c in all_coords) or 1
    max_y = max(c[1] for c in all_coords) or 1

    grid = [['.' for _ in range(size)] for _ in range(size)]

    for loc in warehouses.values():
        gx, gy = _to_grid(*loc, max_x, max_y, size)
        grid[size - 1 - gy][gx] = 'W'

    for loc in agents.values():
        gx, gy = _to_grid(*loc, max_x, max_y, size)
        grid[size - 1 - gy][gx] = 'A'

    for pkg in packages:
        gx, gy = _to_grid(*pkg["destination"], max_x, max_y, size)
        if grid[size - 1 - gy][gx] == '.':
            grid[size - 1 - gy][gx] = 'D'

    lines = ["Overview Map  (W=Warehouse  A=Agent  D=Destination)"]
    lines.append("+" + "-" * size + "+")
    for row in grid:
        lines.append("|" + "".join(row) + "|")
    lines.append("+" + "-" * size + "+")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bonus 1 — Export top performer to CSV
# ---------------------------------------------------------------------------

def export_top_performer(report: dict):
    """Write the best agent's stats to CSV_FILE."""
    best = report.get("best_agent")
    if not best:
        print("No best agent to export.")
        return

    stats = report[best]
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "agent_id", "packages_delivered", "total_distance",
            "efficiency", "total_delay_minutes",
        ])
        writer.writeheader()
        writer.writerow({
            "agent_id":            best,
            "packages_delivered":  stats["packages_delivered"],
            "total_distance":      stats["total_distance"],
            "efficiency":          stats["efficiency"],
            "total_delay_minutes": stats["total_delay_minutes"],
        })
    print(f"Top performer exported to '{CSV_FILE}'.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load input
    with open(INPUT_FILE) as f:
        data = json.load(f)

    warehouses, agents, packages = normalise_input(data)
    assignment = assign_packages(warehouses, agents, packages)

    # Bonus 4: new agent joining mid-day
    if ENABLE_NEW_AGENT:
        agents, assignment = join_agent(
            NEW_AGENT_ID, NEW_AGENT_POS, agents, assignment, warehouses
        )

    # All coordinates — used to scale ASCII maps
    all_coords = (list(warehouses.values()) + list(agents.values())
                  + [p["destination"] for p in packages])

    # Simulate each agent
    print("\nRunning simulation...\n")
    report     = {}
    route_maps = []

    for aid, agent_pkgs in assignment.items():
        dist, delivered, waypoints, delay = simulate_agent(
            aid, agents[aid], agent_pkgs, warehouses
        )
        count      = len(delivered)
        efficiency = round(dist / count, 2) if count > 0 else 0.0

        report[aid] = {
            "packages_delivered":  count,
            "packages":            delivered,
            "total_distance":      round(dist, 2),
            "efficiency":          efficiency,
            "total_delay_minutes": delay,
        }

        route_maps.append(ascii_route_map(aid, waypoints, all_coords))

    # Best agent
    active = {aid: v for aid, v in report.items() if v["packages_delivered"] > 0}
    report["best_agent"] = (
        min(active, key=lambda aid: active[aid]["efficiency"]) if active else None
    )

    # Save report
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to '{OUTPUT_FILE}'.\n")

    # Print summary
    print("=" * 42)
    print("       FastBox Delivery Report")
    print("=" * 42)
    for aid, stats in report.items():
        if aid == "best_agent":
            continue
        print(f"\nAgent {aid}:")
        print(f"  Packages delivered   : {stats['packages_delivered']}  {stats['packages']}")
        print(f"  Total distance       : {stats['total_distance']}")
        print(f"  Efficiency (dist/pkg): {stats['efficiency']}")
        if stats["total_delay_minutes"]:
            print(f"  Total delay          : {stats['total_delay_minutes']} min")

    print(f"\n  Best Agent: {report['best_agent']}")

    # Bonus 3: ASCII maps
    print("\n" + "-" * 42)
    print("  Per-Agent Route Maps")
    print("-" * 42)
    for rmap in route_maps:
        print("\n" + rmap)

    print("\n" + "-" * 42)
    print("  Overview Map")
    print("-" * 42)
    print("\n" + ascii_overview_map(warehouses, agents, packages))

    # Bonus 1: CSV export
    export_top_performer(report)


if __name__ == "__main__":
    main()

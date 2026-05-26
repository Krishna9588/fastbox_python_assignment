"""
FastBox Delivery System — Test Case Runner
==========================================
Runs all test cases from the test_cases/ folder automatically.

For each test case, outputs are saved to:
  output_test_cases/<test_case_name>/report.json
  output_test_cases/<test_case_name>/top_performer.csv

Imports core logic from delivery_system.py — no duplication.
"""

import json
import csv
from pathlib import Path

from delivery_system import (
    normalise_input,
    assign_packages,
    simulate_agent,
    ascii_route_map,
    ascii_overview_map,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEST_CASES_DIR = "test_cases"
OUTPUT_DIR     = "output_test_cases"


# ---------------------------------------------------------------------------
# Per-test-case runner
# ---------------------------------------------------------------------------

def run_test_case(input_path: Path, output_dir: Path):
    """Run simulation for one test case and write outputs to output_dir."""

    with open(input_path) as f:
        data = json.load(f)

    warehouses, agents, packages = normalise_input(data)
    assignment = assign_packages(warehouses, agents, packages)

    all_coords = (list(warehouses.values()) + list(agents.values())
                  + [p["destination"] for p in packages])

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

    active = {aid: v for aid, v in report.items() if v["packages_delivered"] > 0}
    report["best_agent"] = (
        min(active, key=lambda aid: active[aid]["efficiency"]) if active else None
    )

    # Save report.json
    with open(output_dir / "report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Save top_performer.csv
    best = report.get("best_agent")
    if best:
        stats = report[best]
        with open(output_dir / "top_performer.csv", "w", newline="") as f:
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

    # Save ascii_maps.txt
    overview = ascii_overview_map(warehouses, agents, packages)
    with open(output_dir / "ascii_maps.txt", "w") as f:
        f.write(overview + "\n\n")
        for rmap in route_maps:
            f.write(rmap + "\n\n")

    return report


# ---------------------------------------------------------------------------
# Main — loop over all test cases
# ---------------------------------------------------------------------------

def main():
    test_cases_path = Path(TEST_CASES_DIR)
    test_files      = sorted(test_cases_path.glob("*.json"))

    if not test_files:
        print(f"No JSON files found in '{TEST_CASES_DIR}/'.")
        return

    print(f"Found {len(test_files)} test case(s). Running...\n")
    print("=" * 52)

    for input_path in test_files:
        case_name  = input_path.stem                        # e.g. "test_case_1"
        output_dir = Path(OUTPUT_DIR) / case_name
        output_dir.mkdir(parents=True, exist_ok=True)

        report = run_test_case(input_path, output_dir)

        best       = report.get("best_agent")
        total_pkgs = sum(v["packages_delivered"] for k, v in report.items()
                         if k != "best_agent")

        print(f"  {case_name}")
        print(f"    Packages delivered : {total_pkgs}")
        print(f"    Best agent         : {best}")
        print(f"    Output             : {output_dir}/")
        print()

    print("=" * 52)
    print(f"All results saved under '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()

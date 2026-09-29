"""
Runs the full experiment suite for the Campus Canteen Checkout Queue
Simulation and writes results tables (CSV) and plots (PNG) to ../Results/.

Scenarios:
    Baseline    - 1 cashier
    Alt A       - 2 cashiers
    Alt B       - 3 cashiers

30 independent replications per scenario, fixed seed list (base_seed=1000,
seeds 1000-1029) so every scenario sees a comparable set of random draws.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from canteen_sim import (
    run_scenario, run_single_replication, SIM_MINUTES,
    MEAN_INTERARRIVAL, MEAN_SERVICE_TIME, WAIT_TARGET_MIN,
)

N_REPLICATIONS = 30
BASE_SEED = 1000
SCENARIOS = {"Baseline (1 cashier)": 1, "Alt A (2 cashiers)": 2, "Alt B (3 cashiers)": 3}
RESULTS_DIR = "../Results"


def ci95(series):
    """Returns (mean, half-width of 95% CI) for a pandas Series."""
    n = len(series)
    mean = series.mean()
    se = series.std(ddof=1) / np.sqrt(n)
    half_width = se * stats.t.ppf(0.975, df=n - 1)
    return mean, half_width


def summarize(raw_df, label):
    rows = []
    for metric in ["avg_wait_min", "utilization", "students_served"]:
        mean, hw = ci95(raw_df[metric])
        rows.append({
            "scenario": label, "metric": metric,
            "mean": mean, "ci95_half_width": hw,
            "ci95_low": mean - hw, "ci95_high": mean + hw,
        })
    return pd.DataFrame(rows)


def main():
    # -----------------------------------------------------------------
    # 1) Baseline experiment: 30 replications per scenario
    # -----------------------------------------------------------------
    all_raw = []
    all_summary = []
    for label, n_cashiers in SCENARIOS.items():
        raw = run_scenario(n_cashiers, n_replications=N_REPLICATIONS, base_seed=BASE_SEED)
        raw["scenario"] = label
        all_raw.append(raw)
        all_summary.append(summarize(raw, label))

    raw_df = pd.concat(all_raw, ignore_index=True)
    summary_df = pd.concat(all_summary, ignore_index=True)

    raw_df.to_csv(f"{RESULTS_DIR}/replication_raw_results.csv", index=False)
    summary_df.to_csv(f"{RESULTS_DIR}/scenario_summary_95ci.csv", index=False)

    print("=== Scenario summary (mean, 95% CI) ===")
    pivot = summary_df.pivot(index="scenario", columns="metric", values="mean")
    print(pivot.round(3))
    print()

    # -----------------------------------------------------------------
    # 2) Verification & Validation checks
    # -----------------------------------------------------------------
    vv_notes = []

    # V&V Check 1: zero-demand edge case -> no students, no wait, 0 utilization
    zero_demand = run_single_replication(2, seed=1, mean_interarrival=1e9)
    check1 = (zero_demand["students_served"] == 0 and zero_demand["avg_wait_min"] == 0.0)
    vv_notes.append(("Zero-demand edge case", check1,
                      f"students_served={zero_demand['students_served']}, "
                      f"avg_wait={zero_demand['avg_wait_min']}"))

    # V&V Check 2: compare simulated light-traffic wait against the
    # analytical Pollaczek-Khinchine (M/G/1) approximation.
    # interarrival mean = 2.0 min (lambda = 0.5/min), service mean = 1.0 min,
    # CV = 0.5 -> rho = 0.5, Wq = lambda*E[S^2] / (2*(1-rho))
    lam = 1 / 2.0
    mean_s, cv_s = 1.0, 0.5
    var_s = (cv_s * mean_s) ** 2
    e_s2 = var_s + mean_s ** 2
    rho = lam * mean_s
    wq_analytical = (lam * e_s2) / (2 * (1 - rho))

    det_result = run_single_replication(
        1, seed=42, mean_interarrival=2.0, mean_service_time=1.0)
    rel_err = abs(det_result["avg_wait_min"] - wq_analytical) / wq_analytical
    check2 = rel_err < 0.5  # same order of magnitude, allowing finite-horizon noise
    vv_notes.append(("Light-traffic case vs. M/G/1 analytical approximation",
                      check2,
                      f"simulated={det_result['avg_wait_min']:.3f} min, "
                      f"analytical={wq_analytical:.3f} min, rel_err={rel_err:.2f}"))

    # V&V Check 3: monotonicity -- adding cashiers must not increase average wait
    means = pivot["avg_wait_min"]
    ordered = [means["Baseline (1 cashier)"], means["Alt A (2 cashiers)"], means["Alt B (3 cashiers)"]]
    check3 = ordered[0] >= ordered[1] >= ordered[2]
    vv_notes.append(("Monotonicity: wait time decreases as cashiers increase",
                      check3, f"means={[round(m,3) for m in ordered]}"))

    vv_df = pd.DataFrame(vv_notes, columns=["check", "passed", "detail"])
    vv_df.to_csv(f"{RESULTS_DIR}/verification_validation_checks.csv", index=False)
    print("=== Verification & Validation checks ===")
    print(vv_df.to_string(index=False))
    print()

    # -----------------------------------------------------------------
    # 3) Sensitivity analysis: +15% arrival rate
    # -----------------------------------------------------------------
    sens_summary = []
    for label, n_cashiers in SCENARIOS.items():
        raw = run_scenario(n_cashiers, n_replications=N_REPLICATIONS,
                            base_seed=BASE_SEED, arrival_rate_multiplier=1.15)
        raw["scenario"] = label
        s = summarize(raw, label)
        sens_summary.append(s)
    sens_df = pd.concat(sens_summary, ignore_index=True)
    sens_df.to_csv(f"{RESULTS_DIR}/sensitivity_plus15pct_arrivals.csv", index=False)

    print("=== Sensitivity analysis: +15% arrival rate ===")
    sens_pivot = sens_df.pivot(index="scenario", columns="metric", values="mean")
    print(sens_pivot.round(3))
    print()

    # -----------------------------------------------------------------
    # 4) Plots
    # -----------------------------------------------------------------
    order = list(SCENARIOS.keys())

    fig, ax = plt.subplots(figsize=(7, 4.5))
    wait_means = [pivot.loc[s, "avg_wait_min"] for s in order]
    wait_err = [summary_df[(summary_df.scenario == s) & (summary_df.metric == "avg_wait_min")]
                ["ci95_half_width"].values[0] for s in order]
    ax.bar(order, wait_means, yerr=wait_err, capsize=6, color="#4C72B0")
    ax.axhline(WAIT_TARGET_MIN, color="red", linestyle="--", label=f"Target ({WAIT_TARGET_MIN} min)")
    ax.set_ylabel("Average wait time (minutes)")
    ax.set_title("Average waiting time by scenario (95% CI, n=30)")
    ax.legend()
    plt.xticks(rotation=10)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/avg_wait_by_scenario.png", dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    util_means = [pivot.loc[s, "utilization"] for s in order]
    util_err = [summary_df[(summary_df.scenario == s) & (summary_df.metric == "utilization")]
                ["ci95_half_width"].values[0] for s in order]
    ax.bar(order, util_means, yerr=util_err, capsize=6, color="#DD8452")
    ax.set_ylabel("Cashier utilization (fraction of time busy)")
    ax.set_title("Cashier utilization by scenario (95% CI, n=30)")
    ax.set_ylim(0, 1.05)
    plt.xticks(rotation=10)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/utilization_by_scenario.png", dpi=150)
    plt.close()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    base_wait = [pivot.loc[s, "avg_wait_min"] for s in order]
    sens_wait = [sens_pivot.loc[s, "avg_wait_min"] for s in order]
    x = np.arange(len(order))
    width = 0.35
    ax.bar(x - width/2, base_wait, width, label="Baseline demand", color="#4C72B0")
    ax.bar(x + width/2, sens_wait, width, label="+15% arrival rate", color="#C44E52")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=10)
    ax.set_ylabel("Average wait time (minutes)")
    ax.set_title("Sensitivity analysis: average wait vs. arrival rate")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/sensitivity_comparison.png", dpi=150)
    plt.close()

    print("Saved CSVs and PNG plots to", RESULTS_DIR)


if __name__ == "__main__":
    main()

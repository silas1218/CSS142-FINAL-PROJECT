CSS142P Final Project - Campus Canteen Checkout Queue Simulation
Group 1

Members:
- Facultad, Josiah Jaravilla
- Juanico, Jessie Jasper, E
- Manlulu, Silas P.
- Sarenas, Heherson

DECISION QUESTION
How many checkout cashiers (1, 2, or 3) are needed during the campus canteen
lunch rush (11:30 AM-1:00 PM) to keep the average student waiting time at or
below a 3-minute target, without leaving cashiers mostly idle?

FOLDER STRUCTURE
  README.txt
  Report/CSS142P_FinalProject_Report.pdf     - full written report
  Model/CSS142P_FinalProject.ipynb            - executable simulation (pre-run, all outputs saved)
  Model/canteen_sim.py                        - simulation engine module (SimPy)
  Model/run_experiments.py                    - experiment runner (same logic as the notebook)
  Data/input_assumptions.csv                  - documented input parameters and sources
  Results/replication_raw_results.csv         - per-replication results, all scenarios (n=30 each)
  Results/scenario_summary_95ci.csv           - mean + 95% CI per scenario per metric
  Results/sensitivity_plus15pct_arrivals.csv  - sensitivity analysis results
  Results/verification_validation_checks.csv  - V&V check outcomes
  Results/*.png                               - generated plots
  Presentation/CSS142P_FinalProject_Presentation.pptx

HOW TO REPRODUCE THE RESULTS
1. Requirements: Python 3.10+, packages: simpy, numpy, pandas, scipy, matplotlib
   Install with:  pip install simpy numpy pandas scipy matplotlib
2. Easiest: open Model/CSS142P_FinalProject.ipynb in Jupyter or Google Colab
   and run all cells top to bottom. It regenerates every CSV and PNG in
   Results/ and prints the summary tables and V&V checks.
   (Alternative: run `python run_experiments.py` from inside Model/, which
   contains identical logic in plain-script form.)
3. All randomness is seeded (base_seed = 1000, one seed per replication,
   30 replications per scenario) so re-running reproduces the same numbers.

SCENARIOS
  Baseline (1 cashier) | Alt A (2 cashiers) | Alt B (3 cashiers)
  30 independent replications each, 90-minute simulated lunch rush.

KEY RESULT (see Report for full analysis)
  Baseline is saturated (utilization ~100%, average wait ~28 minutes) and
  fails the 3-minute target. Alt A (2 cashiers) meets the target with high,
  efficient utilization (~80%). Alt B (3 cashiers) also meets the target but
  leaves cashiers idle over 45% of the time. Recommendation: Alt A.

"""
CSS142P Final Project - Campus Canteen Checkout Queue Simulation
Group 1: Facultad, Josiah Jaravilla | Juanico, Jessie Jasper, E |
         Manlulu, Silas P. | Sarenas, Heherson

Discrete-event simulation of the canteen checkout line during the
lunch rush (11:30 AM - 1:00 PM). Built with SimPy.

Decision question:
    How many checkout cashiers (1, 2, or 3) are needed during the
    lunch rush to keep the average student waiting time at or below
    a 3-minute target, without leaving cashiers mostly idle?
"""

import simpy
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Fixed model parameters (see Report Section 4 for sources/justification)
# ---------------------------------------------------------------------------
SIM_MINUTES = 90.0          # 11:30 AM - 1:00 PM lunch rush
MEAN_INTERARRIVAL = 1.0     # minutes between student arrivals (baseline demand)
MEAN_SERVICE_TIME = 1.6     # minutes per checkout (mean)
SERVICE_TIME_CV = 0.5       # coefficient of variation for service time (lognormal)
WAIT_TARGET_MIN = 3.0       # decision-maker's acceptable average wait (minutes)


def _lognormal_params(mean, cv):
    """Convert a desired mean/CV to the mu, sigma of the underlying normal."""
    sigma2 = np.log(1 + cv ** 2)
    mu = np.log(mean) - sigma2 / 2
    return mu, np.sqrt(sigma2)


def student(env, name, cashiers, service_mu, service_sigma, records):
    arrival_time = env.now
    with cashiers.request() as req:
        yield req
        wait = env.now - arrival_time
        service_time = float(np.random.lognormal(service_mu, service_sigma))
        yield env.timeout(service_time)
        records.append({
            "student": name,
            "arrival_time": arrival_time,
            "wait_time": wait,
            "service_time": service_time,
            "departure_time": env.now,
        })


def arrival_process(env, cashiers, mean_interarrival, service_mu, service_sigma, records):
    i = 0
    while True:
        interarrival = float(np.random.exponential(mean_interarrival))
        yield env.timeout(interarrival)
        if env.now > SIM_MINUTES:
            break
        i += 1
        env.process(student(env, i, cashiers, service_mu, service_sigma, records))


def run_single_replication(num_cashiers, seed, arrival_rate_multiplier=1.0,
                            mean_interarrival=MEAN_INTERARRIVAL,
                            mean_service_time=MEAN_SERVICE_TIME):
    """
    Runs one independent replication of the canteen checkout queue and
    returns a dict of summary performance measures.
    """
    np.random.seed(seed)
    env = simpy.Environment()
    cashiers = simpy.Resource(env, capacity=num_cashiers)
    records = []

    effective_interarrival = mean_interarrival / arrival_rate_multiplier
    service_mu, service_sigma = _lognormal_params(mean_service_time, SERVICE_TIME_CV)

    env.process(arrival_process(env, cashiers, effective_interarrival,
                                 service_mu, service_sigma, records))
    # run a bit past close so students already in line finish being served
    env.run(until=SIM_MINUTES + 60)

    df = pd.DataFrame(records)
    if len(df) == 0:
        return {
            "num_cashiers": num_cashiers, "seed": seed,
            "students_served": 0, "avg_wait_min": 0.0,
            "max_wait_min": 0.0, "utilization": 0.0,
        }

    total_service_time = df["service_time"].sum()
    utilization = total_service_time / (num_cashiers * SIM_MINUTES)
    utilization = min(utilization, 1.0)

    return {
        "num_cashiers": num_cashiers,
        "seed": seed,
        "students_served": len(df),
        "avg_wait_min": df["wait_time"].mean(),
        "max_wait_min": df["wait_time"].max(),
        "utilization": utilization,
    }


def run_scenario(num_cashiers, n_replications=30, base_seed=1000,
                  arrival_rate_multiplier=1.0, **kwargs):
    """Runs n_replications independent replications for one scenario."""
    rows = []
    for r in range(n_replications):
        seed = base_seed + r
        rows.append(run_single_replication(
            num_cashiers, seed,
            arrival_rate_multiplier=arrival_rate_multiplier, **kwargs))
    return pd.DataFrame(rows)

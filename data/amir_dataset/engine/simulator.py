import random
import math

def poisson(lam, k):
    return (lam**k * math.exp(-lam)) / math.factorial(k)


def simulate_match(xg_home, xg_away):
    max_goals = 5
    results = {}

    for i in range(max_goals):
        for j in range(max_goals):
            prob = poisson(xg_home, i) * poisson(xg_away, j)
            results[(i, j)] = prob

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return sorted_results[:3]

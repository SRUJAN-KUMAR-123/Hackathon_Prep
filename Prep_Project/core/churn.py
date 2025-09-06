def churn_score(customer, avg7=None, avg30=None):
    """
    Simple churn scoring heuristic.
    Returns score from 0 to 100 (higher = more likely to churn).
    """
    score = 0

    # 1) Late recharge → big red flag
    if getattr(customer, "last_recharge_days_ago", None) and customer.last_recharge_days_ago > 28:
        score += 40

    # 2) Usage dropped a lot (avg 7 days < 30% of 30-day average)
    if avg30 and avg7 and (avg7 < 0.3 * avg30):
        score += 30

    # 3) Multiple complaints
    if getattr(customer, "complaints_last_90d", 0) >= 2:
        score += 20

    # 4) New customers (< 3 months tenure) churn faster
    if getattr(customer, "tenure_months", 0) < 3:
        score += 10

    return min(score, 100)

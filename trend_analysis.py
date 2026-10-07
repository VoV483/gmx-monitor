from datetime import datetime, timezone, timedelta


def safe_pct_change(current, previous):
    if previous is None or previous == 0:
        return None

    return (
        (current - previous)
        / previous
        * 100
    )


def calculate_liquidity_oi(item):
    """
    Liquidity / Open Interest.

    Чем меньше коэффициент,
    тем выше потенциальная нагрузка
    открытых позиций на доступную ликвидность.
    """

    oi_long = (
        item.get("open_interest_long_usd")
        or 0
    )

    oi_short = (
        item.get("open_interest_short_usd")
        or 0
    )

    liquidity_long = (
        item.get("liquidity_long_usd")
        or 0
    )

    liquidity_short = (
        item.get("liquidity_short_usd")
        or 0
    )

    total_oi = (
        oi_long
        + oi_short
    )

    total_liquidity = (
        liquidity_long
        + liquidity_short
    )

    if total_oi <= 0:
        return None

    return (
        total_liquidity
        / total_oi
    )


def market_risk_signal(item):
    """
    Первичная оценка риска рынка.

    Пока используем:
    - Liquidity/OI
    - дисбаланс Long/Short
    """

    reasons = []

    level = "GREEN"

    liquidity_oi = (
        calculate_liquidity_oi(item)
    )

    long_share = item.get(
        "oi_long_share_pct"
    )

    short_share = item.get(
        "oi_short_share_pct"
    )

    # ----------------------------------------
    # Liquidity / OI
    # ----------------------------------------

    if liquidity_oi is not None:

        if liquidity_oi < 1:
            level = "RED"

            reasons.append(
                "Liquidity/OI ниже 1.0x"
            )

        elif liquidity_oi < 2:
            if level != "RED":
                level = "YELLOW"

            reasons.append(
                "Liquidity/OI ниже 2.0x"
            )

    # ----------------------------------------
    # OI imbalance
    # ----------------------------------------

    if (
        long_share is not None
        and short_share is not None
    ):

        max_side = max(
            long_share,
            short_share,
        )

        if max_side >= 85:
            level = "RED"

            reasons.append(
                "OI imbalance выше 85%"
            )

        elif max_side >= 75:
            if level != "RED":
                level = "YELLOW"

            reasons.append(
                "OI imbalance выше 75%"
            )

    if not reasons:
        reasons.append(
            "Критических отклонений "
            "по OI и ликвидности нет"
        )

    return {
        "level": level,
        "liquidity_oi": liquidity_oi,
        "reasons": reasons,
    }


def build_market_map(rows):
    result = {}

    for row in rows:

        address = row[
            "market_address"
        ]

        if address:
            result[
                address.lower()
            ] = row

    return result


def print_market_risk_report(
    current_metrics,
    limit=10,
):
    """
    Текущий Risk Report по крупнейшим
    рынкам GLV.
    """

    sorted_metrics = sorted(
        current_metrics,
        key=lambda x: (
            x.get("glv_balance_usd")
            or 0
        ),
        reverse=True,
    )

    print("\n" + "=" * 100)
    print("MARKET RISK REPORT")
    print("=" * 100)

    red_count = 0
    yellow_count = 0

    for index, item in enumerate(
        sorted_metrics[:limit],
        start=1,
    ):

        risk = market_risk_signal(
            item
        )

        level = risk["level"]

        if level == "RED":
            red_count += 1

        elif level == "YELLOW":
            yellow_count += 1

        liquidity_oi = (
            risk["liquidity_oi"]
        )

        print("\n" + "-" * 100)

        print(
            f"{index}. "
            f"{item.get('market_name')}"
        )

        print(
            f"Signal: [{level}]"
        )

        if liquidity_oi is not None:
            print(
                f"Liquidity/OI: "
                f"{liquidity_oi:.2f}x"
            )
        else:
            print(
                "Liquidity/OI: N/A"
            )

        long_share = item.get(
            "oi_long_share_pct"
        )

        short_share = item.get(
            "oi_short_share_pct"
        )

        if (
            long_share is not None
            and short_share is not None
        ):
            print(
                f"OI balance: "
                f"{long_share:.2f}% Long / "
                f"{short_share:.2f}% Short"
            )

        apy = item.get("apy")

        if apy is not None:
            print(
                f"APY: "
                f"{apy * 100:.2f}%"
            )

        print(
            "Причина:",
            "; ".join(
                risk["reasons"]
            ),
        )

    print("\n" + "=" * 100)

    if red_count > 0:
        overall = "RED"

    elif yellow_count > 0:
        overall = "YELLOW"

    else:
        overall = "GREEN"

    print(
        f"MARKET RISK SIGNAL: "
        f"[ {overall} ]"
    )

    print(
        f"RED рынков: {red_count}"
    )

    print(
        f"YELLOW рынков: "
        f"{yellow_count}"
    )

    return overall


def print_historical_comparison(
    current_snapshot,
    snapshot_24h,
    snapshot_7d,
):
    """
    GLV-level сравнение:
    сейчас / 24 часа / 7 дней.
    """

    print("\n" + "=" * 100)
    print("GLV HISTORICAL TRENDS")
    print("=" * 100)

    current_assets = (
        current_snapshot[
            "total_assets_usd"
        ]
    )

    print(
        f"\nСейчас: "
        f"${current_assets:,.2f}"
    )

    # ----------------------------------------
    # 24 hours
    # ----------------------------------------

    if snapshot_24h is not None:

        assets_24h = (
            snapshot_24h[
                "total_assets_usd"
            ]
        )

        change_24h = safe_pct_change(
            current_assets,
            assets_24h,
        )

        print("\n24 HOURS")

        print(
            f"Assets 24h ago: "
            f"${assets_24h:,.2f}"
        )

        if change_24h is not None:
            print(
                f"Assets change: "
                f"{change_24h:+.2f}%"
            )

        top5_delta = (
            current_snapshot[
                "top5_share"
            ]
            - snapshot_24h[
                "top5_share"
            ]
        )

        print(
            f"TOP-5 concentration: "
            f"{top5_delta:+.2f} п.п."
        )

    else:

        print("\n24 HOURS")

        print(
            "Недостаточно истории. "
            "Нужен snapshot старше "
            "примерно 24 часов."
        )

    # ----------------------------------------
    # 7 days
    # ----------------------------------------

    if snapshot_7d is not None:

        assets_7d = (
            snapshot_7d[
                "total_assets_usd"
            ]
        )

        change_7d = safe_pct_change(
            current_assets,
            assets_7d,
        )

        print("\n7 DAYS")

        print(
            f"Assets 7d ago: "
            f"${assets_7d:,.2f}"
        )

        if change_7d is not None:
            print(
                f"Assets change: "
                f"{change_7d:+.2f}%"
            )

        top5_delta_7d = (
            current_snapshot[
                "top5_share"
            ]
            - snapshot_7d[
                "top5_share"
            ]
        )

        print(
            f"TOP-5 concentration: "
            f"{top5_delta_7d:+.2f} п.п."
        )

    else:

        print("\n7 DAYS")

        print(
            "Недостаточно истории. "
            "Нужен snapshot старше "
            "примерно 7 дней."
        )
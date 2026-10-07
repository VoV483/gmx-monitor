def evaluate_snapshot(current, previous):
    """
    Оценивает изменение состояния GLV.

    Возвращает:
    - общий статус
    - список сигналов
    - числовые изменения
    """

    signals = []

    red_count = 0
    yellow_count = 0

    # --------------------------------------------------
    # Total Assets
    # --------------------------------------------------

    previous_assets = previous["total_assets_usd"]
    current_assets = current["total_assets_usd"]

    if previous_assets > 0:
        asset_change_pct = (
            (current_assets - previous_assets)
            / previous_assets
            * 100
        )
    else:
        asset_change_pct = 0

    if asset_change_pct <= -15:

        signals.append({
            "level": "RED",
            "metric": "Total Assets",
            "message": (
                f"Сильное снижение активов: "
                f"{asset_change_pct:.2f}%"
            ),
        })

        red_count += 1

    elif asset_change_pct <= -5:

        signals.append({
            "level": "YELLOW",
            "metric": "Total Assets",
            "message": (
                f"Снижение активов: "
                f"{asset_change_pct:.2f}%"
            ),
        })

        yellow_count += 1

    else:

        signals.append({
            "level": "GREEN",
            "metric": "Total Assets",
            "message": (
                f"Изменение активов: "
                f"{asset_change_pct:+.2f}%"
            ),
        })

    # --------------------------------------------------
    # TOP-5 concentration
    # --------------------------------------------------

    top5_change = (
        current["top5_share"]
        - previous["top5_share"]
    )

    if top5_change >= 5:

        signals.append({
            "level": "RED",
            "metric": "TOP-5 concentration",
            "message": (
                f"Концентрация TOP-5 выросла "
                f"на {top5_change:.2f} п.п."
            ),
        })

        red_count += 1

    elif top5_change >= 2:

        signals.append({
            "level": "YELLOW",
            "metric": "TOP-5 concentration",
            "message": (
                f"Концентрация TOP-5 выросла "
                f"на {top5_change:.2f} п.п."
            ),
        })

        yellow_count += 1

    else:

        signals.append({
            "level": "GREEN",
            "metric": "TOP-5 concentration",
            "message": (
                f"Изменение концентрации TOP-5: "
                f"{top5_change:+.2f} п.п."
            ),
        })

    # --------------------------------------------------
    # TOP-10 concentration
    # --------------------------------------------------

    top10_change = (
        current["top10_share"]
        - previous["top10_share"]
    )

    if top10_change >= 7:

        signals.append({
            "level": "RED",
            "metric": "TOP-10 concentration",
            "message": (
                f"Концентрация TOP-10 выросла "
                f"на {top10_change:.2f} п.п."
            ),
        })

        red_count += 1

    elif top10_change >= 3:

        signals.append({
            "level": "YELLOW",
            "metric": "TOP-10 concentration",
            "message": (
                f"Концентрация TOP-10 выросла "
                f"на {top10_change:.2f} п.п."
            ),
        })

        yellow_count += 1

    else:

        signals.append({
            "level": "GREEN",
            "metric": "TOP-10 concentration",
            "message": (
                f"Изменение концентрации TOP-10: "
                f"{top10_change:+.2f} п.п."
            ),
        })

    # --------------------------------------------------
    # Disabled markets
    # --------------------------------------------------

    disabled_change = (
        current["disabled_market_count"]
        - previous["disabled_market_count"]
    )

    if disabled_change > 0:

        signals.append({
            "level": "RED",
            "metric": "Disabled markets",
            "message": (
                f"Появилось новых отключенных рынков: "
                f"{disabled_change}"
            ),
        })

        red_count += 1

    else:

        signals.append({
            "level": "GREEN",
            "metric": "Disabled markets",
            "message": (
                "Новых отключенных рынков нет."
            ),
        })

    # --------------------------------------------------
    # Market count
    # --------------------------------------------------

    market_change = (
        current["market_count"]
        - previous["market_count"]
    )

    if market_change < 0:

        signals.append({
            "level": "YELLOW",
            "metric": "Market count",
            "message": (
                f"Количество рынков уменьшилось "
                f"на {abs(market_change)}."
            ),
        })

        yellow_count += 1

    elif market_change > 0:

        signals.append({
            "level": "GREEN",
            "metric": "Market count",
            "message": (
                f"Добавлено рынков: "
                f"{market_change}."
            ),
        })

    else:

        signals.append({
            "level": "GREEN",
            "metric": "Market count",
            "message": (
                "Количество рынков не изменилось."
            ),
        })

    # --------------------------------------------------
    # Итоговый статус
    # --------------------------------------------------

    if red_count > 0:
        overall_status = "RED"

    elif yellow_count > 0:
        overall_status = "YELLOW"

    else:
        overall_status = "GREEN"

    return {
        "status": overall_status,
        "red_count": red_count,
        "yellow_count": yellow_count,
        "asset_change_pct": asset_change_pct,
        "top5_change": top5_change,
        "top10_change": top10_change,
        "signals": signals,
    }


def print_signal_report(result):
    """
    Вывод итогового отчета Signal Engine.
    """

    print("\n" + "=" * 70)
    print("SIGNAL ENGINE")
    print("=" * 70)

    status = result["status"]

    if status == "GREEN":
        symbol = "[ GREEN ]"

    elif status == "YELLOW":
        symbol = "[ YELLOW ]"

    else:
        symbol = "[ RED ]"

    print(f"\nИТОГОВЫЙ СИГНАЛ: {symbol}")

    print("\nПричины:")

    for signal in result["signals"]:

        print(
            f"{signal['level']:6} | "
            f"{signal['metric']:22} | "
            f"{signal['message']}"
        )

    print("\nСводка:")

    print(
        f"RED сигналов: "
        f"{result['red_count']}"
    )

    print(
        f"YELLOW сигналов: "
        f"{result['yellow_count']}"
    )
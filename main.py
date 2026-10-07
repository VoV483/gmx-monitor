from pprint import pprint

from datetime import (
    datetime,
    timezone,
    timedelta,
)

from market_metrics import (
    build_glv_market_metrics,
    print_glv_market_metrics,
)

from gmx_client import GMXClient

from storage import (
    init_db,
    save_glv_snapshot,
    save_market_metrics,
    get_last_two_snapshots,
    get_market_snapshots,
    get_market_metrics_count,
    get_latest_glv_snapshot,
    get_glv_snapshot_before,
    get_market_metrics_for_snapshot,
)

from trend_analysis import (
    print_market_risk_report,
    print_historical_comparison,
)

from signal_engine import (
    evaluate_snapshot,
    print_signal_report,
)

TARGET_ADDRESS = "0x528A5bac7E746C9A509A1f4F6dF58A03d44279F9"


def normalize_list(data):
    """
    Приводит ответ API к обычному Python list.
    """

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in [
            "markets",
            "glvs",
            "data",
            "items",
        ]:
            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def find_by_address(items, target_address):
    """
    Ищет адрес в наиболее вероятных полях GMX API.
    """

    target = target_address.lower()

    possible_fields = [
        "marketToken",
        "marketTokenAddress",
        "address",
        "glvToken",
        "tokenAddress",
    ]

    for item in items:
        if not isinstance(item, dict):
            continue

        for field in possible_fields:
            value = item.get(field)

            if (
                isinstance(value, str)
                and value.lower() == target
            ):
                return item

    return None


def format_usd30(value):
    """
    GMX часто хранит USD значения с precision 1e30.
    """

    if value is None:
        return None

    try:
        return float(value) / 1e30
    except (ValueError, TypeError):
        return None


def print_market_info(market):
    """
    Красивый вывод информации по обычному GM market.
    """

    print("\n" + "=" * 70)
    print("GMX MARKET INFO")
    print("=" * 70)

    print("Название:", market.get("name", "N/A"))
    print("Market token:", market.get("marketToken", "N/A"))
    print("Listed:", market.get("isListed", "N/A"))
    print("Listing date:", market.get("listingDate", "N/A"))

    print("\nTOKENS")

    print("Index token:", market.get("indexToken"))
    print("Long token:", market.get("longToken"))
    print("Short token:", market.get("shortToken"))

    print("\nOPEN INTEREST")

    oi_long = format_usd30(
        market.get("openInterestLong")
    )

    oi_short = format_usd30(
        market.get("openInterestShort")
    )

    if oi_long is not None:
        print(f"Long:  ${oi_long:,.2f}")
    else:
        print("Long: N/A")

    if oi_short is not None:
        print(f"Short: ${oi_short:,.2f}")
    else:
        print("Short: N/A")

    if oi_long is not None and oi_short is not None:
        total_oi = oi_long + oi_short

        print(f"Total: ${total_oi:,.2f}")

        if total_oi > 0:
            print(
                f"Long share: "
                f"{oi_long / total_oi * 100:.2f}%"
            )

            print(
                f"Short share: "
                f"{oi_short / total_oi * 100:.2f}%"
            )

    print("\nAVAILABLE LIQUIDITY")

    liquidity_long = format_usd30(
        market.get("availableLiquidityLong")
    )

    liquidity_short = format_usd30(
        market.get("availableLiquidityShort")
    )

    if liquidity_long is not None:
        print(f"Long:  ${liquidity_long:,.2f}")
    else:
        print("Long: N/A")

    if liquidity_short is not None:
        print(f"Short: ${liquidity_short:,.2f}")
    else:
        print("Short: N/A")

    print("\nRATES")

    print(
        "Funding long raw:",
        market.get("fundingRateLong"),
    )

    print(
        "Funding short raw:",
        market.get("fundingRateShort"),
    )

    print(
        "Borrowing long raw:",
        market.get("borrowingRateLong"),
    )

    print(
        "Borrowing short raw:",
        market.get("borrowingRateShort"),
    )


def print_glv_info(glv):
    """
    Красивый вывод основных показателей GLV.
    """

    print("\n" + "=" * 70)
    print("GMX GLV INFO")
    print("=" * 70)

    print("Название:", glv.get("name"))
    print("GLV token:", glv.get("glvToken"))
    print("Listed:", glv.get("isListed"))
    print("Listing date:", glv.get("listingDate"))

    markets = glv.get("markets", [])

    total_usd = sum(
        int(m.get("balanceUsd", 0))
        for m in markets
    ) / 1e30

    active_markets = [
        m
        for m in markets
        if not m.get("isDisabled", False)
    ]

    disabled_markets = [
        m
        for m in markets
        if m.get("isDisabled", False)
    ]

    print(f"\nКоличество рынков: {len(markets)}")
    print(f"Total assets: ${total_usd:,.2f}")
    print(f"Активных рынков: {len(active_markets)}")
    print(f"Отключённых рынков: {len(disabled_markets)}")

    sorted_markets = sorted(
        markets,
        key=lambda x: int(
            x.get("balanceUsd", 0)
        ),
        reverse=True,
    )

    print("\nTOP-10 рынков:")
    print("-" * 70)

    for index, market in enumerate(
        sorted_markets[:10],
        start=1,
    ):
        balance_usd = (
            int(market.get("balanceUsd", 0))
            / 1e30
        )

        share = (
            int(market.get("share", 0))
            / 1e30
            * 100
        )

        address = market.get(
            "address",
            "N/A",
        )

        print(
            f"{index:2}. "
            f"{address}  "
            f"${balance_usd:,.2f}  "
            f"{share:.2f}%"
        )

    top5_share = sum(
        int(m.get("share", 0))
        for m in sorted_markets[:5]
    ) / 1e30 * 100

    top10_share = sum(
        int(m.get("share", 0))
        for m in sorted_markets[:10]
    ) / 1e30 * 100

    print("\nCONCENTRATION")

    print(
        f"TOP-5 share:  "
        f"{top5_share:.2f}%"
    )

    print(
        f"TOP-10 share: "
        f"{top10_share:.2f}%"
    )


def print_market_changes(
    previous_snapshot_id,
    current_snapshot_id,
):
    """
    Показывает рынки GLV
    с наибольшими изменениями.
    """

    previous_rows = get_market_snapshots(
        previous_snapshot_id
    )

    current_rows = get_market_snapshots(
        current_snapshot_id
    )

    previous = {
        row["market_address"].lower(): row
        for row in previous_rows
        if row["market_address"]
    }

    current = {
        row["market_address"].lower(): row
        for row in current_rows
        if row["market_address"]
    }

    changes = []

    for address, current_market in current.items():
        previous_market = previous.get(
            address
        )

        if previous_market is None:
            changes.append(
                {
                    "address": address,
                    "type": "NEW",
                    "balance_change": (
                        current_market[
                            "balance_usd"
                        ]
                    ),
                    "share_change": (
                        current_market[
                            "share_pct"
                        ]
                    ),
                }
            )

            continue

        balance_change = (
            current_market["balance_usd"]
            - previous_market["balance_usd"]
        )

        share_change = (
            current_market["share_pct"]
            - previous_market["share_pct"]
        )

        changes.append(
            {
                "address": address,
                "type": "CHANGE",
                "balance_change": balance_change,
                "share_change": share_change,
            }
        )

    for address in previous:
        if address not in current:
            changes.append(
                {
                    "address": address,
                    "type": "REMOVED",
                    "balance_change": (
                        -previous[address][
                            "balance_usd"
                        ]
                    ),
                    "share_change": (
                        -previous[address][
                            "share_pct"
                        ]
                    ),
                }
            )

    changes.sort(
        key=lambda x: abs(
            x["balance_change"]
        ),
        reverse=True,
    )

    print(
        "\nКРУПНЕЙШИЕ ИЗМЕНЕНИЯ "
        "ПО РЫНКАМ"
    )

    print("-" * 70)

    for item in changes[:10]:
        print(
            f"{item['type']:8} "
            f"{item['address']}  "
            f"${item['balance_change']:+,.2f}  "
            f"{item['share_change']:+.2f} п.п."
        )


def print_snapshot_comparison(
    glv_address,
):
    """
    Сравнивает два последних snapshot.
    """

    snapshots = get_last_two_snapshots(
        glv_address
    )

    if len(snapshots) < 2:
        print("\n" + "=" * 70)
        print("ИСТОРИЯ")
        print("=" * 70)

        print(
            "Это первый snapshot. "
            "Сравнивать пока не с чем."
        )

        return

    current = snapshots[0]
    previous = snapshots[1]

    signal_result = evaluate_snapshot(
    current,
    previous,
)

    print("\n" + "=" * 70)

    print(
        "ИЗМЕНЕНИЯ С ПРЕДЫДУЩЕГО "
        "SNAPSHOT"
    )

    print("=" * 70)

    print(
        "Предыдущий:",
        previous["created_at"],
    )

    print(
        "Текущий:",
        current["created_at"],
    )

    asset_change = (
        current["total_assets_usd"]
        - previous["total_assets_usd"]
    )

    if previous["total_assets_usd"] != 0:
        asset_change_pct = (
            asset_change
            / previous["total_assets_usd"]
            * 100
        )
    else:
        asset_change_pct = 0

    print("\nTotal assets:")

    print(
        f"  было: "
        f"${previous['total_assets_usd']:,.2f}"
    )

    print(
        f"  стало: "
        f"${current['total_assets_usd']:,.2f}"
    )

    print(
        f"  изменение: "
        f"${asset_change:+,.2f} "
        f"({asset_change_pct:+.2f}%)"
    )

    top5_delta = (
        current["top5_share"]
        - previous["top5_share"]
    )

    top10_delta = (
        current["top10_share"]
        - previous["top10_share"]
    )

    print("\nTOP-5 concentration:")

    print(
        f"  было: "
        f"{previous['top5_share']:.2f}%"
    )

    print(
        f"  стало: "
        f"{current['top5_share']:.2f}%"
    )

    print(
        f"  изменение: "
        f"{top5_delta:+.2f} п.п."
    )

    print("\nTOP-10 concentration:")

    print(
        f"  было: "
        f"{previous['top10_share']:.2f}%"
    )

    print(
        f"  стало: "
        f"{current['top10_share']:.2f}%"
    )

    print(
        f"  изменение: "
        f"{top10_delta:+.2f} п.п."
    )

    print("\nКоличество рынков:")

    print(
        f"  было: "
        f"{previous['market_count']}"
    )

    print(
        f"  стало: "
        f"{current['market_count']}"
    )

    print("\nОтключённых рынков:")

    print(
        f"  было: "
        f"{previous['disabled_market_count']}"
    )

    print(
        f"  стало: "
        f"{current['disabled_market_count']}"
    )

    print_market_changes(
        previous["id"],
        current["id"],
    )

    print_signal_report(
    signal_result
)


def main():
    init_db()

    print("=" * 70)
    print("GMX MONITOR v0.8")
    print("=" * 70)

    print(
        "\nИскомый адрес:",
        TARGET_ADDRESS,
    )

    client = GMXClient()

    print(
        "\n[1] Получаем /markets/info ..."
    )

    markets_info_response = (
        client.get_markets_info()
    )

    markets = normalize_list(
        markets_info_response
    )

    print(
        f"Получено рынков: "
        f"{len(markets)}"
    )

    market = find_by_address(
        markets,
        TARGET_ADDRESS,
    )

    if market:
        print(
            "\nАдрес найден как GM market."
        )

        print_market_info(market)

        return

    print(
        "\nАдрес не найден "
        "среди GM markets."
    )

    print(
        "\n[2] Проверяем /glvs/info ..."
    )

    try:
        glvs_response = (
            client.get_glvs_info()
        )

        glvs = normalize_list(
            glvs_response
        )

        print(
            f"Получено GLV объектов: "
            f"{len(glvs)}"
        )

        glv = find_by_address(
            glvs,
            TARGET_ADDRESS,
        )

        if glv:
            print(
                "\nАдрес найден "
                "как GLV vault."
            )

            print_glv_info(glv)

            snapshot_id = (
                save_glv_snapshot(glv)
            )

            print(
                f"\nSnapshot сохранен. "
                f"ID: {snapshot_id}"
            )

            print_snapshot_comparison(
                TARGET_ADDRESS
            )

            markets_info_response = (
    client.get_markets_info()
)

            apy_response = client.get_apy(
                period="7d"
            )

            metrics = build_glv_market_metrics(
            glv,
            markets_info_response,
            apy_response,
        )

        save_market_metrics(
            snapshot_id,
            metrics,
        )

        print_glv_market_metrics(
            metrics,
            limit=10,
        )

        print_market_risk_report(
            metrics,
            limit=10,
        )

        current_snapshot = (
            get_latest_glv_snapshot(
                TARGET_ADDRESS
            )
        )

        now = datetime.now(
            timezone.utc
        )

        time_24h = (
            now
            - timedelta(hours=24)
        ).isoformat()

        time_7d = (
            now
            - timedelta(days=7)
        ).isoformat()

        snapshot_24h = (
            get_glv_snapshot_before(
                TARGET_ADDRESS,
                time_24h,
            )
        )

        snapshot_7d = (
            get_glv_snapshot_before(
                TARGET_ADDRESS,
                time_7d,
            )
        )

        print_historical_comparison(
            current_snapshot,
            snapshot_24h,
            snapshot_7d,
        )

        print(
            f"\nMarket metrics сохранено: "
            f"{len(metrics)}"
        )

        print(
            f"Всего записей market_metrics "
            f"в SQLite: "
            f"{get_market_metrics_count()}"
        )

        return

    except Exception as error:
        print(
            "Ошибка при чтении GLV:",
            error,
        )

    print(
        "\n[3] Проверяем APY ..."
    )

    try:
        apy_response = client.get_apy(
            period="7d"
        )

        apy_items = normalize_list(
            apy_response
        )

        apy_object = find_by_address(
            apy_items,
            TARGET_ADDRESS,
        )

        if apy_object:
            print(
                "\nАдрес найден "
                "в APY endpoint:"
            )

            pprint(apy_object)

            return

    except Exception as error:
        print(
            "Ошибка APY:",
            error,
        )

    print(
        "\n[4] Проверяем performance ..."
    )

    try:
        performance = (
            client.get_performance(
                period="30d",
                address=TARGET_ADDRESS,
            )
        )

        print(
            "\nОтвет performance:"
        )

        pprint(performance)

    except Exception as error:
        print(
            "Ошибка performance:",
            error,
        )

    print("\n" + "=" * 70)

    print(
        "Адрес не удалось "
        "однозначно идентифицировать."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
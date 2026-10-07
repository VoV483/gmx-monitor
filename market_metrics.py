def normalize_list(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in [
            "markets",
            "data",
            "items",
        ]:
            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def build_market_info_map(
    markets_info,
):
    result = {}

    for market in markets_info:
        address = market.get(
            "marketToken"
        )

        if address:
            result[
                address.lower()
            ] = market

    return result


def build_apy_map(
    apy_response,
):
    result = {}

    if not isinstance(
        apy_response,
        dict,
    ):
        return result

    markets = apy_response.get(
        "markets",
        {},
    )

    if not isinstance(
        markets,
        dict,
    ):
        return result

    for address, data in markets.items():
        if isinstance(data, dict):
            result[
                address.lower()
            ] = data

    return result


def usd30(value):
    if value in (
        None,
        "",
    ):
        return None

    try:
        return float(value) / 1e30
    except (
        ValueError,
        TypeError,
    ):
        return None


def float_or_none(value):
    if value in (
        None,
        "",
    ):
        return None

    try:
        return float(value)
    except (
        ValueError,
        TypeError,
    ):
        return None


def build_glv_market_metrics(
    glv,
    markets_info_response,
    apy_response,
):
    markets_info = normalize_list(
        markets_info_response
    )

    market_info_map = (
        build_market_info_map(
            markets_info
        )
    )

    apy_map = build_apy_map(
        apy_response
    )

    glv_markets = glv.get(
        "markets",
        [],
    )

    metrics = []

    for glv_market in glv_markets:
        address = glv_market.get(
            "address"
        )

        if not address:
            continue

        market_info = (
            market_info_map.get(
                address.lower()
            )
        )

        if not market_info:
            continue

        apy_info = apy_map.get(
            address.lower(),
            {},
        )

        balance_usd = (
            int(
                glv_market.get(
                    "balanceUsd",
                    0,
                )
            )
            / 1e30
        )

        share_pct = (
            int(
                glv_market.get(
                    "share",
                    0,
                )
            )
            / 1e30
            * 100
        )

        oi_long = usd30(
            market_info.get(
                "openInterestLong"
            )
        )

        oi_short = usd30(
            market_info.get(
                "openInterestShort"
            )
        )

        total_oi = (
            (oi_long or 0)
            + (oi_short or 0)
        )

        if total_oi > 0:
            oi_long_share = (
                (oi_long or 0)
                / total_oi
                * 100
            )

            oi_short_share = (
                (oi_short or 0)
                / total_oi
                * 100
            )

        else:
            oi_long_share = None
            oi_short_share = None

        metric = {
            "market_address":
                address,

            "market_name":
                market_info.get(
                    "name"
                ),

            "glv_balance_usd":
                balance_usd,

            "glv_share_pct":
                share_pct,

            "apy":
                float_or_none(
                    apy_info.get(
                        "apy"
                    )
                ),

            "base_apy":
                float_or_none(
                    apy_info.get(
                        "baseApy"
                    )
                ),

            "bonus_apr":
                float_or_none(
                    apy_info.get(
                        "bonusApr"
                    )
                ),

            "open_interest_long_usd":
                oi_long,

            "open_interest_short_usd":
                oi_short,

            "oi_long_share_pct":
                oi_long_share,

            "oi_short_share_pct":
                oi_short_share,

            "liquidity_long_usd":
                usd30(
                    market_info.get(
                        "availableLiquidityLong"
                    )
                ),

            "liquidity_short_usd":
                usd30(
                    market_info.get(
                        "availableLiquidityShort"
                    )
                ),

            "funding_long_raw":
                market_info.get(
                    "fundingRateLong"
                ),

            "funding_short_raw":
                market_info.get(
                    "fundingRateShort"
                ),

            "borrowing_long_raw":
                market_info.get(
                    "borrowingRateLong"
                ),

            "borrowing_short_raw":
                market_info.get(
                    "borrowingRateShort"
                ),
        }

        metrics.append(metric)

    return metrics


def print_glv_market_metrics(
    metrics,
    limit=10,
):
    sorted_metrics = sorted(
        metrics,
        key=lambda x: (
            x.get(
                "glv_balance_usd"
            )
            or 0
        ),
        reverse=True,
    )

    print("\n" + "=" * 100)
    print(
        "GLV MARKET METRICS "
        f"— TOP {limit}"
    )
    print("=" * 100)

    for index, item in enumerate(
        sorted_metrics[:limit],
        start=1,
    ):
        print(
            "\n"
            + "-"
            * 100
        )

        print(
            f"{index}. "
            f"{item['market_name']}"
        )

        print(
            "Market:",
            item["market_address"],
        )

        print(
            f"GLV balance: "
            f"${item['glv_balance_usd']:,.2f}"
        )

        print(
            f"GLV share: "
            f"{item['glv_share_pct']:.2f}%"
        )

        if item["apy"] is not None:
            print(
                f"Total APY: "
                f"{item['apy'] * 100:.2f}%"
            )
        else:
            print(
                "Total APY: N/A"
            )

        if item[
            "base_apy"
        ] is not None:
            print(
                f"Base APY: "
                f"{item['base_apy'] * 100:.2f}%"
            )

        if item[
            "bonus_apr"
        ] is not None:
            print(
                f"Bonus APR: "
                f"{item['bonus_apr'] * 100:.2f}%"
            )

        print(
            f"OI Long: "
            f"${item['open_interest_long_usd']:,.2f}"
            if item[
                "open_interest_long_usd"
            ] is not None
            else "OI Long: N/A"
        )

        print(
            f"OI Short: "
            f"${item['open_interest_short_usd']:,.2f}"
            if item[
                "open_interest_short_usd"
            ] is not None
            else "OI Short: N/A"
        )

        if item[
            "oi_long_share_pct"
        ] is not None:
            print(
                f"OI balance: "
                f"{item['oi_long_share_pct']:.2f}% Long / "
                f"{item['oi_short_share_pct']:.2f}% Short"
            )

        print(
            f"Liquidity Long: "
            f"${item['liquidity_long_usd']:,.2f}"
            if item[
                "liquidity_long_usd"
            ] is not None
            else "Liquidity Long: N/A"
        )

        print(
            f"Liquidity Short: "
            f"${item['liquidity_short_usd']:,.2f}"
            if item[
                "liquidity_short_usd"
            ] is not None
            else "Liquidity Short: N/A"
        )

        print(
            "Funding Long raw:",
            item[
                "funding_long_raw"
            ],
        )

        print(
            "Funding Short raw:",
            item[
                "funding_short_raw"
            ],
        )

        print(
            "Borrowing Long raw:",
            item[
                "borrowing_long_raw"
            ],
        )

        print(
            "Borrowing Short raw:",
            item[
                "borrowing_short_raw"
            ],
        )
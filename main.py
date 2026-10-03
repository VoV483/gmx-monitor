from pprint import pprint

from gmx_client import GMXClient


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


def format_rate(value):
    """
    Rates GMX могут использовать высокую fixed-point precision.
    Пока выводим raw + приблизительное значение.
    """

    if value is None:
        return None

    try:
        return float(value) / 1e30
    except (ValueError, TypeError):
        return None


def print_market_info(market):
    """
    Красивый вывод основных метрик GMX market.
    """

    print("\n" + "=" * 70)
    print("GMX MARKET INFO")
    print("=" * 70)

    print(
        "Название:",
        market.get("name", "N/A"),
    )

    print(
        "Market token:",
        market.get("marketToken", "N/A"),
    )

    print(
        "Listed:",
        market.get("isListed", "N/A"),
    )

    print(
        "Listing date:",
        market.get("listingDate", "N/A"),
    )

    print("\nTOKENS")

    print(
        "Index token:",
        market.get("indexToken"),
    )

    print(
        "Long token:",
        market.get("longToken"),
    )

    print(
        "Short token:",
        market.get("shortToken"),
    )

    print("\nOPEN INTEREST")

    oi_long = format_usd30(
        market.get("openInterestLong")
    )

    oi_short = format_usd30(
        market.get("openInterestShort")
    )

    print(
        f"Long:  ${oi_long:,.2f}"
        if oi_long is not None
        else "Long: N/A"
    )

    print(
        f"Short: ${oi_short:,.2f}"
        if oi_short is not None
        else "Short: N/A"
    )

    if oi_long is not None and oi_short is not None:

        total_oi = oi_long + oi_short

        print(
            f"Total: ${total_oi:,.2f}"
        )

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

    print(
        f"Long:  ${liquidity_long:,.2f}"
        if liquidity_long is not None
        else "Long: N/A"
    )

    print(
        f"Short: ${liquidity_short:,.2f}"
        if liquidity_short is not None
        else "Short: N/A"
    )

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

    print("\nRAW OBJECT")

    pprint(market)


def main():

    print("=" * 70)
    print("GMX MONITOR v0.2")
    print("=" * 70)

    print(
        "\nИскомый адрес:",
        TARGET_ADDRESS,
    )

    client = GMXClient()

    #
    # 1. GM markets
    #

    print("\n[1] Получаем /markets/info ...")

    markets_info_response = (
        client.get_markets_info()
    )

    markets = normalize_list(
        markets_info_response
    )

    print(
        f"Получено рынков: {len(markets)}"
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
        "\nАдрес не найден среди GM markets."
    )

    #
    # 2. GLV
    #

    print("\n[2] Проверяем /glvs/info ...")

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
                "\nАдрес найден как GLV vault."
            )

            pprint(glv)

            return

    except Exception as error:

        print(
            "Ошибка при чтении GLV:",
            error,
        )

    #
    # 3. APY
    #

    print("\n[3] Проверяем APY ...")

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
                "\nАдрес найден в APY endpoint:"
            )

            pprint(apy_object)

            return

    except Exception as error:

        print(
            "Ошибка APY:",
            error,
        )

    #
    # 4. Performance
    #

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
        "Адрес не удалось однозначно "
        "идентифицировать."
    )

    print(
        "Покажите вывод программы — "
        "по нему определим тип объекта."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
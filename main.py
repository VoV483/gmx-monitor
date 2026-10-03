from pprint import pprint

from gmx_client import GMXClient

TARGET_MARKET = "0x528A5bac7E746C9A509A1f4F6dF58A03d44279F9"


def extract_markets(response, endpoint: str):
    """GMX возвращает объект с markets; также поддерживаем прямой список."""
    markets = response.get("markets") if isinstance(response, dict) else response
    if not isinstance(markets, list) or not all(
        isinstance(market, dict) for market in markets
    ):
        raise ValueError(f"Неожиданная структура {endpoint}: ожидался список markets")
    return markets


def find_market(markets, market_address: str):

    target = market_address.lower()

    for market in markets:

        possible_addresses = [
            market.get("marketToken"),
            market.get("marketTokenAddress"),
            market.get("address"),
        ]

        for address in possible_addresses:

            if isinstance(address, str) and address.lower() == target:
                return market

    return None


def main():
    print("=" * 70)
    print("GMX MONITOR")
    print("=" * 70)

    client = GMXClient()

    print("\nПолучаем список рынков GMX...\n")

    markets = client.get_markets()

    print(f"Тип ответа: {type(markets).__name__}")

    market_list = extract_markets(markets, "/markets")

    target_market = find_market(market_list, TARGET_MARKET)

    print("\n" + "=" * 70)
    print("ИСКОМЫЙ РЫНОК")
    print("=" * 70)

    if target_market:
        pprint(target_market)
    else:
        print(
            f"Рынок {TARGET_MARKET} "
            "не найден в /markets"
        )

    print(f"Количество рынков: {len(market_list)}")

    print("\nПервые 5 рынков:")
    print("-" * 70)

    for index, market in enumerate(market_list[:5], start=1):

        print("-" * 70)

        print(f"Рынок #{index}")

        print(
            "Название:",
            market.get("name")
            or market.get("marketName")
            or "N/A"
        )

        print(
            "Market token:",
            market.get("marketToken")
            or market.get("marketTokenAddress")
            or market.get("address")
            or "N/A"
        )

    print("\n" + "=" * 70)
    print("Получаем /markets/info...")
    print("=" * 70)

    markets_info = client.get_markets_info()

    info_list = extract_markets(markets_info, "/markets/info")
    print(f"\nПолучено записей: {len(info_list)}")
    print("\nПервая запись /markets/info:")
    pprint(info_list[0] if info_list else None)


if __name__ == "__main__":
    main()

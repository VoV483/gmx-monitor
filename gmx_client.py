import requests

class GMXClient:
    """
    Простой клиент для публичного GMX Oracle API.
    """

    BASE_URL = "https://arbitrum-api.gmxinfra.io"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def _get(self, endpoint: str):
        url = f"{self.BASE_URL}{endpoint}"

        response = requests.get(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "gmx-monitor/0.1",
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()

    def get_markets(self):
        """
        Получить список рынков GMX.
        """
        return self._get("/markets")

    def get_markets_info(self):
        """
        Получить актуальное состояние рынков:
        liquidity, open interest, funding, borrowing и др.
        """
        return self._get("/markets/info")
import requests


class GMXClient:
    BASE_URL = "https://arbitrum-api.gmxinfra.io"

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def _get(self, endpoint: str, params=None):
        url = f"{self.BASE_URL}{endpoint}"

        response = requests.get(
            url,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "gmx-monitor/0.2",
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        return response.json()

    def get_markets(self):
        return self._get("/markets")

    def get_markets_info(self):
        return self._get("/markets/info")

    def get_glvs(self):
        return self._get("/glvs/")

    def get_glvs_info(self):
        return self._get("/glvs/info")

    def get_apy(self, period="7d"):
        return self._get(
            "/apy",
            params={"period": period},
        )

    def get_performance(self, period="30d", address=None):
        params = {
            "period": period,
        }

        if address:
            params["address"] = address

        return self._get(
            "/performance/annualized",
            params=params,
        )
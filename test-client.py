
import requests

BASE_URL = "http://127.0.0.1:5000"
API_KEY = "123"


def test_get_data():
    print("\nTesting /getData")

    params = {
        "key": API_KEY,
        "start": "2022-11-23 05:28:10",
        "end": "2022-11-23 05:28:15"
    }

    response = requests.get(
        f"{BASE_URL}/getData",
        params=params,
        timeout=15
    )

    print("HTTP Status:", response.status_code)
    print("Response:", response.json())


def test_count_in_polygon():
    print("\nTesting /countInPolygon")

    params = {
        "key": API_KEY,
        "polygon": "-74 42,-75 39,-74 41,-74 42"
    }

    response = requests.get(
        f"{BASE_URL}/countInPolygon",
        params=params,
        timeout=15
    )

    print("HTTP Status:", response.status_code)
    print("Response:", response.json())


def test_avg_speed():
    print("\nTesting /getAvgSpeedByFlight")

    params = {
        "key": API_KEY,
        "start": "2022-11-23 05:00:00",
        "end": "2022-11-23 08:00:00"
    }

    response = requests.get(
        f"{BASE_URL}/getAvgSpeedByFlight",
        params=params,
        timeout=15
    )

    print("HTTP Status:", response.status_code)
    print("Response:", response.json())


if __name__ == "__main__":
    test_get_data()
    test_count_in_polygon()
    test_avg_speed()

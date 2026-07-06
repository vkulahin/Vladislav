#!/usr/bin/env python3
"""Скрипт получения текущей погоды по названию города."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10

WEATHER_CODES = {
    0: "ясно",
    1: "в основном ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "морось: слабая",
    53: "морось: умеренная",
    55: "морось: сильная",
    61: "дождь: слабый",
    63: "дождь: умеренный",
    65: "дождь: сильный",
    71: "снег: слабый",
    73: "снег: умеренный",
    75: "снег: сильный",
    80: "ливень: слабый",
    81: "ливень: умеренный",
    82: "ливень: сильный",
    95: "гроза",
    96: "гроза с градом",
    99: "сильная гроза с градом",
}


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def find_city(name: str) -> dict[str, Any]:
    data = fetch_json(GEOCODING_URL, {"name": name, "count": 1, "language": "ru"})
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Город «{name}» не найден")
    return results[0]


def get_weather(latitude: float, longitude: float) -> dict[str, Any]:
    return fetch_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        },
    )


def describe_weather(code: int) -> str:
    return WEATHER_CODES.get(code, f"код погоды {code}")


def format_weather(city: dict[str, Any], forecast: dict[str, Any]) -> str:
    current = forecast["current"]
    location = city.get("admin1")
    country = city.get("country", "")
    place = city["name"]
    if location:
        place = f"{place}, {location}"
    if country:
        place = f"{place} ({country})"

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    wind = current["wind_speed_10m"]
    condition = describe_weather(current["weather_code"])

    return (
        f"Погода в {place}:\n"
        f"  Температура: {temperature:.1f} °C\n"
        f"  Условия: {condition}\n"
        f"  Влажность: {humidity} %\n"
        f"  Ветер: {wind:.1f} км/ч"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Получить текущую погоду по городу")
    parser.add_argument("city", nargs="?", default="Москва", help="Название города")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        city = find_city(args.city)
        forecast = get_weather(city["latitude"], city["longitude"])
        print(format_weather(city, forecast))
    except requests.RequestException as exc:
        print(f"Ошибка сети: {exc}", file=sys.stderr)
        return 1
    except (ValueError, KeyError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

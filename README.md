## Project Overview

This project uses Python, Flask, and MySQL to build a REST API for querying ADSB aircraft data stored in the Clarkson MySQL database.

The API supports three endpoints and uses database-backed API key authentication and request logging.

## API Endpoints

| Endpoint | Description | Parameters |
|---|---|---|
| `/getData` | Retrieves up to 500 ADS-B records within a date range | `key`, `start`, `end` |
| `/countInPolygon` | Counts ADS-B records within a geographic polygon | `key`, `polygon` |
| `/getAvgSpeedByFlight` | Calculates average ground speed by flight, returning up to 500 groups | `key`, optional `start` and `end` |

All endpoints use the GET method.

## Requirements

- Python 3
- Flask
- PyMySQL
- PyYAML
- Requests

## Installation

Install the required libraries:

```bash
python -m pip install flask pymysql pyyaml requests
```

Copy `config.example.yml` to `config.yml` and provide the database connection settings.


## Database Setup

The project includes `setup_tables.sql`, which defines the authentication and logging tables.

Execute this SQL file using a MySQL client with the required database permissions before running authenticated requests.

## Running the API

Start the Flask server:

```bash
python main.py
```

The API runs locally at `http://127.0.0.1:5000`.

## Testing

With Flask running, open another terminal and execute:

```bash
python test-client.py
```

The test client sends requests to all three endpoints and displays their HTTP status codes and JSON responses.

## API Responses

Every ADSB endpoint returns these fields:

- `code`: `1` for success or `0` for failure
- `msg`: Description of the result
- `req`: Name of the requested endpoint
- `sqltime`: SQL execution time in seconds

Each endpoint also returns either a `results` list or a `count`.

## Current Testing Status

Local Flask routing, parameter checks, and JSON error responses have been tested.

Database-backed authentication, request logging, and successful ADSB SQL queries still need verification because the MySQL server was unreachable during testing.
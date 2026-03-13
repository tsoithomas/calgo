# Bugfix Requirements Document

## Introduction

The Calgo trading bot application is unable to fetch market data due to authentication and rate limiting failures in both configured data sources. The Alpaca API returns 401 Unauthorized errors because the data source configuration is missing the required `api_secret` field, while Yahoo Finance returns 429 Too Many Requests errors due to rate limiting. This prevents the trading bot from obtaining market data for any symbols (AAPL, MSFT, GOOGL), rendering the application non-functional despite successful initialization.

The bug affects the data fetching pipeline where the `MarketDataIngester` attempts to fetch real-time market data through the configured adapters. The Alpaca adapter requires both `api_key` and `api_secret` for authentication, but the current `config.json` only provides `api_key` for data sources. Additionally, the Yahoo Finance fallback fails due to rate limiting, leaving no working data source.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the system attempts to fetch market data from Alpaca with only `api_key` configured in the data source configuration THEN the Alpaca API returns 401 Unauthorized error and the request fails

1.2 WHEN the system falls back to Yahoo Finance after Alpaca authentication failure THEN Yahoo Finance returns 429 Too Many Requests error due to rate limiting and the request fails

1.3 WHEN both data sources fail to fetch market data THEN the trading bot continues running but cannot execute any trading operations due to lack of market data

1.4 WHEN the Alpaca data source configuration lacks the `api_secret` field THEN the AlpacaAdapter is initialized with only `api_key` and `api_secret` parameter receives an empty string default value, causing authentication to fail

### Expected Behavior (Correct)

2.1 WHEN the system attempts to fetch market data from Alpaca with both `api_key` and `api_secret` configured in the data source configuration THEN the Alpaca API SHALL authenticate successfully and return market data

2.2 WHEN the data source configuration includes the `api_secret` field for Alpaca THEN the AlpacaAdapter SHALL be initialized with valid credentials and authenticate successfully

2.3 WHEN Alpaca authentication succeeds THEN the system SHALL fetch market data successfully without needing to fall back to Yahoo Finance

2.4 WHEN the configuration file is updated with the missing `api_secret` field THEN the system SHALL load the complete credentials and initialize the Alpaca adapter correctly

### Unchanged Behavior (Regression Prevention)

3.1 WHEN Yahoo Finance is configured as a data source without `api_secret` (since it doesn't require one) THEN the system SHALL CONTINUE TO initialize the YahooFinanceAdapter correctly with only `api_key`

3.2 WHEN the data source priority configuration specifies Alpaca as priority 1 and Yahoo Finance as priority 2 THEN the system SHALL CONTINUE TO attempt Alpaca first and fall back to Yahoo Finance on failure

3.3 WHEN the MarketDataIngester receives valid market data from any source THEN the system SHALL CONTINUE TO validate the data and proceed with signal generation and trading operations

3.4 WHEN the configuration file contains other fields (broker_config, risk_parameters, etc.) THEN the system SHALL CONTINUE TO load and use those configurations correctly without modification

3.5 WHEN the system initializes with valid data source credentials THEN the system SHALL CONTINUE TO transition through states (INITIALIZING -> READY -> RUNNING) as designed

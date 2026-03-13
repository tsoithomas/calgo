# Data Source Auth Fix Bugfix Design

## Overview

The Alpaca data source configuration in `config/config.json` is missing the required `api_secret` field, causing 401 Unauthorized errors when attempting to fetch market data. The `AlpacaAdapter` requires both `api_key` and `api_secret` for authentication, but the current data source configuration only provides `api_key`. This causes the adapter to be initialized with an empty string for `api_secret` (from the default parameter value in `DataSourceConfig`), resulting in authentication failures.

The fix involves adding the `api_secret` field to the Alpaca data source configuration in `config/config.json`, using the same secret value that's already correctly configured in the `broker_config` section. This is a minimal configuration change that enables proper authentication without modifying any code logic.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when the Alpaca data source configuration lacks the `api_secret` field
- **Property (P)**: The desired behavior - Alpaca API authentication succeeds and returns market data
- **Preservation**: Existing Yahoo Finance configuration, data source priority logic, and broker configuration that must remain unchanged
- **AlpacaAdapter**: The class in `src/data_sources.py` that handles Alpaca API requests and requires both `api_key` and `api_secret` for authentication
- **DataSourceConfig**: The dataclass in `src/config_models.py` that defines data source configuration structure with `api_secret` as an optional field with empty string default
- **MarketDataIngester**: The component that uses data source adapters to fetch market data, attempting sources in priority order

## Bug Details

### Bug Condition

The bug manifests when the system attempts to initialize the AlpacaAdapter using a DataSourceConfig that lacks the `api_secret` field. The `ConfigManager` loads the data source configuration from `config/config.json`, and since `api_secret` is not present in the Alpaca data source entry, the `DataSourceConfig` dataclass uses its default value of empty string. The AlpacaAdapter is then initialized with valid `api_key` but empty `api_secret`, causing all API requests to fail with 401 Unauthorized.

**Formal Specification:**
```
FUNCTION isBugCondition(config)
  INPUT: config of type DataSourceConfig
  OUTPUT: boolean
  
  RETURN config.source == DataSource.ALPACA
         AND config.api_key != ""
         AND config.api_secret == ""
         AND alpacaAdapterInitialized(config)
END FUNCTION
```

### Examples

- **Alpaca historical data fetch**: System attempts to fetch historical bars for AAPL from Alpaca, API returns 401 Unauthorized due to missing api_secret in authentication headers
- **Alpaca real-time data fetch**: System attempts to fetch latest bar for MSFT from Alpaca, API returns 401 Unauthorized due to incomplete credentials
- **Data source fallback**: After Alpaca fails with 401, system falls back to Yahoo Finance which then fails with 429 rate limiting, leaving no working data source
- **Edge case - broker operations**: Broker operations using `broker_config` continue to work correctly because that section includes both api_key and api_secret

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Yahoo Finance data source configuration must continue to work with only `api_key` field (no `api_secret` required)
- Data source priority logic must continue to attempt Alpaca first (priority 1) and Yahoo Finance second (priority 2)
- Broker configuration in `broker_config` section must remain unchanged and continue to work for trading operations
- Risk parameters, active models, trading schedule, and logging configuration must remain unchanged
- Configuration loading logic in `ConfigManager` must continue to parse all configuration sections correctly

**Scope:**
All configuration fields and data sources that do NOT involve the Alpaca data source `api_secret` should be completely unaffected by this fix. This includes:
- Yahoo Finance data source configuration (no api_secret needed)
- Broker configuration (already has api_secret)
- All other configuration sections (risk_parameters, active_models, trading_schedule, logging_config)
- Configuration validation and loading logic

## Hypothesized Root Cause

Based on the bug description and code analysis, the root cause is:

1. **Missing Configuration Field**: The `config/config.json` file's `data_sources` array entry for Alpaca only includes `source`, `api_key`, and `priority` fields, but omits the required `api_secret` field
   - The `broker_config` section correctly includes both `api_key` and `api_secret`
   - The data source configuration was likely created by copying only the visible fields without realizing `api_secret` was required

2. **Default Value Masking**: The `DataSourceConfig` dataclass defines `api_secret` with a default value of empty string (`api_secret: str = ""`), which allows the configuration to load successfully without the field present
   - This default value masks the missing configuration at load time
   - The error only surfaces when the AlpacaAdapter attempts API authentication

3. **Inconsistent Configuration Structure**: The configuration file has the correct `api_secret` value in `broker_config` but not in `data_sources`, suggesting the field was overlooked when configuring data sources
   - Both sections use the same Alpaca API credentials
   - The secret should be present in both locations for their respective purposes

## Correctness Properties

Property 1: Bug Condition - Alpaca Authentication Success

_For any_ data source configuration where the source is Alpaca and both `api_key` and `api_secret` are provided as non-empty strings, the AlpacaAdapter SHALL successfully authenticate with the Alpaca API and fetch market data without 401 Unauthorized errors.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-Alpaca Configuration Unchanged

_For any_ configuration field that is NOT the Alpaca data source `api_secret` field (including Yahoo Finance configuration, broker configuration, risk parameters, and all other sections), the configuration loading and system behavior SHALL produce exactly the same result as before the fix, preserving all existing functionality.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

The fix is a minimal configuration change to add the missing field.

**File**: `config/config.json`

**Section**: `data_sources` array, first element (Alpaca configuration)

**Specific Changes**:
1. **Add api_secret field**: Add the `api_secret` field to the Alpaca data source configuration object
   - Use the same secret value from `broker_config.api_secret`: `"HxMG9Lnf2atktpCP4DFbo7jbkVJ79dDGUYiZH6whdgXz"`
   - Place the field after `api_key` and before `priority` for consistency

2. **Verify field placement**: Ensure the JSON structure remains valid with proper comma placement

3. **No code changes required**: The `DataSourceConfig` dataclass already supports the `api_secret` field, and the `AlpacaAdapter` already expects it in its constructor

**Before**:
```json
{
  "source": "alpaca",
  "api_key": "PKQ7YTGYJWIEY6G5AGMTDHJUQ3",
  "priority": 1
}
```

**After**:
```json
{
  "source": "alpaca",
  "api_key": "PKQ7YTGYJWIEY6G5AGMTDHJUQ3",
  "api_secret": "HxMG9Lnf2atktpCP4DFbo7jbkVJ79dDGUYiZH6whdgXz",
  "priority": 1
}
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code by attempting Alpaca API calls with incomplete credentials, then verify the fix works correctly by confirming successful authentication and preserving all other configuration behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the missing `api_secret` field causes 401 Unauthorized errors from the Alpaca API.

**Test Plan**: Write tests that load the unfixed configuration, initialize the AlpacaAdapter with the incomplete credentials, and attempt to fetch market data. Run these tests on the UNFIXED configuration to observe 401 authentication failures and confirm the root cause.

**Test Cases**:
1. **Alpaca Historical Data Fetch Test**: Load unfixed config, initialize AlpacaAdapter, attempt to fetch historical bars for AAPL (will fail with 401 on unfixed config)
2. **Alpaca Real-time Data Fetch Test**: Load unfixed config, initialize AlpacaAdapter, attempt to fetch latest bar for MSFT (will fail with 401 on unfixed config)
3. **Adapter Initialization Test**: Load unfixed config, verify that AlpacaAdapter is initialized with empty string for api_secret (will show incomplete credentials on unfixed config)
4. **Authentication Header Test**: Load unfixed config, inspect the headers sent to Alpaca API, verify that APCA-API-SECRET-KEY header is empty or invalid (will show missing secret on unfixed config)

**Expected Counterexamples**:
- Alpaca API returns 401 Unauthorized with message indicating authentication failure
- AlpacaAdapter headers contain empty or invalid APCA-API-SECRET-KEY value
- Possible causes: missing api_secret field in config, default empty string value used, incomplete credentials passed to adapter

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (Alpaca data source configuration), the fixed configuration produces the expected behavior (successful authentication).

**Pseudocode:**
```
FOR ALL config WHERE isBugCondition(config) DO
  config_fixed := addApiSecretField(config)
  adapter := AlpacaAdapter(config_fixed.api_key, config_fixed.api_secret)
  result := adapter.fetch_realtime("AAPL")
  ASSERT result.is_ok() AND NOT result.is_err_with_401()
END FOR
```

### Preservation Checking

**Goal**: Verify that for all configuration fields where the bug condition does NOT hold (all non-Alpaca-api_secret fields), the fixed configuration produces the same result as the original configuration.

**Pseudocode:**
```
FOR ALL config_field WHERE NOT isAlpacaApiSecretField(config_field) DO
  ASSERT loadConfig_original(config_field) = loadConfig_fixed(config_field)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the configuration space
- It catches edge cases where configuration loading might be affected by the JSON structure change
- It provides strong guarantees that all other configuration sections remain unchanged

**Test Plan**: Observe behavior on UNFIXED configuration first for Yahoo Finance, broker config, and other sections, then write property-based tests capturing that those sections load identically after the fix.

**Test Cases**:
1. **Yahoo Finance Configuration Preservation**: Verify that Yahoo Finance data source loads with same api_key and priority after fix
2. **Broker Configuration Preservation**: Verify that broker_config section loads identically (already has api_secret, should be unchanged)
3. **Risk Parameters Preservation**: Verify that risk_parameters section loads with same values after fix
4. **Trading Schedule Preservation**: Verify that trading_schedule section loads with same values after fix
5. **Data Source Priority Preservation**: Verify that data source priority ordering (Alpaca first, Yahoo second) remains unchanged after fix

### Unit Tests

- Test configuration loading with fixed config file, verify Alpaca data source has non-empty api_secret
- Test AlpacaAdapter initialization with complete credentials, verify headers contain valid APCA-API-SECRET-KEY
- Test Alpaca API authentication with valid credentials, verify 200 OK response instead of 401
- Test that Yahoo Finance configuration remains unchanged after fix
- Test that broker configuration remains unchanged after fix

### Property-Based Tests

- Generate random symbols and verify Alpaca adapter can fetch data successfully with fixed credentials
- Generate random date ranges and verify Alpaca historical data fetching works with fixed credentials
- Verify that all non-Alpaca configuration sections load identically before and after fix across many test runs
- Test that configuration validation logic continues to work correctly with the added field

### Integration Tests

- Test full data ingestion flow: load fixed config, initialize adapters, fetch market data from Alpaca, verify success
- Test data source fallback behavior: if Alpaca fails for non-auth reasons, verify Yahoo Finance fallback still works
- Test that trading bot can initialize and transition to RUNNING state with fixed configuration
- Test that broker operations continue to work correctly (using broker_config credentials) after data source fix

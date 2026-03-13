# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Alpaca Authentication Failure with Missing api_secret
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to the concrete failing case - Alpaca data source configuration missing api_secret field
  - Test that AlpacaAdapter initialized with api_key but empty api_secret fails authentication with 401 Unauthorized
  - Test implementation details from Bug Condition in design: config.source == DataSource.ALPACA AND config.api_key != "" AND config.api_secret == ""
  - The test assertions should match the Expected Behavior Properties from design: successful authentication and market data fetch
  - Run test on UNFIXED code (config.json without api_secret field in Alpaca data source)
  - **EXPECTED OUTCOME**: Test FAILS with 401 Unauthorized error (this is correct - it proves the bug exists)
  - Document counterexamples found: Alpaca API returns 401 for fetch_realtime("AAPL"), fetch_historical("MSFT", dates), etc.
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.4, 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy configuration sections
  - Observe: Yahoo Finance data source loads with api_key="not_required_for_yahoo", priority=2
  - Observe: broker_config section loads with api_key, api_secret, base_url unchanged
  - Observe: risk_parameters, active_models, trading_schedule, logging_config sections load correctly
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Test that Yahoo Finance configuration (api_key, priority) remains unchanged after fix
  - Test that broker_config section (api_key, api_secret, base_url) remains unchanged after fix
  - Test that risk_parameters section loads identically after fix
  - Test that trading_schedule section loads identically after fix
  - Test that logging_config section loads identically after fix
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for missing api_secret in Alpaca data source configuration

  - [x] 3.1 Implement the configuration fix
    - Open config/config.json file
    - Locate the data_sources array, first element (Alpaca configuration)
    - Add "api_secret" field with value "HxMG9Lnf2atktpCP4DFbo7jbkVJ79dDGUYiZH6whdgXz" (same as broker_config.api_secret)
    - Place the field after "api_key" and before "priority" for consistency
    - Ensure JSON structure remains valid with proper comma placement
    - Verify no other configuration sections are modified
    - _Bug_Condition: isBugCondition(config) where config.source == DataSource.ALPACA AND config.api_key != "" AND config.api_secret == ""_
    - _Expected_Behavior: AlpacaAdapter successfully authenticates with Alpaca API and fetches market data without 401 errors (from design Property 1)_
    - _Preservation: Yahoo Finance configuration, broker configuration, risk parameters, trading schedule, and logging configuration remain unchanged (from design Property 2)_
    - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Alpaca Authentication Success
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify AlpacaAdapter can fetch real-time data for AAPL without 401 errors
    - Verify AlpacaAdapter can fetch historical data for MSFT without 401 errors
    - Verify AlpacaAdapter headers contain valid APCA-API-SECRET-KEY value
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Alpaca Configuration Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm Yahoo Finance configuration loads identically
    - Confirm broker_config section loads identically
    - Confirm risk_parameters section loads identically
    - Confirm trading_schedule section loads identically
    - Confirm logging_config section loads identically
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

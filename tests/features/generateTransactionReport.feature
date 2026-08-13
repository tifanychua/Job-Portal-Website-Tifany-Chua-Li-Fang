Feature: Generate Transaction Report

  Scenario: View transaction report page
    Given the admin is logged into the system
    When the admin opens the transaction report page
    Then the system should display the transaction report page

  Scenario: Generate transaction report
    Given the admin is viewing the transaction report page
    When the admin generates the transaction report
    Then the system should display the transaction report with employer payment information

  Scenario: Generate report using selected criteria
    Given the admin is viewing the transaction report page
    When the admin selects a payment status and date range
    Then the system should display only transactions that match the selected criteria

  Scenario: View report summary
    Given the admin has generated a transaction report
    When the report summary is displayed
    Then the system should show total transactions successful payments pending payments failed payments and total revenue

  Scenario: Download transaction report
    Given the admin has generated a transaction report
    When the admin downloads the transaction report
    Then the system should generate a PDF transaction report
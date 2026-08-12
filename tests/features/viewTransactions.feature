Feature: View Transactions
  As an Admin
  I want to view and filter employer transactions
  So that I can monitor payment and subscription activities.

  Scenario: Admin views the transaction management page
    Given the admin is logged into the system
    When the admin opens the transaction management page
    Then the system should display the transaction management page

  Scenario: Admin views transaction records
    Given the admin is viewing the transaction management page
    When the transaction records are loaded
    Then the system should display the transaction records

  Scenario: Admin views transaction information
    Given the admin is viewing the transaction management page
    When the transaction records are loaded
    Then each transaction should display the required transaction information

  Scenario: Admin views transaction payment status
    Given the admin is viewing the transaction management page
    When the transaction records are loaded
    Then the transaction payment status should be displayed

  Scenario: Admin views transaction summary
    Given the admin is viewing the transaction management page
    When the transaction records are loaded
    Then the system should display the transaction summary

  Scenario: Admin searches transaction by transaction ID
    Given the admin is viewing the transaction management page
    When the admin searches using a transaction ID
    Then the matching transaction should be displayed

  Scenario: Admin searches transaction by company name
    Given the admin is viewing the transaction management page
    When the admin searches using a company name
    Then the matching company transactions should be displayed

  Scenario: Admin searches transaction using lowercase keyword
    Given the admin is viewing the transaction management page
    When the admin searches using a lowercase keyword
    Then the search should be case insensitive

  Scenario: Admin searches transaction using partial keyword
    Given the admin is viewing the transaction management page
    When the admin searches using a partial keyword
    Then transactions containing the keyword should be displayed

  Scenario: Admin searches for a transaction that does not exist
    Given the admin is viewing the transaction management page
    When the admin searches using a non existing transaction
    Then the system should return no matching transactions without an error

  Scenario: Admin leaves transaction search empty
    Given the admin is viewing the transaction management page
    When the admin searches without entering a keyword
    Then all available transactions should remain accessible

  Scenario: Admin filters completed transactions
    Given the admin is viewing the transaction management page
    When the admin selects the completed status
    Then only completed transactions should match the status filter

  Scenario: Admin filters pending transactions
    Given the admin is viewing the transaction management page
    When the admin selects the pending status
    Then only pending transactions should match the status filter

  Scenario: Admin filters failed transactions
    Given the admin is viewing the transaction management page
    When the admin selects the failed status
    Then only failed transactions should match the status filter

  Scenario: Admin removes the status filter
    Given the admin is viewing the transaction management page
    When the admin selects all status
    Then transactions of all statuses should be available

  Scenario: Invalid transaction status is supplied
    Given the admin is viewing the transaction management page
    When an invalid transaction status is supplied
    Then the system should handle the invalid status without crashing

  Scenario: Transaction date filter is available
    Given the admin is viewing the transaction management page
    When the admin opens the date filter
    Then the system should provide from date and to date filters

  Scenario: Admin filters transactions using a valid date range
    Given the admin is viewing the transaction management page
    When the admin selects a valid transaction date range
    Then the date filter controls should support the selected range

  Scenario: Admin cannot select a future transaction date
    Given the admin is viewing the transaction management page
    When the transaction date filter is displayed
    Then future transaction dates should not be allowed

  Scenario: Admin enters from date later than to date
    Given the admin is viewing the transaction management page
    When the from date is later than the to date
    Then the invalid transaction date range should be prevented

  Scenario: Admin clears transaction date filter
    Given the admin is viewing the transaction management page
    When the admin clears the transaction date filter
    Then the transaction date filter should return to its default state

  Scenario: Transaction completed date is available
    Given a transaction contains both created date and completed date
    When the transaction date is determined
    Then the completed date should be used as the transaction date

  Scenario: Transaction completed date is missing
    Given a transaction does not contain a completed date
    When the transaction date is determined
    Then the created date should be used as the transaction date

  Scenario: Transaction contains no date
    Given a transaction does not contain a created date or completed date
    When the transaction management page processes the transaction
    Then the system should handle the missing transaction date without crashing

  Scenario: Transaction references a valid company
    Given a transaction contains a valid company ID
    When the transaction records are loaded
    Then the corresponding company information should be associated with the transaction

  Scenario: Transaction references a company that does not exist
    Given a transaction contains an unknown company ID
    When the transaction records are loaded
    Then the system should handle the missing company without crashing

  Scenario: Transaction contains no company ID
    Given a transaction does not contain a company ID
    When the transaction records are loaded
    Then the system should handle the missing company ID without crashing

  Scenario: Completed current year payment contributes to revenue
    Given a completed transaction belongs to the current year
    When the transaction summary is calculated
    Then the completed payment amount should contribute to total revenue

  Scenario: Pending payment does not contribute to revenue
    Given a pending transaction exists
    When the transaction summary is calculated
    Then the pending payment amount should not contribute to total revenue

  Scenario: Failed payment does not contribute to revenue
    Given a failed transaction exists
    When the transaction summary is calculated
    Then the failed payment amount should not contribute to total revenue

  Scenario: Previous year payment does not contribute to current year revenue
    Given a completed transaction belongs to the previous year
    When the transaction summary is calculated
    Then the previous year payment should not contribute to current year revenue

  Scenario: Transaction has missing amount
    Given a transaction does not contain an amount
    When the transaction summary is calculated
    Then the missing amount should be treated as zero

  Scenario: Transactions are sorted by newest date
    Given multiple transactions exist with different dates
    When the transaction records are loaded
    Then the newest transaction should be displayed before older transactions

  Scenario: Fewer than twenty transactions are available
    Given fewer than twenty transactions exist
    When the admin views the first transaction page
    Then only one transaction page should be required

  Scenario: Exactly twenty transactions are available
    Given exactly twenty transactions exist
    When the admin views the transaction list
    Then only one transaction page should be required

  Scenario: Twenty one transactions are available
    Given twenty one transactions exist
    When the admin views the transaction list
    Then two transaction pages should be required

  Scenario: Admin opens the second transaction page
    Given more than twenty transactions exist
    When the admin opens transaction page two
    Then the remaining transactions should be displayed

  Scenario: Admin requests page zero
    Given transaction records are available
    When transaction page zero is requested
    Then the system should use transaction page one

  Scenario: Admin requests a negative page
    Given transaction records are available
    When a negative transaction page is requested
    Then the system should use transaction page one

  Scenario: Admin requests a page greater than the final page
    Given transaction records are available
    When a transaction page greater than the final page is requested
    Then the system should use the final transaction page

  Scenario: No transactions exist
    Given no transaction records exist
    When the admin views the transaction management page
    Then the system should handle the empty transaction list successfully
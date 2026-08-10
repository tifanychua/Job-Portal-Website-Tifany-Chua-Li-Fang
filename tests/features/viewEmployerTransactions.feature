Feature: View Employer Transactions
  As an Employer
  I want to view and filter my transaction history
  So that I can monitor my subscription payments and billing records.

  Scenario: Employer opens transaction history page
    Given an employer company exists
    When the employer opens the transaction history page
    Then the transaction history page should be displayed

  Scenario: Only current company transactions are displayed
    Given payments belonging to different companies exist
    When the employer opens the transaction history page
    Then only the current company transactions should be displayed

  Scenario: Transaction information is displayed
    Given an employer company has payment transactions
    When the employer opens the transaction history page
    Then each transaction should contain the required transaction information

  Scenario: Completed transaction contributes to total spent
    Given completed pending and failed payments exist
    When the employer opens the transaction history page
    Then only completed payment amounts should contribute to total spent

  Scenario: Transaction status counts are calculated
    Given completed pending and failed payments exist
    When the employer opens the transaction history page
    Then the completed pending and failed counts should be correct

  Scenario: Employer searches by transaction ID
    Given an employer company has payment transactions
    When the employer searches using a transaction ID
    Then only the matching transaction should be displayed

  Scenario: Employer searches by plan name
    Given an employer company has payment transactions
    When the employer searches using a plan name
    Then transactions matching the plan should be displayed

  Scenario: Employer searches by payment method
    Given an employer company has payment transactions
    When the employer searches using the payment method
    Then transactions matching the payment method should be displayed

  Scenario: Search is case insensitive
    Given an employer company has payment transactions
    When the employer searches using lowercase text
    Then the transaction search should be case insensitive

  Scenario: Search ignores surrounding spaces
    Given an employer company has payment transactions
    When the employer searches with surrounding spaces
    Then the surrounding search spaces should be ignored

  Scenario: Search returns no transactions
    Given an employer company has payment transactions
    When the employer searches for a transaction that does not exist
    Then the transaction result should be empty

  Scenario: Empty search displays all transactions
    Given an employer company has payment transactions
    When the employer searches without a keyword
    Then all current company transactions should remain available

  Scenario: Employer filters completed transactions
    Given completed pending and failed payments exist
    When the employer filters by completed status
    Then only completed transactions should be displayed

  Scenario: Employer filters pending transactions
    Given completed pending and failed payments exist
    When the employer filters by pending status
    Then only pending transactions should be displayed

  Scenario: Employer filters failed transactions
    Given completed pending and failed payments exist
    When the employer filters by failed status
    Then only failed transactions should be displayed

  Scenario: Status filter is case insensitive
    Given completed pending and failed payments exist
    When the employer filters using lowercase completed status
    Then the status filter should be case insensitive

  Scenario: Invalid status returns no transactions
    Given completed pending and failed payments exist
    When the employer filters using an invalid status
    Then no transactions should match the invalid status

  Scenario: Search and status filter work together
    Given completed pending and failed payments exist
    When the employer searches and filters by status
    Then only transactions matching both criteria should be displayed

  Scenario: Completed date is preferred
    Given a transaction has both completed and created dates
    When the employer opens the transaction history page
    Then the completed date should be used

  Scenario: Created date is fallback
    Given a transaction has only a created date
    When the employer opens the transaction history page
    Then the created date should be used

  Scenario: Missing transaction date is handled
    Given a transaction has no completed or created date
    When the employer opens the transaction history page
    Then the missing transaction date should be represented safely

  Scenario: Missing package is handled
    Given a transaction has no package
    When the employer opens the transaction history page
    Then the missing package should be represented with a dash

  Scenario: Missing payment method is handled
    Given a transaction has no payment method
    When the employer opens the transaction history page
    Then the missing payment method should be represented with a dash

  Scenario: Missing amount is handled
    Given a transaction has no amount
    When the employer opens the transaction history page
    Then the missing amount should default to zero

  Scenario: Missing credits are handled
    Given a transaction has no credits
    When the employer opens the transaction history page
    Then the missing credits should default to zero

  Scenario: Transactions are sorted newest first
    Given transactions exist with different payment dates
    When the employer opens the transaction history page
    Then the newest transaction should be displayed first

  Scenario: Fewer than twenty transactions use one page
    Given fewer than twenty transactions exist
    When the employer opens the transaction history page
    Then only one transaction page should be required

  Scenario: Exactly twenty transactions use one page
    Given exactly twenty transactions exist
    When the employer opens the transaction history page
    Then only one transaction page should be required

  Scenario: Twenty one transactions use two pages
    Given twenty one transactions exist
    When the employer opens the transaction history page
    Then two transaction pages should be required

  Scenario: Second transaction page displays remaining records
    Given twenty five transactions exist
    When the employer opens transaction page two
    Then five transactions should be displayed on page two

  Scenario: Page zero is corrected
    Given an employer company has payment transactions
    When transaction page zero is requested
    Then the current transaction page should be one

  Scenario: Negative page is corrected
    Given an employer company has payment transactions
    When a negative transaction page is requested
    Then the current transaction page should be one

  Scenario: Page above final page is corrected
    Given twenty five transactions exist
    When a transaction page above the final page is requested
    Then the final transaction page should be used

  Scenario: Company has no transactions
    Given the employer company has no payment transactions
    When the employer opens the transaction history page
    Then the transaction list should be empty

  Scenario: Current employer company does not exist
    Given the current employer company does not exist
    When the employer opens the transaction history page expecting an error
    Then company not found should be returned

  Scenario: Completed transaction has receipt link
    Given an employer company has payment transactions
    When the transaction history template is inspected
    Then completed transactions should provide a receipt link

  Scenario: Search and status controls exist
    Given the transaction history template is available
    When the transaction history template is inspected
    Then search and status filter controls should exist

  Scenario: Empty transaction state exists
    Given the transaction history template is available
    When the transaction history template is inspected
    Then the no transactions message should exist

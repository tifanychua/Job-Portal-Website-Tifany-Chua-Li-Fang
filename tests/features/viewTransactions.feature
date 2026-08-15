Feature: View Employer Payment Transactions

  Scenario: View list of employer payment transactions
    Given the admin is logged into the admin dashboard
    When the admin accesses the payment transaction management section
    Then the system should display a list of all employer payment transactions

  Scenario: View payment transaction details
    Given the admin is viewing the employer payment transaction list
    When the admin selects a specific transaction
    Then the system should display the transaction details including employer information payment date purchased credit package payment amount and payment status

  Scenario: Filter employer payment transactions
    Given the admin is viewing the payment transaction management section
    When the admin applies payment transaction filters
    Then the system should display only transactions that match the selected criteria

  Scenario: View unsuccessful payment transactions
    Given there are failed or pending employer payment transactions
    When the admin accesses the payment transaction management section
    Then the system should display the payment transactions with their respective statuses for monitoring
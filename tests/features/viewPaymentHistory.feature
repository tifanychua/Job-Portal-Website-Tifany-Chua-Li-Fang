Feature: View Payment History

  Scenario: View payment transaction history
    Given the employer has completed one or more payment transactions
    When the employer accesses the payment history page
    Then the system should display a list of the employer's previous payment transactions

  Scenario: View payment transaction details
    Given the employer has a recorded payment transaction
    When the employer selects a transaction from the payment history
    Then the system should display details including transaction date payment amount payment status and purchased credit package

  Scenario: Employer has no payment history
    Given the employer has not completed any payment transactions
    When the employer accesses the payment history page
    Then the system should display that no payment records are available
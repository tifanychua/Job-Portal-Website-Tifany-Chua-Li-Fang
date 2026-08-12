Feature: View Employer Credit
  As an Employer
  I want to view my job posting credits and subscription information
  So that I can monitor my credit usage and recent subscription payments.

  Scenario: Employer opens credit page
    Given an employer company exists
    When the employer opens the credit page
    Then the employer credit page should be displayed

  Scenario: Credit summary is displayed
    Given an employer company exists
    When the employer opens the credit page
    Then the total available used and expired credits should be correct

  Scenario: Used credit field exists
    Given the company stores a used credit value
    When the employer opens the credit page
    Then the stored used credit should be displayed

  Scenario: Used credit field is missing
    Given the company does not store a used credit value
    When the employer opens the credit page
    Then used credit should be calculated from total and available credit

  Scenario: Missing credit values are handled
    Given the company does not contain credit values
    When the employer opens the credit page
    Then all missing credit values should default to zero

  Scenario: Current starter subscription is displayed
    Given the company has a starter subscription
    When the employer opens the credit page
    Then the current subscription should be Starter Pack

  Scenario: Current business subscription is displayed
    Given the company has a business subscription
    When the employer opens the credit page
    Then the current subscription should be Business Pack

  Scenario: Current enterprise subscription is displayed
    Given the company has an enterprise subscription
    When the employer opens the credit page
    Then the current subscription should be Enterprise Pack

  Scenario: Subscription plan is case insensitive
    Given the company subscription plan is stored using uppercase letters
    When the employer opens the credit page
    Then the subscription plan should still be recognised correctly

  Scenario: Company has no active subscription
    Given the company does not have a subscription plan
    When the employer opens the credit page
    Then the current subscription name should be empty

  Scenario: Subscription end date is formatted
    Given the company has a subscription end date
    When the employer opens the credit page
    Then the subscription end date should be formatted correctly

  Scenario: Subscription end date is missing
    Given the company does not have a subscription end date
    When the employer opens the credit page
    Then the subscription end date should be empty

  Scenario: Subscription is scheduled for cancellation
    Given the company subscription is scheduled for cancellation
    When the employer opens the credit page
    Then the cancellation flag should be true

  Scenario: Subscription is not scheduled for cancellation
    Given the company subscription is active and not cancelling
    When the employer opens the credit page
    Then the cancellation flag should be false

  Scenario: Payment history is loaded
    Given the company has payment records
    When the employer opens the credit page
    Then the payment history should be displayed

  Scenario: Completed date is used for payment history
    Given a payment contains completed and created dates
    When the employer opens the credit page
    Then the completed date should be used as the payment history date

  Scenario: Created date is used when completed date is missing
    Given a payment does not contain a completed date
    When the employer opens the credit page
    Then the created date should be used as the payment history date

  Scenario: Payment date is missing
    Given a payment does not contain a completed or created date
    When the employer opens the credit page
    Then the payment history date should be represented safely

  Scenario: Payment amount is converted to float
    Given a payment amount is stored as a string
    When the employer opens the credit page
    Then the payment amount should be converted correctly

  Scenario: Missing payment amount is handled
    Given a payment does not contain an amount
    When the employer opens the credit page
    Then the missing payment amount should default to zero

  Scenario: Missing package name is handled
    Given a payment does not contain a package
    When the employer opens the credit page
    Then the missing package should be represented with a dash

  Scenario: Payments are sorted newest first
    Given multiple payment records exist with different dates
    When the employer opens the credit page
    Then the newest payment should be displayed first

  Scenario: Only latest five payments are displayed
    Given more than five payment records exist
    When the employer opens the credit page
    Then only five recent payments should be displayed

  Scenario: More payment history is available
    Given more than five payment records exist
    When the employer opens the credit page
    Then the has more payment history flag should be true

  Scenario: Five payment records exist
    Given exactly five payment records exist
    When the employer opens the credit page
    Then the has more payment history flag should be false

  Scenario: No payment history exists
    Given the company has no payment records
    When the employer opens the credit page
    Then the recent payment history should be empty

  Scenario: Payment from another company is excluded
    Given payments belonging to different companies exist
    When the employer opens the credit page
    Then only the current company payments should be displayed

  Scenario: Company does not exist
    Given the current employer company does not exist
    When the employer opens the credit page expecting an error
    Then the system should return company not found
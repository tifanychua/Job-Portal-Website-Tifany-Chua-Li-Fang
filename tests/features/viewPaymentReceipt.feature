Feature: View Payment Receipt

  Scenario: Employer opens a valid payment receipt
    Given a completed card payment exists for the current company
    When the employer opens the payment receipt
    Then the payment receipt page should be displayed

  Scenario: Receipt displays the correct payment information
    Given a completed card payment exists for the current company
    When the employer opens the payment receipt
    Then the receipt should contain the correct company package credits payment method status and amount

  Scenario: Receipt displays the correct receipt number
    Given a completed card payment exists for the current company
    When the employer opens the payment receipt
    Then the receipt number should match the payment ID

  Scenario: Completed payment date is formatted
    Given a completed card payment exists for the current company
    When the employer opens the payment receipt
    Then the purchase date should be formatted correctly

  Scenario: Missing completed date is handled
    Given a completed card payment has no completed date
    When the employer opens the payment receipt
    Then the purchase date should be represented with a dash

  Scenario: Missing payment method defaults to Card
    Given a completed payment has no payment method
    When the employer opens the payment receipt
    Then the payment method should default to Card

  Scenario: Receipt does not exist
    Given the requested receipt does not exist
    When the employer opens the payment receipt expecting an error
    Then receipt not found should be returned

  Scenario: Employer cannot view another company's receipt
    Given a completed payment belongs to another company
    When the employer opens the payment receipt expecting an error
    Then receipt access should be denied

  Scenario: Pending payment cannot be viewed as a receipt
    Given a pending card payment exists for the current company
    When the employer opens the payment receipt expecting an error
    Then completed payment receipt should be required

  Scenario: Failed payment cannot be viewed as a receipt
    Given a failed card payment exists for the current company
    When the employer opens the payment receipt expecting an error
    Then completed payment receipt should be required

  Scenario: Company record does not exist
    Given a completed card payment exists for the current company
    And the current company record does not exist
    When the employer opens the payment receipt expecting an error
    Then company not found should be returned
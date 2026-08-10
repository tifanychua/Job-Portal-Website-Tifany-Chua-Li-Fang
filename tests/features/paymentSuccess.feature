Feature: Stripe Payment Success
  As an Employer
  I want to view the Stripe payment success page
  So that I can confirm my subscription payment.

  Scenario: Payment success page uses Firestore payment
    Given the current company exists with the matching Stripe customer
    And Stripe returns a valid checkout session
    And a completed Firestore payment exists
    When the employer opens the payment success page
    Then the payment success page should be displayed
    And the saved Firestore payment should be used

  Scenario: Payment success uses fallback when webhook payment is not ready
    Given the current company exists with the matching Stripe customer
    And Stripe returns a valid checkout session
    And no Firestore payment exists
    When the employer opens the payment success page
    Then a fallback card payment should be displayed

  Scenario: Invoice amount is converted from cents
    Given the current company exists with the matching Stripe customer
    And Stripe returns a valid checkout session with an amount paid
    And no Firestore payment exists
    When the employer opens the payment success page
    Then the fallback payment amount should be converted from cents

  Scenario: Firestore completed date is formatted
    Given the current company exists with the matching Stripe customer
    And Stripe returns a valid checkout session
    And a Firestore payment with completed date exists
    When the employer opens the payment success page
    Then the completed payment date should be formatted for display

  Scenario: Stripe session belongs to another customer
    Given the current company exists with a different Stripe customer
    And Stripe returns a valid checkout session
    When the employer opens the payment success page expecting an error
    Then access to the payment success page should be denied

  Scenario: Current company does not exist
    Given the current company does not exist
    And Stripe returns a valid checkout session
    When the employer opens the payment success page expecting an error
    Then company not found should be returned

  Scenario: Stripe session retrieval fails
    Given Stripe checkout session retrieval fails
    When the employer opens the payment success page expecting an error
    Then a Stripe payment success error should be returned

  Scenario: String subscription ID is retrieved
    Given the current company exists with the matching Stripe customer
    And Stripe returns a session containing a subscription ID
    And no Firestore payment exists
    When the employer opens the payment success page
    Then the subscription should be retrieved and the plan should be displayed

  Scenario: Order ID falls back to session ID
    Given the current company exists with the matching Stripe customer
    And Stripe returns a valid checkout session without invoice
    When the employer opens the payment success page
    Then the order ID should use the session ID

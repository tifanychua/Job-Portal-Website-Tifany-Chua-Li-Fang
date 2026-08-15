Feature: Payment Confirmation

  Scenario: Receive payment confirmation after successful transaction
    Given the employer has completed a payment transaction successfully
    When the payment is confirmed by the system
    Then the system should display a payment confirmation message to the employer

  Scenario: View payment receipt details
    Given the employer has received a payment confirmation
    When the employer views the confirmation details
    Then the system should display transaction information including payment amount transaction date and purchased credit package

  Scenario: Access payment history
    Given the employer has completed one or more successful transactions
    When the employer views payment history
    Then the system should display a list of completed payment transactions
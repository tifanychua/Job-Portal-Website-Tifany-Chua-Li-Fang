Feature: Forgot Password
As a User
I want to reset my password through email verification
So that I can securely recover access to my account when I forget my password

  Scenario: Request password reset
    Given the user is on the Forgot Password page
    When the user enters a registered email address and submits the request
    Then the system should send a password reset email containing a verification link

  Scenario: Enter an unregistered email address
    Given the user is on the Forgot Password page
    When the user enters an email address that is not registered
    Then the system should display the same confirmation message
    And no information about whether the email exists should be revealed

  Scenario: Reset password using a valid verification link
    Given the user has received the password reset email
    When the user opens the valid verification link and enters a new password
    Then the system should update the user's password successfully
    And redirect the user to the login page

  Scenario: Reset password with an expired or invalid verification link
    Given the password reset verification link is expired or invalid
    When the user attempts to reset the password
    Then the system should display an "Invalid or expired verification link" message
    And the password should not be updated
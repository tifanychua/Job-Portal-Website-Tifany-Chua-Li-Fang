Feature: Employer Delete Notifications
  As an employer
  I want to delete unwanted notifications
  So that my notification list does not become cluttered.

  Scenario: Delete a notification successfully
    Given the employer is viewing the notification list
    And the notification belongs to the employer
    When the employer selects the delete option for the notification
    And confirms the deletion
    Then the system should remove the notification from the notification list
    And display a notification-deleted success message

  Scenario: Cancel notification deletion
    Given the employer has selected the delete option for a notification
    And the confirmation message is displayed
    When the employer cancels the deletion
    Then the system should not delete the notification
    And the notification should remain in the notification list

  Scenario: Deleted notification remains deleted after refresh
    Given the employer has successfully deleted a notification
    When the employer refreshes or revisits the notification page
    Then the deleted notification should not appear in the notification list

  Scenario: Delete an unread notification
    Given the employer has an unread notification
    When the employer deletes the unread notification
    Then the notification should be removed from the notification list
    And the unread notification count should decrease by one

  Scenario: Prevent deletion of another employer's notification
    Given a notification belongs to another employer
    When the employer attempts to delete that notification
    Then the system should reject the request
    And the notification should not be deleted

  Scenario: Notification deletion fails
    Given the employer is viewing the notification list
    When the employer attempts to delete a notification
    And the deletion request fails
    Then the system should display an appropriate error message
    And the notification should remain in the notification list

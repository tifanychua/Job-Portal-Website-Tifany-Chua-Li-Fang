Feature: Job Seeker Delete Notifications
  As a job seeker
  I want to delete unwanted notifications
  So that my notification list does not become cluttered.

  Scenario: Delete a notification successfully
    Given the job seeker is viewing the notification list
    And the notification belongs to the job seeker
    When the job seeker selects the delete option for the notification
    And confirms the deletion
    Then the system should remove the notification from the notification list
    And display a notification-deleted success message

  Scenario: Cancel notification deletion
    Given the job seeker has selected the delete option for a notification
    And the confirmation message is displayed
    When the job seeker cancels the deletion
    Then the system should not delete the notification
    And the notification should remain in the notification list

  Scenario: Deleted notification remains deleted after refresh
    Given the job seeker has successfully deleted a notification
    When the job seeker refreshes or revisits the notification page
    Then the deleted notification should not appear in the notification list

  Scenario: Delete an unread notification
    Given the job seeker has an unread notification
    When the job seeker deletes the unread notification
    Then the notification should be removed from the notification list
    And the unread notification count should decrease by one

  Scenario: Prevent deletion of another job seeker's notification
    Given a notification belongs to another job seeker
    When the current job seeker attempts to delete that notification
    Then the system should reject the request
    And the notification should not be deleted

  Scenario: Notification deletion fails
    Given the job seeker is viewing the notification list
    When the job seeker attempts to delete a notification
    And the deletion request fails
    Then the system should display an appropriate error message
    And the notification should remain in the notification list

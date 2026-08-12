Feature: Delete Career Advice Post

  As an Admin
  I want to delete career advice posts
  So that I can remove outdated or irrelevant information

  Scenario: Delete an existing career advice post
    Given the admin is viewing the career advice management section
    When the admin selects a career advice post and chooses the delete option
    Then the system should remove the selected career advice post from the system

  Scenario: Confirm career advice post deletion
    Given the admin has selected a career advice post for deletion
    When the admin confirms the delete action
    Then the system should delete the selected post
    And display a confirmation message indicating that the post has been successfully deleted

  Scenario: Cancel career advice post deletion
    Given the admin has selected a career advice post for deletion
    When the admin cancels the delete action
    Then the system should keep the career advice post unchanged

  Scenario: Verify the deleted post is unavailable
    Given the admin has successfully deleted a career advice post
    When a job seeker accesses the career advice section
    Then the deleted post should no longer be displayed
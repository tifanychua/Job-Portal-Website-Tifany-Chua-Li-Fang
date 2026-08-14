Feature: Filter Saved Career Advice Posts

  As a Job Seeker
  I want to filter my saved Career Advice posts
  So that I can view posts from a specific category

  Scenario: Filter saved posts by category
    Given the job seeker is viewing the saved posts page
    When the job seeker selects a Career Advice category
    Then the system should display only saved posts that belong to the selected category

  Scenario: Display no posts for the selected category
    Given the job seeker is viewing the saved posts page
    When the job seeker selects a category that has no matching saved posts
    Then the system should display a message indicating that no matching posts were found

  Scenario: Display saved posts from all categories
    Given the job seeker has filtered the saved posts by category
    When the job seeker selects all categories
    Then the system should display saved posts from every category
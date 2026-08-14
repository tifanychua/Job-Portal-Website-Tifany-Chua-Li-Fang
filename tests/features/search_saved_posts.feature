Feature: Search Saved Career Advice Posts

  As a Job Seeker
  I want to search my saved Career Advice posts
  So that I can quickly find a specific saved post

  Scenario: Search saved posts by title
    Given the job seeker is viewing the saved posts page
    When the job seeker enters a post title in the search field
    Then the system should display saved posts that match the entered title

  Scenario: Search saved posts by summary
    Given the job seeker is viewing the saved posts page
    When the job seeker enters a summary keyword in the search field
    Then the system should display saved posts containing the entered keyword

  Scenario: Search for a saved post that does not exist
    Given the job seeker is viewing the saved posts page
    When the job seeker enters a keyword that does not match any saved post
    Then the system should display a message indicating that no matching posts were found

  Scenario: Clear the saved post search
    Given the job seeker has entered a keyword in the saved post search field
    When the job seeker clears the search field
    Then the system should display all saved Career Advice posts
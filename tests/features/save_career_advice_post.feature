Feature: Save Career Advice Post

  As a Job Seeker
  I want to save career advice posts
  So that I can read them again later

  Scenario: Save a career advice post
    Given the job seeker is viewing a career advice post
    When the job seeker selects the save option
    Then the system should save the selected post to the job seeker's saved posts list

  Scenario: Confirm successful saving of a career advice post
    Given the job seeker has selected a career advice post to save
    When the save action is completed successfully
    Then the system should display a confirmation message indicating that the post has been saved successfully

  Scenario: View saved career advice posts
    Given the job seeker has saved one or more career advice posts
    When the job seeker accesses the saved posts section
    Then the system should display a list of all saved career advice posts

  Scenario: Prevent duplicate saving of the same career advice post
    Given the job seeker has already saved a career advice post
    When the job seeker selects the save option for the same post again
    Then the system should prevent a duplicate entry from being created
    And indicate that the post has already been saved
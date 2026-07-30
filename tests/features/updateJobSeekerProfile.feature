Feature: Update Job Seeker Profile

Scenario: Update profile information successfully
    Given the job seeker is logged in
    And the job seeker is viewing the Edit Profile page
    When the job seeker updates their personal details and saves the changes
    Then the system should update the profile information successfully
    And display the updated details in the profile

Scenario: Update profile with valid information
    Given the job seeker is editing their profile information
    When the job seeker enters valid details such as name, contact information, education, or experience
    And saves the changes
    Then the system should store the updated information successfully

Scenario: Update profile with invalid information
    Given the job seeker is editing their profile information
    When the job seeker enters invalid or incorrectly formatted information
    And saves the changes
    Then the system should display appropriate validation messages
    And prevent the invalid information from being saved

Scenario: Cancel profile update
    Given the job seeker has modified their profile information
    When the job seeker cancels the update action
    Then the system should discard the changes
    And keep the previous profile information unchanged

Scenario: Display updated profile information
    Given the job seeker has successfully updated their profile
    When the job seeker views their profile page
    Then the system should display the latest saved profile information

Scenario: Update profile without entering a required name
    Given the job seeker is editing their profile information
    When the job seeker leaves the name field empty
    And saves the changes
    Then the system should display a validation message
    And prevent the profile information from being updated

Scenario: Update profile with an invalid email address
    Given the job seeker is editing their profile information
    When the job seeker enters an invalid email address
    And saves the changes
    Then the system should display a validation message
    And prevent the profile information from being updated

Scenario: Update profile with an invalid phone number
    Given the job seeker is editing their profile information
    When the job seeker enters an invalid phone number
    And saves the changes
    Then the system should display a validation message
    And prevent the profile information from being updated

Scenario: Update profile with empty required fields
    Given the job seeker is editing their profile information
    When the job seeker leaves one or more required fields empty
    And saves the changes
    Then the system should display validation messages
    And prevent the profile information from being updated
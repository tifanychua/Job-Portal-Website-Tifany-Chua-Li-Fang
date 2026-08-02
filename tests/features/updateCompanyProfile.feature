Feature: Update Company Profile

  Scenario: Update company profile successfully
    Given the employer has an existing company profile
    When the employer updates the company information with valid details
    Then the system should save the updated company profile
    And display the updated company information

  Scenario: Update all required company information
    Given the employer has an existing company profile
    When the employer updates all required company information
    Then the system should allow the company profile to be updated successfully

  Scenario: Upload company logo successfully
    Given the employer has an existing company profile
    When the employer uploads a valid company logo
    Then the system should store the uploaded logo
    And display the logo on the company profile

  Scenario: View updated company profile
    Given the employer has updated the company profile
    When a job seeker views the company profile
    Then the system should display the latest company information

  Scenario: Update company profile with missing company name
    Given the employer has an existing company profile
    When the employer submits the profile without entering the company name
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with missing industry
    Given the employer has an existing company profile
    When the employer submits the profile without selecting an industry
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with missing contact information
    Given the employer has an existing company profile
    When the employer submits the profile without contact information
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with invalid founded year
    Given the employer has an existing company profile
    When the employer enters an invalid founded year
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with invalid postal code
    Given the employer has an existing company profile
    When the employer enters an invalid postal code
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile without selecting any specialty
    Given the employer has an existing company profile
    When the employer submits the profile without selecting any specialty
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with more than six specialties
    Given the employer has an existing company profile
    When the employer selects more than six specialties
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Update company profile with missing company description
    Given the employer has an existing company profile
    When the employer submits the profile without entering the company description
    Then the system should display a validation message
    And the company profile should not be updated

  Scenario: Upload unsupported company logo format
    Given the employer has an existing company profile
    When the employer uploads an unsupported file format
    Then the system should reject the uploaded file
    And display an error message
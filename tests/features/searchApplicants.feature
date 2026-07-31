Feature: Search Applicants

  Scenario: Search applicants by name
    Given the employer has received applications from multiple candidates
    When the employer enters an applicant's name in the search bar
    Then the system should display applicants whose names match the search keyword

  Scenario: Search applicants by skills
    Given applicants have listed their skills in their profiles
    When the employer enters a skill keyword in the search bar
    Then the system should display applicants who have matching skills

  Scenario: Search applicants by email address
    Given the employer has access to applicant records
    When the employer enters an applicant's email address in the search bar
    Then the system should display the applicant record associated with the email address

  Scenario: Search applicants using partial keywords
    Given the employer is searching for an applicant
    When the employer enters a partial keyword
    Then the system should display applicant records containing the matching keyword

  Scenario: No matching applicant records found
    Given the employer enters a keyword that does not match any applicant records
    When the search is performed
    Then the system should display a "No applicants found" message

  Scenario: Clear search results
    Given the employer has performed an applicant search
    When the employer clears the search keyword
    Then the system should display the complete applicant list again
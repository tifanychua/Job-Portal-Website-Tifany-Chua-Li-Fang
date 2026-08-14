Feature: Search Conversations

  As a User
  I want to search my conversations
  So that I can quickly find a specific conversation

  Scenario: Search conversations by user name
    Given the user is logged into the system
    And the user is viewing the Messages page
    When the user enters a name in the conversation search field
    Then the system should display conversations that match the entered name

  Scenario: Search conversations by latest message
    Given the user is logged into the system
    And the user is viewing the Messages page
    When the user enters a keyword from the latest message in the search field
    Then the system should display conversations containing the entered keyword

  Scenario: Search for a conversation that does not exist
    Given the user is viewing the Messages page
    When the user enters a search value that does not match any conversation
    Then the system should display a message indicating that no conversations were found

  Scenario: Clear the conversation search
    Given the user has entered a value in the conversation search field
    When the user clears the search field
    Then the system should display all conversations
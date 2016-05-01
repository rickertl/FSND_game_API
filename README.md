#Hangman Game app using Google App Engine backed by Google Datastore

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
 
##Game Description:
Hangman is a guessing game. Each game begins with a random 'target' word with
'x' number of letter spaces to spell a word. Letter 'guesses' are sent to the `make_move` 
endpoint which will reply with either: 'good guess', 'bad guess', 'you win', or 'you lose'
(if the maximum number of attempts is reached). Many different Hangman games can be played 
by many different Users at any given time. Each game can be retrieved or played by using the 
path parameter `urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.

- **get_game_history**
    - Path: 'game/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForm with games plays made.
    - Description: Returns play history of specific game.
    
- **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
- **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
- **get_high_scores**
    - Path: 'scores/highest'
    - Method: GET
    - Parameters: number_of_results (optional, defaults to 5 max)
    - Returns: ScoreForms sorted by least misses first.
    - Description: Returns up to top 5 scores ranked by least misses first.

- **get_user_rankings**
    - Path: 'rankings'
    - Method: GET
    - Parameters: None
    - Returns: RankingsForms.
    - Description: Returns User rankings by wins/games_played, sorted by best percentage
    first.

- **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms filtered for specific user.
    - Description: Returns all of an individual User's active games.

- **cancel_game**
    - Path: 'games/cancel/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: Message confirming deletion of game.
    - Description: Users can cancel a game. Completed games not included.



##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, missies_remaining,
    bad_guesses, good_guesses, status, history, game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **GameHistoryForm**
    - Representation of a game's play history (urlsafe_key, history)
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    misses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **RankingsForm**
    - Representation of player rankings (user_name, percentag_won, played).
 - **StringMessage**
    - Multiple RankingsForm container.

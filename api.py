# -*- coding: utf-8 -*-`
"""api.py - Hangman Game app using Google App Engine backed by Google Datastore"""

__author__ = "Rick Ertl"

import logging
import endpoints
from protorpc import remote, messages

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameForms, RankingsForms, GameHistoryForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1),)


@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):

    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        game = Game.new_game(user.key)

        # create initial output of hangman board
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        guess = request.guess.lower()
        got_word = False

        if game.game_over:
            return game.to_form('Game already over!')

        def winner():
            game.end_game(True)
            game.history.append('guess: ' + guess + ', result: win')
            return game.to_form('You win! The word was {}.'.format(game.
                                                                   target))
        # check if input OK to make game play
        if guess == game.target:
            got_word = True
        elif len(guess) != 1:
            return game.to_form("You can only guess a single letter or the whole word.")
        elif guess in game.bad_guesses or guess in game.good_guesses:
            return game.to_form("You've already guessed that letter.")
        elif not guess.isalpha():
            return game.to_form("You can only guess letters.")

        # create output of hangman board
        def board():
            status_list = []
            for letter in game.target:
                if got_word:
                    status_list.append(letter)
                elif letter in game.good_guesses:
                    status_list.append(letter)
                else:
                    status_list.append('_')
            game.status = ' '.join(status_list)

        # play letter input
        if guess in game.target or got_word:
            game.good_guesses.append(guess)
            board()
            if len(game.good_guesses) == len(''.join(set(game.target))) or got_word:
                game.end_game(True)
                game.history.append('guess: ' + guess + ', result: win')
                return game.to_form('You win! The word was {}.'.format(game.
                                                                       target))
            else:
                game.history.append('guess: ' + guess + ', result: hit')
                msg = 'good guess'
        else:
            game.bad_guesses.append(guess)
            board()
            game.misses_remaining -= 1
            game.history.append('guess: ' + guess + ', result: miss')
            msg = 'bad guess'

        if game.misses_remaining < 1:
            game.end_game(False)
            game.history.append('guess: ' + guess + ', result: lose')
            return game.to_form('You lost! The word was {}.'.format(game.
                                                                    target))
        else:
            game.put()
            return game.to_form(msg)

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistoryForm,
                      path='game/history/{urlsafe_game_key}',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Task 3e: Return play history of specific game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.history_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/highest',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Task 3c: Returns highest scores (least number of misses)"""
        if request.number_of_results:
            number_of_results = request.number_of_results
        else:
            number_of_results = 5
        high_scores = Score.query().order(Score.misses).fetch(
            number_of_results)
        return ScoreForms(items=[score.to_form() for score in high_scores])

    @endpoints.method(response_message=RankingsForms,
                      path='rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Task 3d: Returns player rankings based on win/loss."""
        rankings = User.query().order(-User.percent_won, -User.played).fetch()
        return RankingsForms(items=[ranking.to_form() for ranking in rankings])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Task 3a: Returns all of an individual User's active games"""
        user = User.query(User.name == request.user_name).get()
        start = Game.query(Game.user == user.key).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        elif not start:
            raise endpoints.NotFoundException('No games yet for User!')
        else:
            games = Game.query(Game.user == user.key and Game.game_over ==
                               False)
            return GameForms(items=[game.to_form('') for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Task 3b: Users can cancel a game. Completed games not included."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        elif game.game_over:
            raise endpoints.ConflictException('Game already over!')
        else:
            game.key.delete()
            return StringMessage(message='Success. Game cancelled.')


api = endpoints.api_server([HangmanApi])

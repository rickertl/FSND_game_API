"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


words = [
    'alligator',
    'camel',
    'cheetah',
    'chicken',
    'chimpanzee',
    'crocodile',
    'dolphin',
    'eagle',
    'elephant',
    'giraffe',
    'goldfish',
    'hamster',
    'hippopotamus',
    'horse',
    'kangaroo',
    'kitten',
    'lobster',
    'monkey',
    'octopus',
    'panda',
    'puppy',
    'rabbit',
    'scorpion',
    'shark',
    'sheep',
    'snail',
    'snake',
    'spider',
    'squirrel',
    'tiger',
    'turtle',
    'zebra'
]


class User(ndb.Model):

    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(default=0)
    played = ndb.IntegerProperty(default=0)
    percent_won = ndb.IntegerProperty(default=0)

    def to_form(self):
        return RankingsForm(user_name=self.name, percent_won=(self.percent_won),
                            played=(self.played))


class Game(ndb.Model):

    """Game object"""
    target = ndb.StringProperty(required=True)
    bad_guesses = ndb.GenericProperty(repeated=True)
    good_guesses = ndb.GenericProperty(repeated=True)
    status = ndb.StringProperty(required=True)
    misses_remaining = ndb.IntegerProperty(required=True, default=6)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.GenericProperty(repeated=True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        word = random.choice(words)
        start_board = len(list(word)) * '_ '
        game = Game(user=user,
                    target=word,
                    bad_guesses=[],
                    good_guesses=[],
                    status=start_board,
                    misses_remaining=6,
                    game_over=False,
                    history=[])
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.misses_remaining = self.misses_remaining
        form.bad_guesses = self.bad_guesses
        form.good_guesses = self.good_guesses
        form.status = self.status
        form.history = self.history
        form.game_over = self.game_over
        form.message = message
        return form

    def history_form(self):
        """Returns a GameHistoryForm representation of the Game"""
        form = GameHistoryForm()
        form.urlsafe_key = self.key.urlsafe()
        form.history = self.history
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      misses=len(self.bad_guesses))
        score.put()
        # Add the game to the user's record
        user = User.query(User.key == self.user).get()
        if won:
            user.wins += 1
        user.played += 1
        calc = float(user.wins) / float(user.played)
        percent_won = int((calc * 100) + 0.5)
        result = User(key=user.key, name=user.name, email=user.email,
                      wins=user.wins, played=user.played, percent_won=percent_won)
        result.put()


class Score(ndb.Model):

    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    misses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), misses=self.misses)


class GameForm(messages.Message):

    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    misses_remaining = messages.IntegerField(2, required=True)
    bad_guesses = messages.StringField(3, repeated=True)
    good_guesses = messages.StringField(4, repeated=True)
    status = messages.StringField(5, required=True)
    history = messages.StringField(6, repeated=True)
    game_over = messages.BooleanField(7, required=True)
    message = messages.StringField(8, required=True)
    user_name = messages.StringField(9, required=True)


class GameForms(messages.Message):

    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):

    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):

    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class GameHistoryForm(messages.Message):

    """GameHistoryForm for outbound game history information"""
    urlsafe_key = messages.StringField(1, required=True)
    history = messages.StringField(2, repeated=True)


class ScoreForm(messages.Message):

    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    misses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):

    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):

    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class RankingsForm(messages.Message):

    """RankingsForm for outbound User Rankings information"""
    user_name = messages.StringField(1, required=True)
    percent_won = messages.IntegerField(2, required=True)
    played = messages.IntegerField(3, required=True)


class RankingsForms(messages.Message):

    """Return multiple RankingsForms"""
    items = messages.MessageField(RankingsForm, 1, repeated=True)

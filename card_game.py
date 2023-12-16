# CPE 551 WS1
# Final project
# Nikhil Varma Bandaru
# 20015416
from collections import defaultdict
import os
import re
import threading
import time
import random
import bisect
instructions = '''
Creator: Nikhil Varma Bandaru
CWID: 20015416
----------------  ONO card game-------------------
There is a time limit for this game. It can be provided by the admin, by default it is 300 seconds(5 minutes)
1. This game consists a deck of 54 cards, once deck is over it is regenerated. 2 to 8 players can play this game. 
2. Suits are Red, blue, green, yellow colors while ranks are 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
   'eight', 'nine', 'rev
   erse', 'skip', '+2'.
   This can constitute to 4 x 13 = 52 cards.
3. There are 2 wild cards namely color change card, +4 card.
4. Each card carries a weight, score of zero is 0, one is 1, and so on, as the order increases the score of that card increases.
    It doesn't matter what color it is.
5. Wild card carries 15 points. 
6. All cards are shuffled, distributed among players, number of cards distributed can be provided by the admin, by default it is 7
    and one card from deck is picked and placed at center(let's call it top card). 
7. Players can only drop card if they have a card matching the top card by the rank on them or color of them or if they have a wild card.
    Ex: If top card is "One of Blue", player can put any color card having "One" on them or any other "blue" card or any wild card(color change, +4).
8. After dropping a wild card that player decides the color that the next player needs to play, rank doesn't matter here.
9. If a reverse card is dropped, the direction of game changes.
    ex: If it is going by 1,2,3,4 order and 2 puts a reverse card then it changes to 1,4,3,2 and this continues until next reverse card is placed.
10. If a skip card is dropped, The turn of next player is skipped.
    Ex: If player 1 drops a skip and the order is 1,2,3,4 then, player 2 is skipped and player 3 has to play.
11. If a +2 card is dropped, the next player in the order takes in 2 cards from the deck and his turn gets skipped.
12. If a +4 card is dropped the player also has to choose a color of their choice for the game, 
    the next player in the order picks up 4 cards and their turn is skipped..
13. If a player enters 'q' when prompted they will be kicked out of the game and their score is invalid.
14. If a player finishes their deck first by dropping all their cards, they win..
    If 2 or more players receive same score, they are treated as winners..
    If all players have same score, it means game is tie for all the players...
All the best buddies, have fun!!! 
'''


# Card class to create a playing card with suit representing the color of the card and rank saying the type of card.
# There are few wild cards that are independent of the rank.

class Card:
    def __init__(self, suit, rank=None, weight=None):
        self.suit = suit
        self.rank = rank
        self.weight = weight

    def __str__(self):
        if self.rank:
            return f"{self.rank.capitalize()} of {self.suit.capitalize()}"
        return f"{self.suit.capitalize()} card"

# Class Deck to create a deck(list) of cards there are a total of 54 cards(52 normal+2 wild)


class Deck:
    def __init__(self):
        self.suits = ['Red', 'Blue', 'Green', 'Yellow']
        self.ranks = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
                      'eight', 'nine', 'reverse', 'skip', '+2']
        self.weights = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self.wild = ['color change', '+4']
        self.cards = [Card(suit, rank, weight) for suit in self.suits for rank, weight in zip(
            self.ranks, self.weights)] + [Card(w, None, None) for w in self.wild]

    # This will shuffle the deck of cards
    def shuffle(self):
        random.shuffle(self.cards)

    # This method fetches the last card from the deck of cards.
    # If the deck becomes, it creates a new deck and take cards from that deck.
    def deal_card(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            self.shuffle()
            if len(self.cards) > 0:
                return self.cards.pop()
            else:
                self.cards = [Card(suit, rank, weight) for suit in self.suits for rank, weight in zip(
                    self.ranks, self.weights)] + [Card(w, None, None) for w in self.wild]
                self.shuffle()
                return self.cards.pop()

    # Overwritten string method to return the cards as a single string
    def __str__(self):
        s = ""
        for i in range(len(self.cards)):
            s = s+i*" "+str(self.cards[i])+'\n'
        return s


# Class ONO(ONO is the name of this card game..similar to UNO :D)
class ONO:
    def __init__(self, timer_duration=180, numberofcards=7):
        self.deck = Deck()  # creates a Deck object
        self.deck.shuffle()  # Shuffles the deck of cards
        # a dictionary to store {player:[card Object 1,card object 2,...]}
        self.players_hands = None
        self.winner = ''  # Stores the won player name
        # Time duration for the game, by default it is set to 180 seconds.
        self.timer_duration = timer_duration
        self.start_time = None
        self.timer_thread = None  # thread that runs the timer
        # number of cards each player gets, by default it is set to 7 cards per player.
        self.n_cards = numberofcards
        # Changes to True if the game is over(Either the timer ends or a player finishes their deck).
        self.game_started = False
        print(f"All available cards are:\n----------")
        time.sleep(1)
        print(self.deck)  # Prints all the cards in the deck.
        # Takes a card out for the game to start.
        self.top_card = self.deck.deal_card()
        # 1st card can't be a color change.
        if self.top_card.suit == 'color change':
            temp = self.top_card
            self.top_card = self.deck.deal_card()
            self.deck.cards.append(temp)

    # function to start the timer
    def start_timer(self):
        self.start_time = time.time()
        print(f"Timer started! {self.timer_duration}s left...")
        time.sleep(1)

    # method that checks if the time is up or not
    def timer_clock(self):
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.timer_duration - elapsed_time)

        # Check if the time is up
        if remaining_time == 0:
            print("\nTime's up!!!\n")
            self.game_over = True
            self.end_game()

        else:
            # Schedule the timer to check again in 1 second
            threading.Timer(1, self.timer_clock).start()

    # This method distributes the required number of cards between the given players
    # 2 to 4 players can play this at once..
    def distribute_cards(self, num_players, deck, name_list):
        players = defaultdict(list)
        for _ in range(self.n_cards):
            for player in name_list:
                card = deck.deal_card()
                if card:
                    players[player].append(card)
                    players[player].sort(key=lambda x: (
                        x.weight if x.rank is not None else float('+inf')), reverse=True)
        return players

    # Method to add cards to a player(runs when +2 card or +4 card is dropped by a neighboring player..)
    def add_cards(self, n, name_list, player_choice):
        c = ''
        for i in range(n):
            c = self.deck.deal_card()
            if not c:
                self.game_over = True
                break
            player = name_list[player_choice]
            self.players_hands[player].append(c)
        self.players_hands[player].sort(key=lambda x: (
            x.weight if x.rank is not None else float('+inf')), reverse=True)
        return c

    # This method has the logic for the game..
    def play(self):
        numberOfplayers = 0
        color_emoji = ''
        direction = 1  # used for reverse card
        self.game_over = False  # Boolean to determine game is over or not.
        red = '\U0001F534'
        blue = '\U0001F535'
        green = '\U0001F7E2'
        yellow = '\U0001F7E1'
        # Asks number of players wanted to play this game
        # Expects input values ranging from 2 to 8.
        while not (1 < numberOfplayers <= 8):
            try:
                numberOfplayers = int(input("Input number of players(2-8):"))
            except:
                None
            if not (1 < numberOfplayers <= 8):
                print("Invalid number of players, please try again!!")
        print()
        # time.sleep(1)
        name_choice = ''
        name_list = []
        # Asks whether the users wanted to give their names or use default names generated by the program..
        # If yes, it expects the input to be a string with alphabets at start and may contain numbers at the end of string.
        # Examples:
        # can give Nikhil, Nikhil123..
        # can not give 123Nikhil, 1234,@#$%..
        # if given no, player1, player2, etc are generated.
        while name_choice not in ['y', 'n']:
            name_choice = input(
                "Would you like to assign names to all the players? (y/n): ").strip().lower()
        if name_choice == 'y':
            i = 1
            pattern = r'^[a-zA-Z]+[0-9]*$'
            print(
                "Every name should be unique, start with alphabets and can end with a number")
            while i < numberOfplayers+1:
                name = input(f"Enter Player {i}'s name: ").strip().lower()
                if len(name) > 15:
                    print("Try a name with less than 15 characters")
                    continue
                matching = re.match(pattern, name)
                if matching and name not in name_list:
                    name_list.append(name)
                    i += 1
                else:
                    print(
                        "\u274C Name already exists/invalid, try a different name! \n")
        else:
            for i in range(1, numberOfplayers+1):
                name_list.append(f"Player {i}")

        print("\n \U0001F38A Welcome to ONO! ", end='')

        for i, name in enumerate(name_list):
            print(name.capitalize(), end=", " if i <
                  len(name_list) - 1 else ".\n")

        # Timer gets started at this point.
        self.start_timer()
        # Schedule the timer to check every second
        self.timer_thread = threading.Thread(target=self.timer_clock)
        self.timer_thread.start()

        print("Game started...\U0001F680\n")
        time.sleep(1)

        # player_hands stores, name of player as a key and list of cards as a value in a default dictionary.
        self.players_hands = self.distribute_cards(
            numberOfplayers, self.deck, name_list)
        # Prints the cards of each player
        '''
        for i, hand in enumerate(list(self.players_hands.values())):
            print(f"{name_list[i]}'s Hand:")
            print("-"*len(max(name_list, key=len))+"------\n")

            for card in hand:
                print(card)
            time.sleep(0.5)
            print()
        print("- - - - - - - - - - - - - - -")
        time.sleep(1)
        '''
        # Chooses a player randomly from given number of players
        player_choice = random.randint(0, numberOfplayers-1)

        top_card_rank = self.top_card.rank
        top_card_suit = self.top_card.suit

        print()
        color_choice = ''
        direction_changed = False  # checks if the direction changed or when used a reverse card
        skipped = False  # Checks if card skipped is used or not
        cards_added2 = False  # Checks if 2 cards are added to the targeted player
        cards_added4 = False  # Checks if 4 cards are added to the targeted player

        # Loops until game gets over or number of players are greater than 1
        while not self.game_over and numberOfplayers > 1:
            top_card_rank = self.top_card.rank
            top_card_suit = self.top_card.suit

            print(f"Play card: {str(self.top_card)} \n")

            # checks if the top card is a reverse card and processes.
            if top_card_rank == 'reverse' and not direction_changed:
                print("Reversing the direction\U0001F504")
                direction *= -1
                player_choice = (player_choice+(2*direction)) % numberOfplayers
                direction_changed = True
            # checks if the top card is a skip card and processes.
            elif top_card_rank == 'skip' and not skipped:
                print(
                    f"{name_list[player_choice].capitalize()} skipped \U0001F6AB..\n")
                player_choice = (player_choice+1) % numberOfplayers
                skipped = True
            # checks if the top card is a +2 card and processes.
            elif top_card_rank == '+2' and not cards_added2:
                self.add_cards(2, name_list, player_choice)
                emoji = '\U0001F0CF' * 2
                print(
                    f"\n2 cards{emoji} added to '{name_list[player_choice].capitalize()}'\n")
                print(
                    f"{name_list[player_choice].capitalize()} skipped \U0001F6AB..\n")
                cards_added2 = True
                player_choice = self.get_player(
                    direction, player_choice, numberOfplayers)
            # checks if the top card is a +4 and processes.
            elif top_card_suit == '+4' and not cards_added4:
                self.add_cards(4, name_list, player_choice)
                emoji = '\U0001F0CF' * 4
                print(
                    f"\n4 cards{emoji}  added to '{name_list[player_choice].capitalize()}'\n")
                print(
                    f"{name_list[player_choice].capitalize()} skipped \U0001F6AB..\n")
                cards_added4 = True
                player_choice = self.get_player(
                    direction, player_choice, numberOfplayers)
                if not color_choice:
                    top_card_suit = random.choice(self.deck.suits)
            # checks if the top card is a color change card and processes.
            if not top_card_rank:
                if top_card_suit == 'color change' or top_card_suit == '+4':
                    print(f"Color changed to {color_choice}{color_emoji}")
                    top_card_suit = color_choice

            # Prints the player's name
            player_name = name_list[player_choice].capitalize()
            print(f"--> {player_name}'s chance to play..\n")

            # Enough time to exchange the control between players
            time.sleep(2)

            # Prints the cards a player has when mode="" or mode is 'all'
            # Prints the cards that can be dropped by a player when mode='drop'
            def print_cards(mode=""):
                if mode == 'all' or mode == "":
                    print(
                        f"{name_list[player_choice].capitalize()}: Your cards.\n-----------")
                    for ind, card in enumerate(list(self.players_hands.values())[player_choice]):
                        print(f"[{ind}]: {str(card)}")

                elif mode == 'drop':
                    valid_indices = []
                    print(
                        f"\n{player_name}: You can drop the cards below!\n----------")
                    for ind, card in enumerate(list(self.players_hands.values())[player_choice]):
                        if top_card_rank is None:
                            if card.suit == top_card_suit:
                                valid_indices.append(ind)
                                print(f"[{ind}]: {str(card)}")
                        else:
                            if (card.rank is None or card.rank == top_card_rank or card.suit == top_card_suit):
                                valid_indices.append(ind)
                                print(f"[{ind}]: {str(card)}")
                    return valid_indices
            print_cards()
            # Gets all the indices of cards that can be dropped.
            valid_indices = print_cards('drop')

            p_choice = ''
            # Gets the choice from the user, whether a player wants to pick a card or drop a card or quit game.
            # If a user doesn't have any card to drop, it automatically picks a card for the player.
            while True and not self.game_over:
                if valid_indices:
                    print("- - "*15)
                    p_choice = input(
                        f"{player_name}, You can pick a new card from deck (press p),\n\t\t Quit game(press q),\n\t\tDrop one of your cards(press the index number): \nYour choice: ").strip().lower()
                else:
                    print(
                        'you do not have a matching card to drop, picking a card for you :)\U0001F64C\n')
                    time.sleep(1)
                    # assigning pick up card mode, when there are no cards left.
                    p_choice = 'p'
                if p_choice == 'p':
                    pick = self.add_cards(1, name_list, player_choice)
                    print(f"{player_name} picked {str(pick)} sucessfully\n")
                    time.sleep(1)
                    break
                # When a player chooses q, which means player wants to quit game
                # In this case, that player is removed from the game and other players can continue to play.
                elif p_choice == 'q':
                    del self.players_hands[name_list[player_choice]]
                    name_list.pop(player_choice)
                    player_choice = self.get_player(
                        direction, player_choice, numberOfplayers)
                    numberOfplayers -= 1
                    if direction > 0:
                        player_choice = (player_choice-1) % numberOfplayers
                    else:
                        player_choice = player_choice % numberOfplayers
                    print(
                        f"{player_name} exited the game \U0001F6AA\U0001F3C3, {numberOfplayers} player/s remaining..")
                    time.sleep(1)
                    break
                else:
                    # Sometimes users give different types of inputs, for example instead of giving 1, they might also give "1", [1].
                    # This below code handles that, saving the player's time.
                    try:
                        p_choice = int(self.extract_digits(p_choice))
                    except:
                        None

                    if p_choice in valid_indices:  # meaning player has given correct index to drop the card
                        self.top_card = self.players_hands[name_list[player_choice]].pop(
                            p_choice)
                        valid_indices = []
                        if self.top_card.rank == 'reverse':
                            direction_changed = False
                        elif self.top_card.rank == 'skip':
                            skipped = False
                        elif self.top_card.rank == '+2':
                            cards_added2 = False
                        if self.top_card.suit == '+4':
                            cards_added4 = False
                        print(
                            f"{player_name} dropped {self.top_card} Card.. \n")
                        time.sleep(1)
                        if not self.top_card.rank:
                            color = ''

                            print("Since you dropped a wild card, \n")

                            while color not in ['r', 'b', 'g', 'y']:
                                print_cards()
                                color = input(
                                    f"Choose a color({red}Red[r], {blue}Blue[b], {green}Green[g], {yellow}Yellow[y]): ").strip().lower()
                                if color not in ['r', 'b', 'g', 'y']:
                                    print('wrong choice, try again..\n')
                            colors = {'r': ['Red', red], 'b': ['Blue', blue],
                                      'g': ['Green', green], 'y': ['Yellow', yellow]}
                            color_choice = colors[color][0]
                            color_emoji = colors[color][1]
                            # print("Color changed to ",color_choice,"\n")
                        break
                    else:  # Player gave some other values
                        print(
                            f"\u274CYour choice {p_choice} can't be dropped/ invalid, \n Try again by entering a valid value.. \n")
                        # waits for 1 second, letting player know something went wrong..
                        time.sleep(1)
                        print_cards('drop')

            # It checks if a user dropped all their cards.
            # If true, it ends the game by setting gave_over to True thus breaking the while loop
            # It assigns the current player as a winner, as they dropped all cards first.
            if not list(self.players_hands[name_list[player_choice]]):
                self.game_over = True
                self.winner = player_name
                break
            # If a player doesn't quit, the player should be updated based on direction of the game..
            if p_choice != 'q':
                player_choice = self.get_player(
                    direction, player_choice, numberOfplayers)
            print("===============================================\n")
        # calls end_game() that calculates score and terminates the program
        return self.end_game()

    # Method used in the above while loop to get the index of the player
    def get_player(self, direction, player_choice, numberOfplayers):
        if direction < 0:
            player_choice = (player_choice - 1) % numberOfplayers
        else:
            player_choice = (player_choice + 1) % numberOfplayers
        return player_choice

    # Helper method used to filter the numerical choice of the dropping card from the player input
    def extract_digits(self, input_string):
        # Define a regular expression pattern to capture digits
        digit_pattern = r'^(\d+|\[(\d+)\])$'

        # Use re.match to check if the input matches the allowed pattern
        match = re.match(digit_pattern, input_string)

        if match:
            # If there is a match, extract the digits
            if match.group(2):
                return match.group(2)  # Digits inside square brackets
            else:
                return match.group(1)  # Other digits
        else:
            # If there is no match, raise an error
            raise ValueError("\u274CInvalid input format")

    # Method to calculate score and decide the winner
    def end_game(self):
        min_score = float('inf')
        winners = []
        scores = []
        if self.winner:
            print(
                f"Congratulations {self.winner}, you won the game\U0001F3C6..")

        else:
            if self.players_hands:  # Checking if the dictionary is not empty
                for player, cards in self.players_hands.items():
                    score = 0
                    for card in cards:
                        if card.rank is None:
                            score += 15
                        else:
                            score += self.deck.ranks.index(card.rank)
                    if score < min_score:
                        min_score = score
                        self.winner = player
                        winners = [player]
                    elif score == min_score:
                        winners.append(player)
                    scores.append(score)

                if len(winners) < len(self.players_hands):
                    print("Congratulations ", end="")
                    # prints all the players with minimum scores..
                    for i, p in enumerate(winners):
                        print(p, end=', ' if i < len(winners) -
                              1 else ', you won the game\U0001F3C6\n')
                elif len(winners) > 1 and len(winners) == len(self.players_hands):
                    print("Tie for all..\u2696\ufe0f")
                elif len(winners) == 1:
                    print(
                        f"Congratulations {winners[0]}, you won the game..")
            else:
                print("Game hasn't started, results can't be printed...")
        self.exit_program()

    # method to terminate the program
    def exit_program(self):
        print("Game ended\U0001F3C1")
        os._exit(1)


def readme():
    ins = input("Do you want to read the instructions? (y): ").strip().lower()

    if ins == 'y':
        print(instructions)
        input("Press Enter to continue..")
    else:
        print("Well, Entering the world of luck...")
    return


def settings(duration, number_of_cards):
    user = input(
        "Do you want to change the time limit and number of cards per each player? (y), Enter to skip: ").strip().lower()
    if user == 'y':
        password = ''
        tries = 5
        while password != 'admin' and tries > 0:
            # admin is the password
            password = input("Enter the admin's password: ").strip()
            if password != 'admin':
                tries -= 1
                print(f"\u274CWrong password, {tries} attempts left")
        if password == 'admin':
            print("Correct password \u2705\n")
            tries = 5
            while tries >= 1:
                try:
                    duration = int(
                        input("Enter valid number of seconds of the game[300 to 7200]: ").strip())
                    if 300 <= duration <= 7200:
                        break
                    else:
                        tries -= 1
                        duration = 300
                        print(
                            f"\u274CInvalid duration({tries} tries left). Please enter a number between 300 and 7200(minimum 5 minutes and maximum 2 hours).")
                except:
                    tries -= 1
                    print(
                        f"\u274CInvalid response({tries} tries left), try again :(")
            if tries == 0:
                print("Going with default time limit [300s]")
            tries2 = 5
            while tries2 >= 1:
                try:
                    number_of_cards = int(
                        input("Enter valid number of cards per each player[1 to 20]: ").strip())
                    if 1 <= number_of_cards <= 20:
                        break
                    else:
                        number_of_cards = 7
                        tries2 -= 1
                        print(
                            f"Give only between 1 and 20, {tries2} tries left..")
                except:
                    tries2 -= 1
                    print(
                        f"\u274CInvalid response({tries2} tries left), try again :(")
            if tries2 == 0:
                print("Going with default number of cards [7/player]")
            if tries > 0 or tries2 > 0:
                print(
                    f"Changes updated sucessfully\u2705..[{duration}s, {number_of_cards} cards per player]")
            else:
                print("No changes made..")
        else:
            print(
                "Starting the game with default values.[7 cards per player and 300 seconds time limit]")
    else:
        print(
            "Starting the game with default values.[7 cards per player and 300 seconds time limit]")
    return duration, number_of_cards


duration = 300
number_of_cards = 7
invalid_input_emoji = "\u274C"
if __name__ == "__main__":
    # timer_clock(timer_duration)
    readme()
    duration, number_of_cards = settings(duration, number_of_cards)
    for i, e in enumerate(['\u0033\uFE0F\u20E3', '\u0032\uFE0F\u20E3', '\u0031\uFE0F\u20E3']):
        print(e, end="..." if i < 2 else '')
    time.sleep(3)
    print()
    # object created with a specific time duration and number of cards per player
    game = ONO(duration, number_of_cards)
    game.play()
    os._exit(1)

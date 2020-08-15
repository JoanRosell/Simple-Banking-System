# Write your code here
import random
import sqlite3
from collections import namedtuple

Choice = namedtuple('Choice', ['text', 'value'])

db_name = 'card.s3db'  # The database path should be stored in a config module


# TODO: Add documentation
class User:
    def __init__(self):
        self.is_logged: bool = False
        self.account: Account = None


# TODO: Add documentation
class Account:
    def __init__(self, card_number: str, pin: str, _balance: float = 0):
        self.card_number: str = card_number
        self.pin: str = pin
        self.balance: float = _balance

    def __eq__(self, other):
        if isinstance(other, Account):
            return other.card_number == self.card_number and other.pin == self.pin and other.balance == self.balance
        return NotImplemented

    def __repr__(self):
        return "Your card number:\n" + self.card_number + "\n" + "Your card PIN:\n" + self.pin + "\n"


def luhn_validate(number: str):
    digits = [int(char) for char in number]

    # Luhn algorithm
    # Step 1: multiply all odd digits by two
    modified_digits = digits[0::2]
    for i, digit in enumerate(modified_digits):
        digit *= 2
        # Step 2: if the modified digit is over 9, subtract 9
        modified_digits[i] = digit - 9 if digit > 9 else digit
    digits[0::2] = modified_digits

    # Step 3: add all digits
    return sum(digits) % 10 == 0


# TODO: Add documentation
def create_account(_) -> None:
    new_account = Account(CardNumberGenerator.gen_card_number(db_name), PinGenerator.gen_pin(db_name))

    conn = sqlite3.connect(db_name)
    try:
        with conn:
            conn.execute('INSERT INTO card(number, pin) VALUES (?, ?)', (new_account.card_number, new_account.pin))
    except sqlite3.Error as e:
        print(str(e))
    finally:
        conn.close()

    print("Your card has been created")
    print(new_account)


def log_into_account(user: User) -> None:
    """ Log the user into the system

        To log the user into the system we:
            1. Prompt the user to input the account information

            2. Try to pull the account balance from the database
                2.a. If the query returns None then the account doesn't exist

                2.b. If the query returns something then we log the user into the system

        :return: None
    """

    card_number = input("Enter your card number: \n").strip()
    pin = input("Enter your pin: \n").strip()
    conn = sqlite3.connect(db_name)
    try:
        with conn:
            # Calling Cursor.fetchone() returns a tuple containing the row returned by the query
            # In this case the tuple has only one element
            res = conn.execute('SELECT balance FROM card WHERE number = ? AND pin = ?',
                               (card_number, pin)).fetchone()
            if res is not None:
                user.account = Account(card_number, pin, float(res[0]))
                user.is_logged = True
    except sqlite3.Error as e:
        print(str(e))
    finally:
        conn.close()

    print("You have successfully logged in!\n" if user.is_logged else "Wrong card number or PIN!\n")


def get_balance(user: User) -> None:
    """ Print the users account balance

        :return: None
    """

    print(f"Balance: {user.account.balance}\n")


def add_income(user: User) -> None:
    """ Ask the user for income and add it to it's account

        Prompt the user to input a positive float and add it to the account balance.

        :param user: object that holds a reference to the account

        :return: None
    """

    income = float(input("Enter income: \n").strip())
    if income > 0:
        user.account.balance += income
        conn = sqlite3.connect(db_name)
        try:
            with conn:
                conn.execute('UPDATE card SET balance = ? WHERE number = ? AND pin = ?',
                             (user.account.balance, user.account.card_number, user.account.pin)).fetchone()
        except sqlite3.Error as e:
            print(str(e))
        finally:
            conn.close()

        print("Income was added!\n")
    else:
        print("Please, enter a positive income amount.\n")


def do_transfer(user: User):
    """ Transfer money between accounts

        To authorize and perform a transfer we:
            1. Prompt the user for the target account number
                1.a. If the card number doesn't pass the luhn verification we abort the transfer
                1.b. If the card number passes the luhn verification but it's not found in the database
                we abort the transfer

            2. Ask the user for the amount to transfer
                2.a. If the amount selected is higher than the current balance held in the user account
                the transfer is aborted

            3. Subtract the amount from the current balance and add it to the other account
            4. Save the changes made to the user account to the database
    """

    print("Transfer")
    card_number = input("Enter card number: \n").strip()
    if luhn_validate(card_number):
        conn = sqlite3.connect(db_name)
        card_id = None
        try:
            with conn:
                res = conn.execute('SELECT id FROM card WHERE number = ?', (card_number,)).fetchone()
                if res is not None:
                    card_id = res[0]
        except sqlite3.Error as e:
            print(str(e))
        finally:
            conn.close()

        if card_id is not None:
            amount = float(input("Enter how much money you want to transfer: \n").strip())

            if amount <= user.account.balance:
                user.account.balance -= amount

                conn = sqlite3.connect(db_name)
                try:
                    with conn:
                        conn.execute('UPDATE card SET balance = ? WHERE id = ?', (amount, card_id))
                        conn.execute('UPDATE card SET balance = ? WHERE number = ?',
                                     (user.account.balance, user.account.card_number))
                except sqlite3.Error as e:
                    print(str(e))
                finally:
                    conn.close()

                print("Success!\n")
            else:
                print("Not enough money!\n")
        else:
            print("Such a card does not exist.\n")
    else:
        print("Probably you made mistake in the card number. Please try again!\n")


def close_account(user: User):
    """ Delete the user account from the database

    """

    conn = sqlite3.connect(db_name)
    try:
        with conn:
            conn.execute('DELETE FROM card WHERE number = ?', (user.account.card_number,))
            user.account = None
            user.is_logged = False
    except sqlite3.Error as e:
        print(str(e))
    finally:
        conn.close()

    print("The account has been closed!\n")


# TODO: Add documentation
def log_out(user: User) -> None:
    user.is_logged = False
    user.account = None
    print("You have successfully logged out!\n")


# TODO: Add documentation
def _exit(_):
    print("Bye!")
    exit()


# TODO: Add documentation
class Menu:
    """ Implement a CLI for our banking system

        This class is responsible for:
            - Displaying the menu options
            - Dispatching the user input
    """

    _GUEST_CHOICES: str = "1. Create an account\n2. Log into account\n0. Exit"
    _REGISTERED_CHOICES: str = "1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit"

    _guest_dispatcher: dict = {
        1: create_account,
        2: log_into_account,
        0: _exit
    }

    _registered_dispatcher: dict = {
        1: get_balance,
        2: add_income,
        3: do_transfer,
        4: close_account,
        5: log_out,
        0: _exit
    }

    # TODO: Add documentation
    @classmethod
    def display_options(cls, user: User) -> int:  # This method should be renamed
        print(cls._REGISTERED_CHOICES if user.is_logged else cls._GUEST_CHOICES)
        return int(input())

    # TODO: Add documentation
    @classmethod
    def dispatch(cls, choice: int, user: User):
        cls._registered_dispatcher[choice](user) if user.is_logged else cls._guest_dispatcher[choice](user)


# TODO: Add documentation
class CardNumberGenerator:
    """ Generates card numbers
        This class generates and stores card numbers in a database

    """

    ACC_NUMBER_LENGTH: int = 9

    @classmethod
    def gen_card_number(cls, db: str) -> str:
        """ Public method that generates a new card number
            The card number is comprised by three parts:
                IIN + Customer account number + Checksum

            :return: the card number as a string
        """

        card_numbers: list = []
        conn = sqlite3.connect(db)
        try:
            with conn:
                card_numbers: list = conn.execute('SELECT number FROM card').fetchall()
        except sqlite3.Error as e:
            print(str(e))
        conn.close()

        number: str = cls._gen_iin() + cls._gen_acc_number(cls.ACC_NUMBER_LENGTH)
        card_number = number + cls._gen_checksum(number)

        while card_number in card_numbers:
            number: str = cls._gen_iin() + cls._gen_acc_number(cls.ACC_NUMBER_LENGTH)
            card_number = number + cls._gen_checksum(number)

        return card_number

    @classmethod
    def _gen_iin(cls) -> str:
        """ Method that generates the IIN
            This method returns the number 400000 by default as it
            is the IIN used by our company.

            It's called by gen_card_number()

            :return: the IIN as a string
        """

        return "400000"

    @classmethod
    def _gen_acc_number(cls, length: int) -> str:
        """ Method that generates a new account number

            :param length: the length of the account number

            :return: the account number as a string
        """

        random.seed()
        return str(random.randint(0, (10 ** length) - 1)).zfill(length)

    @classmethod
    def _gen_checksum(cls, card_number: str) -> str:
        """ Method that generates the checksum for a given card number

            It uses the Luhn algorithm to compute the checksum.

            :param card_number: the card number to be used as input for the checksum function

            :return: the checksum digit as a character
        """

        # Transform the card number string to an integer list
        digits = [int(digit) for digit in card_number]

        # Luhn algorithm
        # Step 1: multiply all odd digits by two
        modified_digits = digits[0::2]
        for i, digit in enumerate(modified_digits):
            digit *= 2
            # Step 2: if the modified digit is over 9, subtract 9
            modified_digits[i] = digit - 9 if digit > 9 else digit
        digits[0::2] = modified_digits

        # Step 3: add all digits
        digit_sum = sum(digits)

        # Step 4: if the number is multiple of 10 return zero, else return the difference to make it multiple of 10
        remainder = digit_sum % 10
        return str(10 - remainder if remainder else remainder)


# TODO: Add documentation
class PinGenerator:
    """ Generates pin numbers

    """

    PIN_LENGTH: int = 4

    @classmethod
    def gen_pin(cls, db: str) -> str:
        """ Generate a random pin number

            Generates a random pin number of length PIN_LENGTH
            :return: pin number as string
        """

        conn = sqlite3.connect(db)
        pins: list = []
        try:
            with conn:
                pins: list = conn.execute('SELECT pin FROM card').fetchall()
        except sqlite3.Error as e:
            print(str(e))

        random.seed()
        pin: str = str(random.randint(0, (10 ** cls.PIN_LENGTH) - 1)).zfill(cls.PIN_LENGTH)
        while pin in pins:
            pin: str = str(random.randint(0, (10 ** cls.PIN_LENGTH) - 1)).zfill(cls.PIN_LENGTH)

        return pin


# TODO: Add documentation
def init_db():
    conn = sqlite3.connect(db_name)
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS card
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    number TEXT,
                    pin TEXT,
                    balance DECIMAL(5,2) DEFAULT 0.00
                );
            ''')
    except sqlite3.Error as e:
        print(str(e))
    finally:
        conn.close()


def main():
    init_db()
    user = User()
    choice = Menu.display_options(user)

    while True:  # Using this idiom avoids returning True on every menu.dispatch(...) call
        Menu.dispatch(choice, user)
        choice = Menu.display_options(user)


if __name__ == '__main__':
    main()

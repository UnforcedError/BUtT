#!/usr/local/Cellar/python3/3.5.1/Frameworks/Python.framework/Versions/3.5/bin/python3.5
# -*- coding utf-8 -*-

"""
------------------------------------------------------------------------------------------------------

This utility is designed to handle applications for you and help you document yourapplication process.

------------------------------------------------------------------------------------------------------

************************************************BUtT**************************************************
+----------------------------(B)ewerber (U)nters(t)uetzungs-(T)ool-----------------------------------+
************************************************BUtT**************************************************

------------------------------------------------------------------------------------------------------

      This tool has been designed and implemented in 2017 by FABIAN STOLLER aka UnforcedError

------------------------------------------------------------------------------------------------------
"""

import sys
import click
import datetime
import enum
import re
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd


@enum.unique
class Status(enum.Enum):
    BEWERBUNG_IN_VORBEREITUNG = 0
    BEWERBUNG_ABGESCHICKT = 1
    TELEFONINTERVIEW = 2
    BEWERBUNGSGESPRAECH_VEREINBART = 3
    BEWERBUNGSGESPRAECH = 4
    WEITERE_GESPRAECHE = 5
    VERTRAGSANGEBOT = 6


class Communicator(object):

    modify_options = [
        'company',
        'job',
        'state',
        'active',
        'last_change',
        'contact'
    ]

    def __init__(self, table_name):
        self.__tablename__ = table_name

    @classmethod
    def print_csv(cls, sql_engine, filename):
        """
        Prints a .csv-File from the Database
        :return: /
        """
        cls.view_table(sql_engine)
        try:
            df = pd.read_sql_table('Applications', sql_engine)
        except ValueError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print('Error while opening the Applications-table from the database. Exception: % s' % exc_type)
            print(exc_traceback)
            return False

        df.to_csv(filename, sep='\t')

    @classmethod
    def view_table(cls, connectable):
        """
        Function to view the current state of the table
        :param connectable: sqlalchemy connectable
        :return:
        """
        df = pd.read_sql_table('Applications', connectable)
        if affirmation('Wollen Sie die gesamte Liste an Bewerbungen sehen:'):
            with pd.option_context('display.max_rows', None, 'display.max_columns', 7):
                print(df.to_string())

    @classmethod
    def modify_entry(cls, connectable, session, column_name):
        # df = pd.read_sql_table('Applications', connectable)
        print('Wähle eine Bewerbung aus die modifiziert werden soll: ')
        print('-------------------------------------------------------------------------')
        cls.view_table(connectable)
        print('-------------------------------------------------------------------------')
        id_str = ""
        while not re.findall(r'^[0-9]+$', id_str):
            id_str = get_string('Gib die ID der zu ändernden Bewerbung ein: ')
        id_int = int(id_str)
        row = session.query(Application).filter_by(id=id_int).first()
        if column_name == 'company':
            row.set_company(
                get_string('Gib den veränderten Namen der Firma ein: ')
            )
        elif column_name == 'job':
            row.set_job(
                get_string('Gib die veränderte Jobbezeichnung ein: ')
            )
        elif column_name == 'state':
            row.set_state(
                int(
                    get_string(create_state_prompt())
                )
            )
        elif column_name == 'last_changed':
            row.set_date(
                datetime.datetime.strptime(
                    get_string('Gib das Datum in der Form >> dd.mm.yyyy <<'), '%d.%m.%Y'
                )
            )
        elif column_name == 'active':
            row.set_active(
                bool(
                    get_string('Ist diese Bewerbung noch aktiv? "0" = Nein, "1" = Ja:')
                )
            )
        elif column_name == 'contact':
            row.set_contact(
                get_string('Gib die veränderten Kontaktdaten an')
            )

        session.commit()

        print('\nDer bearbeitete Eintrag sieht so aus: ')
        cls.view_table(connectable)

    @classmethod
    def add_entry(cls, session):
        """
        Adds a new application to the database
        :param session: open database session
        :return: /
        """
        print('Füge eine neue Bewerbung hinzu:')
        company = get_string('Gib den Namen der Firma ein: ')
        job = get_string('Gib die Stellenbezeichnung an: ')
        state = get_string(create_state_prompt())
        dat = datetime.datetime.strptime(get_string('Gib das Datum in der Form >> dd.mm.yyyy <<'), '%d.%m.%Y')
        active = affirmation('der Status >>aktiv<<')
        contact = get_string('Gib den Namen der kontaktperson an: ')
        if contact == "":
            contact = 'unknown'

        session.add(Application(company=company,
                                job=job,
                                state=state,
                                last_changed=dat,
                                active=active,
                                contact=contact
                                )
                    )
        session.commit()


def get_string(prompt):
    """
    Retrieves string through User-Interaction
    :param prompt is a prompt for the user-input
    :return string
    """
    user_input = input(prompt)

    if user_input != "":
        if affirmation(user_input):
            return user_input
        else:
            return get_string(prompt)
    else:
        return get_string(prompt)


def create_state_prompt():
    """
    Function to assemble an input-prompt for the application state
    :return: string containing the input-prompt
    """
    prompt = 'Please choose the current status of the new application.\nOptions:\n'
    for state in Status:
        prompt = prompt + state.name + ' Eingabe: >>> ' + str(state.value) + '\n'
    return prompt


def affirmation(user_input):
    """
    Get an affirmation for a input
    :param user_input from a previous prompt
    :return: returns boolean-value of the affirmation
    """
    if re.findall(r'^[0-6]$', user_input):
        affirm = input('Ist >%s< korrekt? [j/n]' % Status(int(user_input)).name)
    elif re.findall(r'^[7-9]$', user_input):
        print('Sie haben eine nicht vorhandene Option gewählt, bitte wöhlen Sie erneut!')
        return False
    else:
        affirm = input('Ist >%s< korrekt? [j/n]' % user_input)

    if affirm.upper() == 'J':
        return True
    else:
        return False


class AlreadyExistsException(BaseException):
    """This exception indicates that a row to be inserted in a database already exists"""
    def __init__(self, message, errors):
        """
        Initialises a new exception with an errormessage and an error-dictionary
        :param message: error-massage to be passed on to the super-class constructor
        :param errors: dict containing additional errors or corresponding information. Accessible through a member
        """
        super(AlreadyExistsException, self).__init__(message)
        self.errors = errors


class Application(declarative_base()):
    """
    This class represents a job-application and is used to store corresponding data in a SQLite3 database for
    documentation of my jobsearch.
    """
    __tablename__ = "Applications"
    id = Column(Integer, primary_key=True)
    company = Column(String(250))
    job = Column(String(250))
    state = Column(Integer)
    last_changed = Column(DateTime)
    active = Column(Boolean)
    contact = Column(String(250), nullable=True)

    def get_id(self):
        return self.id

    def get_company(self):
        return self.company

    def set_company(self, company_name):
        self.company = company_name
        print('Company wurde in %s geaendert' % self.company)

    def get_job(self):
        return self.job

    def set_job(self, job_description):
        self.job = job_description
        print('Job wurde in %s geaendert.' % self.job)

    def get_state(self):
        return self.state

    def set_state(self, status):
        self.state = status
        print('Status wurde in %s geaendert.' % self.state)

    def get_date(self):
        return self.last_changed

    def set_date(self, dat):
        self.last_changed = dat
        print('Das letzte Bearbeitungsdatum wurde zu %s geändert.' % self.last_changed.strftime('%d.%m.%Y'))

    def get_active(self):
        return self.active

    def set_active(self, active):
        self.active = active
        print('Bewerbung ist aktive? %s' % self.active)

    def get_contact(self):
        return self.contact

    def set_contact(self, contact):
        self.contact = contact
        print('Kontakt(e) für die Bewerbung ist %s' % self.contact)

    def as_list(self):
        """
        :return: a list of the mebers
        """
        return [
            self.company,
            self.job,
            # self.last_changed
        ]

    def __str__(self):
        return 'Application to ' + str(self.company) + ' for a position as ' + str(self.job)

    def __eq__(self, other):
        return (self.company == other.company) and (self.job == other.job)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    @classmethod
    def unique_insert(cls, session, app):
        """
        The purpose of this function is to insert a new row into the database only if it does not already exist
        :param session: sqlalchemy session object
        :param app: Application object to insert
        :return: returns nothing
        """
        exists = False
        for entry in session.query(Application).filter_by(company=app.company).all():
            if entry == app:
                exists = True
                print('Die Bewerbung %s existiert bereits im System' % entry)
                break
        if not exists:
            session.add(app)
            session.commit()
        else:
            raise AlreadyExistsException('\nERROR: while inserting into database:\n'
                                         '\tThe Row %s already exists\n' % app, {})


# noinspection PyPep8Naming
def connect_or_create_db(name, echo=False):
    """
    connects to a SQLite database using SQLalchemy code
    :param name: name of the database
    :param echo: flag to whether or not echo the database interaction to the console
    :return session: returns a session object to interact with the database
    """

    # splalchemy base
    Base = declarative_base()

    engine = create_engine('sqlite:///%s' % name, echo=echo)

    Base.metadata.create_all(engine)
    Base.metadata.bind = engine

    DBSession = sessionmaker(bind=engine)
    return DBSession(), engine


@click.command()
# option for displaying the whole table
@click.option('--display', is_flag=True, help='Will print the whole application-table to the screen')
@click.option('--add', is_flag=True, help='Will add a new row to the database')
@click.option('--modify', default='company', help='The argument >>TEXT<< specifies the field to modify')
@click.option('--out', default='out.csv', help='Option for printing the table to a .csv-file.\n'
                                               'The argument specifies the filnename. The default filename ist '
                                               '>>out.csv<<')
def main(display, add, modify, out):
    # create database connection
    session, engine = connect_or_create_db('test_1.db', echo=False)

    # choose which action to take in accordance to the given commandline option
    if display:
        Communicator.view_table(engine)
    elif add:
        Communicator.add_entry(session)
    elif out:
        Communicator.print_csv(engine, out)
    else:
        if modify.lower() in Communicator.modify_options:
            print('\nModify the %s of a row\n' % modify)
            Communicator.modify_entry(engine, session, modify.lower())
        else:
            options = ''
            for option in Communicator.modify_options:
                options = options + option + '\t'
            raise ValueError('Geben Sie einen korrekten Spaltennamen an.\n'
                             'Mögliche Optionen: %s' % options)


if __name__ == "__main__":
    main()

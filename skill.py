from pytlas import training, translations, intent, meta
from pytlas.handling.hooks import on_agent_created, on_agent_destroyed
import pytlas.settings as settings
from datetime import datetime
from threading import Thread
import dateutil
import sqlite3
import os
import time
import weakref
import logging

DEFAULT_SLEEP_TIME = 3.0
DEFAULT_TIMEOUT = 1.0

@training('en')
def en_training(): return """
%[add_reminder]
  remind me to @[reminder_object] @[reminder_date] at @[reminder_time]
  remind me @[reminder_date] at @[reminder_time] @[reminder_object]
  remind me every @[reminder_frequency] @[reminder_time] to @[reminder_object]
  remind me to @[reminder_object] every @[reminder_frequency] @[reminder_time] 

@[reminder_object]
  walk the dog
  call my wife
  do homework  
  buy a gift to my boss

@[reminder_frequency]
  day
  monday
  friday
  working day
  week
  month
  trimester
  semester

@[reminder_date](type=datetime)
  tomorrow
  next week
  25th of December

@[reminder_time](type=datetime)
  6 o'clock
  noon
  3:20
  in one hour  
"""

# And in other supported languages, we define the same TEMPLATE_SKILL_INTENT with
# appropriate data:

@training('fr')
def fr_training(): return """
%[add_reminder]
  rappelle moi @[reminder_date] de @[reminder_object]
  rappelle moi de @[reminder_object] @[reminder_date] 
  rappelle moi tous les @[reminder_frequency] @[reminder_time] de @[reminder_object]
  rappelle moi  de @[reminder_object] tous les @[reminder_frequency] @[reminder_time]

@[reminder_object]
  promender le chien
  appeler mon épouse
  faire mes devoirs
  acheter un cadeau pour mon patron

@[reminder_frequency]
  jour
  semaine
  mois
  jours ouvrés
  jours travaillés
  28 mars
  2 juillet

@[reminder_date](type=datetime)
  dans 1 heure
  demain
  aprés demain
  la semaine prochaine
  le 25 décembre

@[reminder_time](type=datetime)
  à 6 heure
  à midi
  à 3:20
"""

# Let's define some metadata for this skill. This step is optional but enables
# pytlas to list loaded skills with more informations:

@meta()
def template_skill_meta(_): return {
  'name': _('reminder'),
  'description': _('When you have no more heads you have pytlas'),
  'author': 'atlassistant',
  'version': '1.0.0',
  'homepage': 'https://github.com/atlassistant/pytlas-reminder',
}

# Now, adds some translations for supported languages:

@translations('fr')
def fr_translations(): return {
  'When do you want I remind you?' : 'Quand voulez vous que je vous le rappelle?',
  'What do you want I remind you?' : 'Quel est l\'objet du rappel?',
  'Ok I will remind you to {0} {1}' : 'Ok, je vous rappellerai de {0} le {1}',
}

# The final part is your handler registered to be called upon TEMPLATE_SKILL_INTENT
# recognition by the pytlas interpreter.


def calculate_next_occurence(date_reference, time_reference, occurence_type):
  if occurence_type == 'once':
    return datetime.combine(date_reference, time_reference)
  else:
    return datetime.now()

class ReminderMonitor(Thread):
  def __init__(self, reminder_db_path):
    super().__init__()
    self.reminder_db_path = reminder_db_path
    self.is_stopped = False
    self._logger = logging.getLogger(self.__class__.__name__.lower())
    self.date_format = "%Y-%m-%d"
    self.time_format = "%H:%M:%S"
    self.datetime_format = "{0} {1}".format(self.date_format, self.time_format)
    
  def run(self):
    self._logger.info("Monitor started")
    while (not self.is_stopped):
      if self.database_exists():
        self.proceed_reminder()
      time.sleep(DEFAULT_SLEEP_TIME)
    self._logger.info("Monitor ended")

  def stop(self):
    self._logger.info("Monitor stopping")
    self.is_stopped = True
    #self.join(DEFAULT_TIMEOUT)

  def proceed_reminder(self):
    global agents
    try:
      db_connection = sqlite3.connect(self.reminder_db_path)
      db_connection.cursor()
      occurences = self.select_occurences(db_connection)
      self.update_occurences(db_connection)
      db_connection.close()
      for occurence in occurences:
        for _agent_id, agent_ref in agents.items():
          if not agent_ref() == None:  
            agent_ref().answer(occurence[0])
    except Exception as _ex:
      pass

  def database_exists(self):
    return os.path.isfile(self.reminder_db_path)

  def update_occurences(self, db_connection):
    try:
      sql_command = """
      DELETE FROM reminder WHERE next_occurence <= ? AND frequency = 'once'
      """
      sql_parameters = (datetime.now().strftime(self.datetime_format),)
      db_connection.execute(sql_command, sql_parameters)
      db_connection.commit()
    except Exception as _ex:
      pass
  
  def select_occurences(self, db_connection):
    try:
      sql_command = """
      SELECT object from reminder WHERE next_occurence <= ?
      """
      sql_parameters = (datetime.now().strftime(self.datetime_format),)
      cur = db_connection.cursor()      
      cur.execute(sql_command, sql_parameters)
      occurences = cur.fetchall()
      return occurences
    except Exception as _ex:
      pass

  
  def create_database(self):
    db_connection = sqlite3.connect(self.reminder_db_path)
    db_connection.cursor()
    db_connection.execute("""
    CREATE TABLE IF NOT EXISTS reminder
    (id integer PRIMARY KEY,
    reference_date text,
    reference_time text,
    recurrence_type text,
    next_occurence text,
    object text)
    """)
    db_connection.commit()
    db_connection.close()

  def add_reminder(self, reminder_date, reminder_time, reminder_frequency, reminder_object, next_occurence):
    db_connection = sqlite3.connect(self.reminder_db_path)
    db_connection.cursor()
    insert_command = """
    INSERT INTO reminder
    (reference_date, reference_time, recurrence_type, object, next_occurence) 
    VALUES 
    (?,?,?,?,?)
    """
    insert_parameters = (reminder_date.strftime(self.date_format), reminder_time.strftime(self.time_format), reminder_frequency, reminder_object, next_occurence.strftime(self.datetime_format),)
    db_connection.execute(insert_command, insert_parameters)
    db_connection.commit()
    db_connection.close()  


agents={}
monitor = None


@on_agent_created()
def when_an_agent_is_created(agt):
  # On conserve une référence à l'agent
  global agents
  global monitor
  agt._logger.info("{0}".format(len(agents)))    

  if len(agents) == 0:
    reminder_db_path = agt.settings.get('reminder_db_path',section='reminder')
    if reminder_db_path == None:
      reminder_db_path = os.path.join(os.getcwd(),'pytlas_reminder.sqlite')    
    monitor = ReminderMonitor(reminder_db_path)
    monitor.start()
    agt._logger.info("Monitor started {0}".format(monitor.reminder_db_path))    
  agents[agt.id] =  weakref.ref(agt)
  pass

@on_agent_destroyed()
def when_an_agent_is_destroyed(agt):
  # On devrait clear les timers pour l'agent à ce moment là
  global agents
  global monitor
  agt._logger.info("Destroying agent")
  agents.pop(agt.id, None)  
  if len(agents) == 0 :
    agt._logger.info("Stopping monitor")
    monitor.stop()
  pass  

@intent('add_reminder')
def on_add_reminder_intent(req):
  global monitor
  if not monitor.database_exists():
    reminder_db_create_confirmed = req.intent.slot('reminder_db_create_confirmed').first().value
    if reminder_db_create_confirmed == None:
      return req.agent.ask('reminder_db_create_confirmed',\
      req._('Reminder database can not be found at {0}. A new database will be created in this location.\nDo you want continue?').format(monitor.reminder_db_path),\
      ['yes','no'])
    if reminder_db_create_confirmed == 'yes':
      try:
        monitor.create_database()
      except Exception as ex:
        req.agent.answer(req._('Unable to create database: {0}').format(ex))
        req.agent.done()      
    else:
      req.agent.answer(req._('Goodbye'))
      req.agent.done()

  reminder_date = req.intent.slot('reminder_date').first().value 
  reminder_frequency = req.intent.slot('reminder_frequency').first().value

  if  reminder_date == None and reminder_frequency == None:
    return req.agent.ask('reminder_date', req._('When do you want I remind you?'))

  if reminder_frequency == None:
    reminder_frequency = 'once'

  if reminder_date == None:
    reminder_date = datetime.now().date()  
  reminder_date_text = req._d(reminder_date, date_only=True)
  reminder_time = req.intent.slot('reminder_time').first().value
  if reminder_time == None:
    return req.agent.ask('reminder_time', req._('Wich time will fits you?'))
  reminder_time_text = req._d(reminder_time, time_only=True)

  reminder_object = req.intent.slot('reminder_object').first().value 
  if reminder_object == None:
    return req.agent.ask('reminder_object', req._('What do you want I remind you?'))
  next_occurence = calculate_next_occurence(reminder_date.date(), reminder_time.time(), reminder_frequency)

  try:
    monitor.add_reminder(reminder_date, reminder_time, reminder_frequency, reminder_object, next_occurence)
  except Exception as ex:
    req.agent.answer(req._('Unable to insert reminder in database: {0}').format(ex))
    req.agent.done()    

  if reminder_frequency == "once":
    answer_text = req._('Ok I will remind you {0} at {1} to {2}').format(reminder_date_text, reminder_time_text, reminder_object)
  else:
    answer_text = req._('Ok I will remind you to {0} every {1} at {3} starting {2}').format(reminder_object, reminder_frequency, reminder_date_text, reminder_time_text)
  req.agent.answer(answer_text)
  return req.agent.done()
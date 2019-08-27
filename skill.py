from pytlas import training, translations, intent, meta

# Hey there o/
# Glad you're taking some times to make a skill for the pytlas assistant!
# Here is all you have to know to make your own skills, let's go!

# Start by defining training data used to trigger your skill.
# Here we are defining the TEMPLATE_SKILL_INTENT with some training data.
# In english:

@training('en')
def en_training(): return """
%[add_reminder]
  add a reminder @[date] at @[time] to @[action]
  remind me @[date] at @[time] to @[action]
  remind me every @[frequency] at @[time] to @[action]
"""

# And in other supported languages, we define the same TEMPLATE_SKILL_INTENT with
# appropriate data:

@training('fr')
def fr_training(): return """
%[add_reminder]
  ajoute un rappel pour @[date] à @[time] de @[action]
  ajoute un rappel récurrent tous les @[frequency] à @[time] de @[action]
  rappelle moi tous les @[frequency] à @[time] de @[action]

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
  'Reminder': 'Rappel',
  'Hello from the reminder skill' : 'Bonjour depuis la compétence rappel'
}

# The final part is your handler registered to be called upon TEMPLATE_SKILL_INTENT
# recognition by the pytlas interpreter.

@intent('add_reminder')
def on_add_reminder_intent(req):

  # Using the pytlas API to communicate with the user: https://pytlas.readthedocs.io/en/latest/writing_skills/handler.html
 
  req.agent.answer(req._('Hello from the reminder skill'))

  return req.agent.done()

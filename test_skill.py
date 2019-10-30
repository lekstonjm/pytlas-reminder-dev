from sure import expect
from pytlas.testing import create_skill_agent
import os

# Testing a pytlas skill is easy.
# Start by instantiating an agent trained only for this skill.

agent = create_skill_agent(os.path.dirname(__file__), lang='en')

class TestTemplateSkill:

  def setup(self):
    # Between each tests, resets the model mock so calls are dismissed and we
    # start on a fresh state.
    # This will be usefull when you have more than one test method :)
    agent.model.reset()

  def test_it_should_launch_the_skill(self):
    # Now, try to trigger our skill
    pass

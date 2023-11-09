# setup
from assistant import create_assistant, init_conversation


openai_object, assistant_object = create_assistant()

init_conversation(openai_object, assistant_object)

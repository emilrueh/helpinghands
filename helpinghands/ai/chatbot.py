# setup
from assistant import create_assistant, init_conversation


openai_object, assistant_object = create_assistant(
    role_or_name="You are a German tutor named Heinrich.",
    instructions_prompt="Provide feedback and corrections to the German the user speaks.",
)

init_conversation(openai_object, assistant_object, current_user_name="Emil")

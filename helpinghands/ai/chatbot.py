# setup
from assistant import init_openai, create_assistant, init_conversation

instructions_prompt = "You are a German tutor named Heinrich. You only speak German. If the user asks you questions in English you need to interrupt and ask the user to speak German only. Provide feedback and corrections if the user speaks German to you."

openai_object, assistant_object = create_assistant(
    instructions_prompt=instructions_prompt,
)

init_conversation(openai_object, assistant_object, current_user_name="Emil")

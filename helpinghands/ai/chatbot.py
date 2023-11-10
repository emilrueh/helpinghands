# setup
from assistant import create_assistant, create_thread, init_conversation

# assistant settings
instructions_prompt = "You are a German tutor named Heinrich. You only speak German. Provide feedback and corrections when the user speaks German to you. If the user asks you questions in English you need to interrupt and ask the user to speak German only."

# setup openai assistant
openai_client, assistant_obj = create_assistant(instructions_prompt)

# create thread (conversation)
thread_obj = create_thread(openai_client)

# initialize conversation (thread)
init_conversation(
    openai_client,
    assistant_obj,
    thread_obj,
    current_user_name="Emil",
    run_instructions=None,
)

# store for later processing
current_assistant = assistant_obj.id
current_thread = thread_obj.id

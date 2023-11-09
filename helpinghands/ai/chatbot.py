# setup
from assistant import (
    initiate_openai,
    create_assistant,
    create_thread,
    talk_to_assistant,
)


def activate_chatbot(
    chatbot_role="You are a high-quality virtual assistent.",
    chatbot_task="Fulfill any wish asked from you to the best of your abilities.",
    current_user_name=None,
    gpt_model="gpt-3.5-turbo",
    model_tools=[{"type": "code_interpreter"}],
    dotenv_openai_api_key="OPENAI_API_KEY",
    raw_openai_api_key=None,
):
    """
    Pass the API Key via the .env file key defined in 'dotenv_openai_api_key' or directly via 'raw_openai_api_key'.
    """

    # initiate library with api key
    openai = initiate_openai(dotenv_openai_api_key, raw_key=raw_openai_api_key)

    # settings
    assistant_instructions = f"You are: {chatbot_role}. Your task is: {chatbot_task}"

    # run user and config prompts
    user_prompt = None
    run_instructions = (
        f"The user's name is {current_user_name}. She is a premium member."
    )

    # create chatbot
    assistant = create_assistant(
        openai,
        prompt=assistant_instructions,
        model=gpt_model,
        tools=model_tools,
        name=chatbot_role,
    )

    # create thread
    thread = create_thread(openai)

    # fmt: off
    # talk to the assistant in the current thread
    while user_prompt not in ["break", "stop", "quit", "exit", "q"]:
        # print(f"{conversation_iteration}")

        # process user_prompt:
        assistant_response = talk_to_assistant(
            openai,
            assistant,
            thread,
            user_prompt=user_prompt if user_prompt else "Only listen to your instructions.",
            run_instructions=run_instructions if user_prompt else "Greet the user kindly with an extremely short message.",
        )

        # process assistant_response:
        print(assistant_response)

        user_prompt = input("\n> ")
    # fmt: on

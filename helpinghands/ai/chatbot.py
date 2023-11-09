# setup
from assistant import (
    initiate_openai,
    create_assistant,
    create_thread,
    talk_to_assistant,
)


def activate_chatbot(
    chatbot_role="You are a high-quality virtual assistent named Timmy.",
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

    # initiate openai lib with api key
    openai = initiate_openai(dotenv_openai_api_key, raw_key=raw_openai_api_key)
    if openai.api_key is None:
        print("No 'OpenAI API Key' provided. Exiting...")
        return

    # settings
    greeting = "Greet the user kindly with an extremely short message."
    goodbye = "Bye, bye."
    if current_user_name:
        greeting += f"The user's name is {current_user_name}."

    # run user and config prompts
    user_prompt = None
    run_instructions = f"Be kind but concise."  # ???

    # create chatbot
    assistant = create_assistant(
        openai,
        prompt=chatbot_task,
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
            run_instructions=run_instructions if user_prompt else greeting,
        )

        # process assistant_response:
        print("\n", assistant_response)

        user_prompt = input("\n> ")
    # fmt: on

    print("\n", goodbye)


# test execution
activate_chatbot()

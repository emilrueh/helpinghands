from time import sleep


# setup
def init_openai(key_in_dotenv="OPENAI_API_KEY", raw_key=None):
    # imports
    import openai
    from dotenv import load_dotenv
    import os

    load_dotenv()
    openai_api_key = os.getenv(key_in_dotenv) or raw_key
    openai.api_key = openai_api_key
    return openai


def create_assistant(
    role_or_name=None,
    instructions_prompt=None,
    model="gpt-3.5-turbo",
    tools=[],
    dotenv_openai_api_key="OPENAI_API_KEY",
    raw_openai_api_key=None,
):
    """
    Pass the API Key via the .env file key defined in 'dotenv_openai_api_key' or directly via 'raw_openai_api_key'.
    """
    openai_object = init_openai(dotenv_openai_api_key, raw_key=raw_openai_api_key)
    if openai_object.api_key is None:
        print("No 'OpenAI API Key' provided. Exiting...")
        return

    assistant_object = openai_object.beta.assistants.create(
        instructions=instructions_prompt, model=model, tools=tools, name=role_or_name
    )
    return openai_object, assistant_object


# initiate new conversation
def create_thread(openai_object):
    return openai_object.beta.threads.create()


# add message to thread
def create_message(openai_object, thread_object, prompt, role="user"):
    return openai_object.beta.threads.messages.create(
        thread_id=thread_object.id,
        role=role,
        content=prompt,
    )


# process messages in thread
def create_run(openai_object, assistant_object, thread_object, prompt):
    return openai_object.beta.threads.runs.create(
        thread_id=thread_object.id,
        assistant_id=assistant_object.id,
        instructions=prompt,
    )


# get response from run
def retrieve_run(openai_object, thread_object, run_object):
    return openai_object.beta.threads.runs.retrieve(
        thread_id=thread_object.id, run_id=run_object.id
    )


def check_on_run(openai_object, thread_object, run_object):
    iteration = 0
    while True:
        run_response = retrieve_run(openai_object, thread_object, run_object)
        status = run_response.status

        # status check
        if status == "completed":
            break
        elif status in ["queued", "in_progress"]:
            if iteration < 1:
                # print(f"The run is {status}...")
                pass
        elif status == "requires_action":
            print("The run requires action...")
        elif status == "failed":
            print(
                f"The run has failed at {run_response.failed_at} due to {run_response.last_error}"
            )
            break
        else:
            print(f"Unexpected run status: {status}")
            break

        iteration += 1
        sleep(3)
    return run_object.id


# display all message in the conversation
def list_messages(openai_object, thread_object):
    return openai_object.beta.threads.messages.list(thread_id=thread_object.id)


# re-usable implementation
def talk_to_assistant(
    openai_object,
    assistant_object,
    thread_object,
    user_prompt: str,
    run_instructions: str = None,
):
    # create message and add to thread
    message = create_message(openai_object, thread_object, prompt=user_prompt)

    # create run for messages in thread
    run_object = create_run(
        openai_object, assistant_object, thread_object, prompt=run_instructions
    )

    # retrieve run object
    run_id = check_on_run(openai_object, thread_object, run_object)

    # list messages of a thread
    messages = list_messages(openai_object, thread_object)

    # access content of last message
    for message in messages.data:
        if message.run_id == run_id:
            reply = message.content[0].text.value

    # return message content
    return reply


def init_conversation(
    openai_object,
    assistant_object,
    thread_object,
    current_user_name=None,
):
    # settings
    greeting = "Introduce yourself briefly and greet the user kindly with an extremely short message."
    goodbye = "Bye, bye."
    if current_user_name:
        greeting += f"The user's name is {current_user_name}."

    user_prompt = greeting
    run_instructions = None  # ?

    # fmt: off
    # talk to the assistant in the current thread
    while user_prompt not in ["break", "stop", "quit", "exit", "q"]:
        # process user_prompt:
        assistant_response = talk_to_assistant(
            openai_object,
            assistant_object,
            thread_object,
            user_prompt=user_prompt,
            run_instructions=run_instructions,
        )

        # process assistant_response:
        print(f"\n{assistant_response}")

        user_prompt = input("\n> ")
    # fmt: on

    print(f"\n{goodbye}\n")

    return thread_object.id

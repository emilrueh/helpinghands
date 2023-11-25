from time import sleep
import pathlib

from ..ai.tts import text_to_speech
from ..audio.music import mix_voice_and_music
from ..data.text import write_to_txt_file

from .setup import init_openai_client


# setup
def create_assistant(
    instructions_prompt=None,
    role_or_name=None,
    model="gpt-3.5-turbo",
    tools=[],
    dotenv_openai_api_key="OPENAI_API_KEY",
    raw_openai_api_key=None,
):
    """
    Pass the API Key via the .env file key defined in 'dotenv_openai_api_key' or directly via 'raw_openai_api_key'.
    """
    openai_client = init_openai_client(
        dotenv_key=dotenv_openai_api_key, raw_api_key=raw_openai_api_key
    )
    if openai_client.api_key is None:
        print("\nNo 'OpenAI API Key' provided. Exiting...")
        quit()

    assistant_obj = openai_client.beta.assistants.create(
        instructions=instructions_prompt, model=model, tools=tools, name=role_or_name
    )
    return openai_client, assistant_obj


# initiate new conversation
def create_thread(openai_client):
    return openai_client.beta.threads.create()


# add message to thread
def create_message(openai_client, thread_obj, prompt, role="user"):
    return openai_client.beta.threads.messages.create(
        thread_id=thread_obj.id,
        role=role,
        content=prompt,
    )


# process messages in thread
def create_run(openai_client, assistant_obj, thread_obj, prompt):
    return openai_client.beta.threads.runs.create(
        thread_id=thread_obj.id,
        assistant_id=assistant_obj.id,
        instructions=prompt,
    )


# get response from run
def retrieve_run(openai_client, thread_obj, run_obj):
    return openai_client.beta.threads.runs.retrieve(
        thread_id=thread_obj.id, run_id=run_obj.id
    )


def check_on_run(openai_client, thread_obj, run_obj):
    iteration = 0
    while True:
        run_response = retrieve_run(openai_client, thread_obj, run_obj)
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
    return run_obj.id


# display all message in the conversation
def list_messages(openai_client, thread_obj):
    return openai_client.beta.threads.messages.list(thread_id=thread_obj.id)


# send message and get reply
def msg_create_send_receive(
    openai_client,
    assistant_obj,
    thread_obj,
    user_prompt: str,
    run_instructions: str = None,
):
    # create message and add to thread
    message = create_message(openai_client, thread_obj, prompt=user_prompt)

    # create run for messages in thread
    run_object = create_run(
        openai_client, assistant_obj, thread_obj, prompt=run_instructions
    )

    # retrieve run object
    run_id = check_on_run(openai_client, thread_obj, run_object)

    # list messages of a thread
    messages = list_messages(openai_client, thread_obj)

    # access content of last message
    for message in messages.data:
        if message.run_id == run_id:
            reply = message.content[0].text.value

    # return message content
    return reply


# CONVERSATION FUNCTIONS


# start new conversation
def init_conversation(
    role="You are a helpful assistant.",
    instructions="Your task is to assist the user with their questions.",
):
    # setup openai assistant
    openai_client, assistant_obj = create_assistant(
        instructions_prompt=instructions, role_or_name=role
    )

    # create thread (conversation)
    thread_obj = create_thread(openai_client)

    return openai_client, assistant_obj, thread_obj


# re-usable implementation
def have_conversation(
    openai_client=None,
    assistant_obj=None,
    thread_obj=None,
    current_user_name=None,
    initial_user_prompt="Hello. Who are you?",
    assistant_role=None,
    assistant_instructions=None,
    run_instructions=None,  # what do I use those run instructions for?
    conversation_id=None,
    output_processing="print",
    output_dir=None,
):
    if output_dir is not None:
        output_dir_obj = pathlib.Path(output_dir)

    # optional initial setup:
    #   - either start new conversation
    #   - or continue previous conversation

    # initialize new conversation and new assistant plus openai client
    if openai_client is None and assistant_obj is None and thread_obj is None:
        print("Initializing new conversation...")
        openai_client, assistant_obj, thread_obj = init_conversation(
            role=assistant_role, instructions=assistant_instructions
        )

    # print error for later implementation of seperate setup of client, assistant, thread, and conversation
    elif openai_client is None or assistant_obj is None or thread_obj is None:
        print(
            "Error: Sorry! The 'have_ conversation' function takes either all or none prerequisites.\nYou provided either one or two.\n\nExiting..."
        )
        quit()

    # continue a previous conversation
    elif conversation_id:
        pass  # thread managment

    # SETTINGS

    # fmt: off
    conv_iter = 0

    # add user name to conversation start if provided
    if current_user_name and initial_user_prompt:
        user_prompt = initial_user_prompt + f"My name is {current_user_name}"
    else:
        user_prompt = initial_user_prompt

    # CONVERSATION LOOP

    while user_prompt not in ["break", "stop", "quit", "exit", "q"]:
        #
        # PROCESS USER INPUT:
        print("Creating and sending message...")

        assistant_response = msg_create_send_receive(
            openai_client,
            assistant_obj,
            thread_obj,
            user_prompt=user_prompt,
            run_instructions=run_instructions,
        )

        # SAVING CONVERSATION TO .TXT FILE
        print("Saving iteration to .txt file...")

        # formatting of user and system reponses
        iter_fmt = f"Iteration: {conv_iter}"
        user_fmt = f"User:\n{user_prompt}"
        system_fmt = f"System:\n{assistant_response}"
        conversation_fmt = f"{iter_fmt}\n\n{user_fmt}\n\n{system_fmt}\n\n\n"

        write_to_txt_file(conversation_fmt, output_file_path=output_dir_obj / "conversation.txt")

        # SYSTEM OUTPUT
        print("Choosing system output...")

        system_output = choose_output(
            assistant_response,
            output_style=output_processing if conv_iter > 0 else "print",  # first output only prints
            output_dir=output_dir_obj,
        )
        # implement various outputs returned (or does it happen outside of the function?)
        #   - I guess it needs to happen inside the function (as otherwise how to loop?)

        # USER INPUT

        user_prompt = input("\n> ")
        conv_iter += 1

    print(f"\nBye bye.\n")

    # fmt: on

    # store and return for later processing
    assistant_id = assistant_obj.id
    thread_id = thread_obj.id

    return assistant_id, thread_id


# SELECT OUTPUT PROCESSING
def choose_output(
    text,
    output_style=None,
    output_dir=None,
):
    if output_style == "print":
        print(text)
    elif output_style == "voice":
        mix_voice_and_music(text_to_speech(text, output_dir), output_dir)

from time import sleep
from openai import OpenAI
from dotenv import load_dotenv
import os

from utility.data import choose_random_file
from audio.processing import bpm_match_two_files, play_sound, speaking


# setup
def init_openai_client(raw_api_key=None, dotenv_key=None):
    load_dotenv()

    api_key = (
        os.getenv(dotenv_key)
        if dotenv_key and dotenv_key != "OPENAI_API_KEY"
        else raw_api_key
    )

    return OpenAI(api_key=api_key)


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
def talk_to_assistant(
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


def init_conversation(
    role="You are a helpful assistant.",
    instructions="Your task is to do basic computer work.",
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
    initial_user_prompt="Hi, my name is {}",
    assistant_role=None,
    assistant_instructions=None,
    run_instructions=None,  # what do I use those run instructions for?
    conversation_id=None,
    output_processing="print",
    output_directory=None,
):
    # initialize new conversation and new assistant plus openai client
    if openai_client is None and assistant_obj is None and thread_obj is None:
        print("Initializing new conversation...")
        openai_client, assistant_obj, thread_obj = init_conversation(
            role=assistant_role, instructions=assistant_instructions
        )

    # error for later implementation of seperate setups
    elif openai_client is None or assistant_obj is None or thread_obj is None:
        print(
            "Error: Sorry! The 'have_ conversation' function takes either all or none prerequisites.\nYou provided either one or two.\n\nExiting..."
        )
        quit()

    # continue a previous conversation
    elif conversation_id:
        pass  # thread managment

    # settings

    # fmt: off
    # CONVERSATION LOOP
    # talk to the assistant in the current thread
    # add username to initial greeting if nothing else provided
    conversation_iteration = 0

    if current_user_name and initial_user_prompt and "{}" in initial_user_prompt:
        initial_user_prompt = initial_user_prompt.format(current_user_name)
    elif current_user_name and not initial_user_prompt:
        initial_user_prompt += current_user_name
    user_prompt = initial_user_prompt

    while user_prompt not in ["break", "stop", "quit", "exit", "q"]:

        # PROCESS USER INPUT:
        print("Processing...")
        assistant_response = talk_to_assistant(
            openai_client,
            assistant_obj,
            thread_obj,
            user_prompt=user_prompt,
            run_instructions=run_instructions,
        )

        # SYSTEM OUTPUT
        print("Choosing system output...")
        if conversation_iteration < 1:
            # choose simple print on first iteration
            system_output = choose_output(assistant_response, style="print")
        else:
            # choose voice output on concecutive iterations
            system_output = choose_output(assistant_response, style=output_processing, output_directory=output_directory)
        # print(system_output)
        # print(f"\n{system_output}")

        # USER INPUT
        user_prompt = input("\n> ")
        conversation_iteration += 1
    
    print(f"\nBye bye.\n")
    # fmt: on

    # store and return for later processing
    assistant_id = assistant_obj.id
    thread_id = thread_obj.id

    return assistant_id, thread_id


# Work In Progress:
# -----------------


# SELECT OUTPUT PROCESSING
def choose_output(text, style=None, output_directory=None):
    if style == "print":
        print(text)
    elif style == "voice":
        if output_directory is None:
            print("Warning: No output directory for gTTS specified.")
        voice_output(text, output_directory)


def voice_output(text, output_directory):
    # creating voice audio file
    voice_file_path = speaking(text, output_directory)

    # navigate to directories
    beats_dir = os.path.join(output_directory, "beats")
    adj_bpm_beats_dir = os.path.join(beats_dir, "adjusted_bpm")

    # choosing random file from dir
    random_music_file_path = choose_random_file(output_directory, "beats")

    # bpm matching of the two files
    new_voice_path, new_music_path = bpm_match_two_files(
        file_path_one=voice_file_path,
        file_path_two=random_music_file_path,
        output_dir=adj_bpm_beats_dir,
        tempo=120,
    )

    # playing voice
    play_sound(new_voice_path)
    # playing music (at lower volume)
    play_sound(new_music_path, volume=0.2)

from time import sleep


def initiate_openai(key_in_dotenv="OPENAI_API_KEY", raw_key=None):
    # setup
    import openai
    from dotenv import load_dotenv
    import os

    load_dotenv()
    openai_api_key = os.getenv(key_in_dotenv) or raw_key
    openai.api_key = openai_api_key
    return openai


def create_assistant(openai_object, prompt, model, tools=None, name=None):
    return openai_object.beta.assistants.create(
        instructions=prompt, model=model, tools=tools, name=name
    )


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


def check_run_status(openai_object, thread_object, run_object):
    iteration = 0
    while True:
        run_response = retrieve_run(openai_object, thread_object, run_object)
        status = run_response.status

        # status check
        if status == "completed":
            break
        elif status in ["queued", "in_progress"]:
            if iteration < 1:
                print(f"The run is {status}...")
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
    return status


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
    run_status = check_run_status(openai_object, thread_object, run_object)

    # list messages of a thread
    messages = list_messages(openai_object, thread_object)

    # access message content
    for message in messages:
        if message.role == "assistant":
            for content in message.content:
                response_message = content.text.value
                print(response_message)
        elif message.role == "user":
            pass
        else:
            response_message = f"No response available for message role: {message.role}"

    # return message content
    return response_message


# example usage:
"""
from assistant_funcs import (
    initiate_openai,
    create_assistant,
    create_thread,
    talk_to_assistant,
)

# initiate library with api key
openai = initiate_openai("OPENAI_API_KEY")


# prompts
assistant_name = "German Tutor"
assistant_instructions = "You are a personal German Tutor. Hold a conversation and write lessons and exercises to files for mistakes your student makes in the conversation as well as correcting the homework of your student."

user_prompt = "Hello, I have issues with the passive voice in German. Also, ich fahre ist aktiv. Aber es wird fahren ist Zukunft. Also wo ist der Passiv?"
run_instructions = "The user's name is Juli. She has a friendly attitude."

model = "gpt-4"
assistant_tools = [{"type": "code_interpreter"}]


# create assistant
assistant = create_assistant(
    openai,
    prompt=assistant_instructions,
    model=model,
    tools=assistant_tools,
    name=assistant_name,
)

# create thread
thread = create_thread(openai)

# talk to the assistant in the current thread
assistant_response = talk_to_assistant(
    openai,
    assistant,
    thread,
    user_prompt=user_prompt,
    run_instructions=run_instructions,
)

print(assistant_response)

"""

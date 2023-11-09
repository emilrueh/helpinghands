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
    run_status = check_on_run(openai_object, thread_object, run_object)

    # list messages of a thread
    messages = list_messages(openai_object, thread_object)

    # access content of last message
    for message in reversed(messages.data):
        if message.role == "assistant":
            reply = message.content[0].text.value

    # return message content
    return reply

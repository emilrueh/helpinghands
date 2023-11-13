# setup
from assistant import have_conversation

"""
need to do:
    - implement thread managment
    X refactor into function
"""

# assistant settings

# german_tutor
german_tutor_role = "You are a German tutor named Heinrich. You only speak German."
german_tutor_task = "Interrup and correct the user whenever they make gramatical and spelling mistakes speaking German to you. If the user asks questions in English you need to interrupt and ask the user to speak German only."

# freestyle_rapper
freestyle_rapper_words = input("\nEnter three words:\n> ")

freestyle_rapper_role = "You are a world class freestyle rapper."
freestyle_rapper_task = f"""
Your task is to write three emotional rap song verses with a chorus inbetween each. It has to be inspired by the following three words given by the user. 
Create an engaging storyline around the words. 
Make sure to use each word at least twice in a rhyme. 
Use a good rhyme pattern and a rythm that can go over any beat. 
Respond without saying 'verse 1' or 'chorus' or anyhting similar.

Here are the three words:
{freestyle_rapper_words}
"""
# Your response needs to be in formatted into json with each verse under its unique 'part' key.

# switches:
role = freestyle_rapper_role
task = freestyle_rapper_task

output = "voice"


# initialize conversation (thread)
have_conversation(
    current_user_name="Emil",
    assistant_role=role,
    assistant_instructions=task,
    run_instructions=None,  # what do I use those run instructions for?
    output_processing=output,
    output_directory=r"C:\Users\emilr\Code\libraries\helpinghands\helpinghands\ai\freestyle",
)

"""
> either import vision or write manually again for practice

1. initialize rapper
    - user prompts
        three words or topic
    - system instructions
        - role as freestyle rapper explanation
        - beats to choose from
            - have list of moods ready and analyze user input first for matching beat style
        - 
2. listen for user input
    - text or whisper
    - could be even listening live while rapping and never stop (possibly need for async)

3. analyze input and compare to previous conversations
    - can check against previously used phrases to not be repeating rhymes

4. output rap or rhymes
    - live output would be hard, so probably needs analyzing for first version and then spitting
    - output via text first and later via tts
        - first to terminal then to file
    
? where is the loop
! first only text in and out
X ! first only three words


prompts:

task = Your task is to write a short rap song inspired by the following three words given by the user. Create an engaging storyline around the words. Make sure to use each word at least twice in a rhyme. Use a good rhyme pattern and a rythm that can go over any beat. Never repeat the same rhyme. Your response needs to be in dict json format with each verse under its unique 'part' key. Here are the three words:
instructions = You are a world class freestyle rapper. {task}

1. vision.init_openai
2. whisper.listen
3. gpt.analyze
4. tts.speak

"""

import vision

# this is a chatbot actually brb

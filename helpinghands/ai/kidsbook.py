import vision, os


def write_and_illustrate_book(
    ai_role="You are a childrensbook author with a vivid fantasy and true to life descriptions of your characters.",
    instructions="Your task is to write a small story for children.",
    writing_style="Keep the sentences short but cute.",
    user_input_topic="A story about friendship in 20th century Berlin.",
    user_input_characters="A young lion, a baby duck, and two 87 year old twin grandmas from Brooklyn.",
    directory=r"C:\Users\emilr\Desktop\dalle_directory\childrens_book",
    special_character_images=["character_1.jpg"],
    reference_image_name="artstyle_reference.jpg",
):
    # base settings
    # topic and setting (optional)
    topic_and_setting = f"The topic and setting of the story: {user_input_topic}"

    # characters (optional)
    characters = f"Here are some of the most important characters in the story: {user_input_characters}"

    # special characters from images (optional)
    char_img_fmt = "Respond only with the description but headline each description seperately with three dollar signs $$$."
    character_image_prompt = f"Describe the characters you see as detailed and true to life as possible while still being concise and below 100 words per character. {char_img_fmt}"

    ## loading of images
    print("Loading images...")
    img_paths = [os.path.join(directory, img) for img in special_character_images]

    print("Converting images...")
    ## convert each img from path to base 64 string and add to list
    images_b64str = []
    for path in img_paths:
        char_img_b64str = vision.image_to_base64str(path)
        images_b64str.append(char_img_b64str)

    ## analyzing images
    print("Analyzing images...")
    special_characters = vision.view_image(
        images_in_base64str=[img_b64str for img_b64str in images_b64str],
        prompt=character_image_prompt,  # api call
    ).split("$$$")[1:]
    print(f"Special characters response = {special_characters}")

    ## adding special characters from images description to characters string
    for special_char in special_characters:
        characters += f"And another character: {special_char}"

    # image generation prompts and art style prompt generation
    print("Describing artstyle...")
    reference_image_path = os.path.join(directory, reference_image_name)
    reference_image_b64str = vision.image_to_base64str(reference_image_path)
    style_description = vision.view_image(
        prompt="Describe the art style of the image in the greatest detail. Format your reponse into a comma seperated list of descriptive words and phrases.",
        images_in_base64str=[reference_image_b64str],
        max_tokens=1000,
    )

    # combining of prompts
    print("Combining prompts...")
    full_ai_instructions = f"{ai_role} {instructions} {writing_style}"
    full_ai_prompt = f"Please write a story! Here is some inspiration: {topic_and_setting} {characters}"

    # gpt creating story
    print("GPT writing story...")
    story = vision.chat(full_ai_prompt, full_ai_instructions, model="gpt-4")

    # format into chapters
    print("Formatting chapters...")
    seperator = "Chapter"
    story_formatted = vision.chat(
        story,
        f"Seperate the story with the word '{seperator}' into short chapters.",
        model="gpt-4",
    )
    # split into chapters
    story_split = story_formatted.split(seperator)[1:]

    # generate image for each chapter
    print("Generating illustrations...")
    chapter_illustrations = []
    for chapter in story_split[1:]:  # 1: because 0 is empty for some reason
        chapter_img_prompt = f"{chapter}, {style_description}"
        print(chapter_img_prompt)
        # generate image
        while True:
            try:
                illustration = vision.generate_image(prompt=chapter_img_prompt)
                break
            except Exception as e:
                if "content_policy_violation" in str(e):
                    print(
                        f"\nEncountered content_policy_violation with prompt: {chapter_img_prompt}.\n\nRetrying...\n"
                    )
                    chapter_img_prompt = vision.chat(
                        instructions="Tweak the text slightly to not get flagged by a content policy violation.",
                        prompt=f"The text: {chapter_img_prompt}",
                    )
                    continue

        chapter_illustrations.append(illustration)
        # store text file

    # store illustrations to files
    print("Storing illustrations")
    chapter_ill_b64 = []
    for image_url in chapter_illustrations:
        # download url to b64
        image_b64 = vision.image_to_base64str(image_url)
        chapter_ill_b64.append(image_b64)
    ## save b64 as jpg
    vision.save_b64str_images_to_file(chapter_ill_b64, directory, file_extension="jpeg")
    print(f"Images saved to: {directory}")


write_and_illustrate_book(
    directory=r"C:\Users\emilr\Desktop\dalle_directory\childrens_book\medieval",
    user_input_topic="A medieval tale of honor and honesty.",
    user_input_characters="Three farmers and the king's goat.",
)

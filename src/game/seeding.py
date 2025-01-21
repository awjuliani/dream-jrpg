from src.game.response_manager import ResponseManager
import random
from src.game.response_manager import print_event_text

SETTING_QUESTIONS = [
    {
        "question": "What is the technological level of the world?",
        "answers": [
            "Prehistoric / Primitive",
            "Classical / Ancient",
            "Medieval / Middle Ages",
            "Early Modern / Renaissance",
            "Industrial / Steampunk",
            "Sci-fi / Cyberpunk",
        ],
    },
    {
        "question": "What is the look and feel of the world?",
        "answers": [
            "Mystical and Enchanted",
            "Grounded and Realistic",
            "Peaceful and Serene",
            "Rustic and Pastoral",
            "Dark and Gritty",
            "Surreal and Dreamlike",
        ],
    },
    {
        "question": "Is there anything special about this world you'd like to add?",
    },
]

PROTAGONIST_QUESTIONS = [
    {
        "question": "What is the protagonist's gender presentation?",
        "answers": [
            "Masculine",
            "Androgynous Male",
            "Feminine",
            "Androgynous Female",
            "Non-binary",
            "Protagonist is Non-human",
        ],
    },
    {
        "question": "What is the protagonist's personality?",
        "answers": [
            "Brave (Strength)",
            "Loyal (Defense)",
            "Clever (Intelligence)",
            "Kind (Wisdom)",
            "Energetic (Speed)",
            "Carefree (Luck)",
        ],
    },
    {
        "question": "Would you like to add any other details about your protagonist?",
    },
]

STORY_QUESTIONS = [
    {
        "question": "What is the thematic style of the story?",
        "answers": [
            "Light-hearted & Humorous",
            "Gritty & Hardboiled",
            "Romantic & Emotional",
            "Mysterious & Supernatural",
            "Political & Intriguing",
            "Philosophical & Thoughtful",
        ],
    },
    {
        "question": "Is there anything special about the narrative you'd like to add?",
    },
]


async def collect_seed_answers():
    await print_event_text(
        "Seeding your dream...",
        "You will be asked a series of questions to help generate your dream. Answer them however you like, or feel free to skip them if you'd prefer a surprise.",
    )

    answers = {}
    response_manager = ResponseManager()

    question_types = {
        "setting": SETTING_QUESTIONS,
        "protagonist": PROTAGONIST_QUESTIONS,
        "story": STORY_QUESTIONS,
    }

    for question_type, question_list in question_types.items():
        answers[question_type] = {}
        for question_data in question_list:
            question = question_data["question"]
            main_text = f"{question_type.capitalize()}: Seed Question {len(answers[question_type]) + 1}"

            # Check if it's the personality question
            is_personality_question = (
                question == "What is the protagonist's personality?"
            )

            if "answers" in question_data:
                # Remove "Skip" option for personality question
                options = question_data["answers"] + (
                    ["Random"] if is_personality_question else ["Random", "Skip"]
                )
                response_manager.set_game_response(
                    input_type="menu",
                    menu_options=options,
                    main_text=main_text,
                    sub_text=question,
                )
            else:
                response_manager.set_game_response(
                    input_type="text",
                    menu_options=[],
                    main_text=main_text,
                    sub_text=question,
                )
            response_manager.send_game_response()
            answer = await response_manager.get_player_response()

            if answer == "Random" and "answers" in question_data:
                answer = random.choice(question_data["answers"])

            if not (
                (not answer and "answers" not in question_data) or answer == "Skip"
            ):
                answers[question_type][question] = answer

    return answers

import json
import os
import re


# =========================================================
# PATH TO JSON FILE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

JSON_PATH = os.path.join(
    BASE_DIR,
    "faq_data.json"
)


# =========================================================
# LOAD FAQ DATA
# =========================================================

def load_faq_data():

    """
    Loads question bank and FAQs directly
    from faq_data.json.
    """

    if not os.path.exists(
            JSON_PATH
    ):

        raise FileNotFoundError(

            f"Could not find '{JSON_PATH}'. "
            f"Ensure faq_data.json exists "
            f"in the same folder as ai_chat.py."

        )


    with open(
            JSON_PATH,
            "r",
            encoding="utf-8"
    ) as file:

        data = json.load(
            file
        )


    return (
        data.get(
            "question_bank",
            []
        ),
        data.get(
            "faqs",
            []
        )
    )


QUESTION_BANK, FAQS = (
    load_faq_data()
)


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize_text(text):

    text = (
        str(text)
        .lower()
        .strip()
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# EXTRA PHRASES
#
# These allow short natural questions such as:
# "content ideas"
# "what should I post?"
# =========================================================

EXTRA_PHRASES = {

    "content_ideas": [

        "content ideas",
        "content idea",
        "give me ideas",
        "give me content ideas",
        "ideas for this trend",
        "what should i post",
        "what can i post",
        "what should i make",
        "video ideas",
        "post ideas",
        "creative ideas",
        "five ideas",
        "5 ideas"

    ],


    "trend_timing": [

        "too late",
        "is it too late",
        "late to join",
        "should i join",
        "join now",
        "good time to join"

    ],


    "future_popularity": [

        "stay popular",
        "still popular",
        "next month",
        "will it last",
        "will this last"

    ],


    "fading_risk": [

        "die soon",
        "fading risk",
        "death risk",
        "will it die",
        "will it fade",
        "dying"

    ],


    "stand_out": [

        "stand out",
        "make it unique",
        "different from others",
        "unique content"

    ],


    "competition_check": [

        "oversaturated",
        "too crowded",
        "competition",
        "competitive",
        "many creators"

    ],


    "spending_decision": [

        "worth spending",
        "spend money",
        "should i buy",
        "worth buying",
        "should i spend"

    ],


    "similar_trend": [

        "similar trend",
        "something similar",
        "alternative trend",
        "better trend",
        "other trend"

    ]

}


# =========================================================
# MATCH QUESTION TO TOPIC
# =========================================================

def find_topic(question):

    question = normalize_text(
        question
    )

    best_topic = None
    best_score = 0


    # -----------------------------------------------------
    # STEP 1:
    # MATCH FAQ KEYWORDS FROM JSON
    # -----------------------------------------------------

    for faq in FAQS:

        score = 0

        topic = faq.get(
            "topic"
        )

        keywords = faq.get(
            "keywords",
            []
        )


        for keyword in keywords:

            clean_keyword = normalize_text(
                keyword
            )


            if not clean_keyword:
                continue


            # Exact phrase match
            if clean_keyword in question:

                score += (
                        len(
                            clean_keyword.split()
                        )
                        * 3
                )


            # Word overlap
            keyword_words = set(
                clean_keyword.split()
            )

            question_words = set(
                question.split()
            )

            overlap = (
                    keyword_words
                    & question_words
            )

            score += len(
                overlap
            )


        # -------------------------------------------------
        # STEP 2:
        # EXTRA NATURAL LANGUAGE PHRASES
        # -------------------------------------------------

        extra_phrases = (
            EXTRA_PHRASES.get(
                topic,
                []
            )
        )


        for phrase in extra_phrases:

            clean_phrase = normalize_text(
                phrase
            )


            if clean_phrase in question:

                score += (
                        len(
                            clean_phrase.split()
                        )
                        * 4
                )


            phrase_words = set(
                clean_phrase.split()
            )

            question_words = set(
                question.split()
            )


            overlap = (
                    phrase_words
                    & question_words
            )


            score += len(
                overlap
            )


        if score > best_score:

            best_score = score
            best_topic = topic


    # Require at least a small match
    if best_score > 0:

        return best_topic


    return None


# =========================================================
# FIND MATCH FROM QUESTION BANK
# =========================================================

def find_question_bank_topic(
        question
):

    question = normalize_text(
        question
    )

    best_topic = None
    best_score = 0


    for item in QUESTION_BANK:

        example = normalize_text(
            item.get(
                "question",
                item.get(
                    "example_question",
                    ""
                )
            )
        )


        topic = item.get(
            "topic"
        )


        if not example:
            continue


        # Exact match
        if question == example:

            return topic


        # Word-overlap similarity
        question_words = set(
            question.split()
        )

        example_words = set(
            example.split()
        )

        overlap = (
                question_words
                & example_words
        )


        score = len(
            overlap
        )


        if score > best_score:

            best_score = score
            best_topic = topic


    if best_score >= 2:

        return best_topic


    return None


# =========================================================
# GENERATE CHATBOT REPLY
# =========================================================

def get_chatbot_reply(
        question,
        trend_result=None
):

    question = str(
        question
    ).strip()


    if not question:

        return (
            "Please type a question "
            "or select one of the "
            "suggested questions."
        )


    # -----------------------------------------------------
    # FIRST TRY FAQ KEYWORDS
    # -----------------------------------------------------

    topic = find_topic(
        question
    )


    # -----------------------------------------------------
    # THEN TRY QUESTION BANK
    # -----------------------------------------------------

    if topic is None:

        topic = (
            find_question_bank_topic(
                question
            )
        )


    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    if topic is None:

        return (

            "I'm LARPER's assistant. "
            "I can answer questions about "
            "trend growth, fading risk, "
            "recommendations, content ideas, "
            "budget tips, competition, "
            "and similar trends. "

            "Try asking something like "
            "'Give me content ideas' "
            "or 'Is it too late to join?'"

        )


    # =====================================================
    # FETCH ANSWER TEMPLATE
    # =====================================================

    template_answer = next(

        (
            faq.get(
                "answer"
            )

            for faq in FAQS

            if faq.get(
            "topic"
        )
               == topic
        ),

        (
            "I can help you explore this trend. "
            "Please try selecting one of "
            "the suggested questions."
        )

    )


    # =====================================================
    # GET CURRENT TREND DATA
    # =====================================================

    if (
            isinstance(
                trend_result,
                dict
            )
            and
            "error"
            not in trend_result
    ):

        trend = trend_result.get(
            "trend",
            "the selected trend"
        )

        category = trend_result.get(
            "category",
            "General"
        )

        status = trend_result.get(
            "trend_status",
            "Active"
        )

        growth_rate = trend_result.get(
            "growth_rate",
            0
        )

        growth_speed = trend_result.get(
            "growth_speed",
            "Stable"
        )

        death_risk = trend_result.get(
            "death_risk",
            0
        )

        worth_score = trend_result.get(
            "worth_score",
            0
        )

        recommendation = (
            trend_result.get(
                "recommendation",
                "MONITOR"
            )
        )


    else:

        trend = (
            "the selected trend"
        )

        category = "General"

        status = "Active"

        growth_rate = "N/A"

        growth_speed = "N/A"

        death_risk = "N/A"

        worth_score = "N/A"

        recommendation = (
            "MONITOR"
        )


    # =====================================================
    # FILL PLACEHOLDERS
    # =====================================================

    try:

        formatted_answer = (
            template_answer.format(

                trend=trend,

                category=category,

                status=status,

                growth_rate=
                growth_rate,

                growth_speed=
                growth_speed,

                death_risk=
                death_risk,

                worth_score=
                worth_score,

                recommendation=
                recommendation

            )
        )


    except KeyError as error:

        print(
            "Missing placeholder:",
            error
        )

        formatted_answer = (
            template_answer
        )


    return formatted_answer


# =========================================================
# TEST IN TERMINAL
# =========================================================

if __name__ == "__main__":

    fake_result = {

        "trend":
            "Dubai Chocolate",

        "category":
            "Food",

        "trend_status":
            "Too Crowded",

        "growth_rate":
            -12.5,

        "growth_speed":
            "Declining",

        "death_risk":
            68,

        "worth_score":
            42,

        "recommendation":
            "TRY SOMETHING SIMILAR"

    }


    print("\n")
    print(
        "=" * 55
    )

    print(
        "LARPER CHAT TEST"
    )

    print(
        "=" * 55
    )

    print(
        "\nType 'exit' to stop.\n"
    )


    while True:

        question = input(
            "You: "
        ).strip()


        if (
                question.lower()
                == "exit"
        ):

            break


        reply = (
            get_chatbot_reply(
                question,
                fake_result
            )
        )


        print(
            "\nLARPER:"
        )

        print(
            reply
        )

        print()
import json
import os

# =========================================================
# PATH TO JSON FILE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "faq_data.json")


def load_faq_data():
    """Loads question bank and FAQS directly from faq_data.json."""
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(
            f"Could not find '{JSON_PATH}'. Ensure faq_data.json exists in the same folder as ai_chat.py."
        )

    with open(JSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("question_bank", []), data.get("faqs", [])


QUESTION_BANK, FAQS = load_faq_data()


# =========================================================
# MATCH QUESTION TO TOPIC
# =========================================================

def find_topic(question):
    question = question.lower()
    best_topic = None
    best_score = 0

    for faq in FAQS:
        score = 0
        keywords = faq.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in question:
                # Prioritize longer, specific keyword matches
                score += len(keyword.split())

        if score > best_score:
            best_score = score
            best_topic = faq.get("topic")

    return best_topic


# =========================================================
# GENERATE CHATBOT REPLY WITH TEMPLATE PLACEHOLDERS
# =========================================================

def get_chatbot_reply(question, trend_result=None):
    question = str(question).strip()

    if not question:
        return "Please type a question or select one of the suggested questions."

    topic = find_topic(question)

    if topic is None:
        return (
            "I'm LARPER's rule-based assistant. I can answer questions about trend growth, "
            "fading risk, recommendations, content ideas, budget tips, and comparison limitations. "
            "Please select or ask one of the available suggested questions."
        )

    # Fetch answer template from JSON
    template_answer = next(
        (faq["answer"] for faq in FAQS if faq.get("topic") == topic),
        "I can help you explore this trend. Please try selecting one of the suggested questions."
    )

    # Extract dynamic variables from trend_result if present
    if isinstance(trend_result, dict) and "error" not in trend_result:
        trend = trend_result.get("trend", "the selected trend")
        category = trend_result.get("category", "General")
        status = trend_result.get("trend_status", "Active")
        growth_rate = trend_result.get("growth_rate", 0)
        growth_speed = trend_result.get("growth_speed", "Stable")
        death_risk = trend_result.get("death_risk", 0)
        worth_score = trend_result.get("worth_score", 0)
        recommendation = trend_result.get("recommendation", "MONITOR")
    else:
        trend = "the selected trend"
        category = "General"
        status = "Active"
        growth_rate = "N/A"
        growth_speed = "N/A"
        death_risk = "N/A"
        worth_score = "N/A"
        recommendation = "MONITOR"

    # Fill placeholders inside template answer
    formatted_answer = template_answer.format(
        trend=trend,
        category=category,
        status=status,
        growth_rate=growth_rate,
        growth_speed=growth_speed,
        death_risk=death_risk,
        worth_score=worth_score,
        recommendation=recommendation
    )

    return formatted_answer
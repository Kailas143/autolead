import os

def load_template(filename: str) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", filename)
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read().strip()
    return ""

# System Prompt
SYSTEM_PROMPT = load_template("system_prompt.txt")

# Modular Prompts
INTRO_PROMPT = load_template("intro_prompt.txt")
SUBJECT_PROMPT = load_template("subject_prompt.txt")
FULL_EMAIL_PROMPT = load_template("full_email_prompt.txt")
FOLLOWUP_PROMPT = load_template("followup_prompt.txt")
REPLY_CLASSIFIER_PROMPT = load_template("reply_classifier.txt")
LEAD_SCORING_PROMPT = load_template("lead_scoring_prompt.txt")
CONSULTANCY_PROMPT = load_template("consultancy_prompt.txt")
CLINIC_PROMPT = load_template("clinic_prompt.txt")
ECOMMERCE_PROMPT = load_template("ecommerce_prompt.txt")

# Legacy mapping for backward compatibility if needed
PERSONALIZATION_PROMPT = INTRO_PROMPT
REPLY_CLASSIFICATION_PROMPT = REPLY_CLASSIFIER_PROMPT

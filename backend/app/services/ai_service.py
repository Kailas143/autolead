import google.generativeai as genai
from app.core.config import settings
from app.prompts.outreach import (
    SYSTEM_PROMPT,
    INTRO_PROMPT,
    SUBJECT_PROMPT,
    FULL_EMAIL_PROMPT,
    FOLLOWUP_PROMPT,
    REPLY_CLASSIFIER_PROMPT,
    LEAD_SCORING_PROMPT,
    CONSULTANCY_PROMPT,
    CLINIC_PROMPT,
    ECOMMERCE_PROMPT
)
from typing import Optional, Any, Tuple
from sqlalchemy.orm import Session

class AIService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        genai.configure(api_key=api_key)
        # Using gemini-flash-latest for stable performance
        self.model_name = "gemini-flash-latest"

    async def _generate(self, prompt: str, temperature: float = 0.7) -> tuple[str, Any]:
        """
        Internal helper to generate content with a specific temperature.
        """
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT
        )
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
        )
        
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        text = response.text.strip()
        
        # --- AI CLEANER: Post-process to ensure correct tags ---
        import re
        # Convert AI's "helpful" phrases back to our system tags
        replacements = {
            r"(?i)your company": "{company}",
            r"(?i)the your industry": "{industry}",
            r"(?i)your industry": "{industry}",
            r"(?i)the industry": "{industry}",
            r"(?i)the company": "{company}",
            r"\[\[COMPANY\]\]": "{company}",
            r"\[\[INDUSTRY\]\]": "{industry}",
            r"\[\[FIRST_NAME\]\]": "{first_name}",
        }
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
            
        return text, response.usage_metadata

    async def generate_personalization(self, lead_data: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> str:
        """
        Generates a short personalized intro line for a lead.
        """
        prompt = INTRO_PROMPT.format(
            company=lead_data.get("company", "Unknown"),
            industry=lead_data.get("industry", "Unknown"),
            job_title=lead_data.get("title") or lead_data.get("job_title", "Professional"),
            website_summary=lead_data.get("company_info", "No summary available")
        )
        
        text, usage = await self._generate(prompt, temperature=0.7)
        if db and user_id:
            from app.services.audit_service import audit_service
            audit_service.track_ai_usage(db, user_id, self.model_name, usage.prompt_token_count, usage.candidates_token_count, "personalization")
        return text

    async def generate_subject_lines(self, company: str, industry: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> list[str]:
        """
        Generates 5 professional cold email subject lines.
        """
        prompt = SUBJECT_PROMPT.format(company=company, industry=industry)
        response_text, usage = await self._generate(prompt, temperature=0.8)
        
        if db and user_id:
            from app.services.audit_service import audit_service
            audit_service.track_ai_usage(db, user_id, self.model_name, usage.prompt_token_count, usage.candidates_token_count, "subject_lines")

        # Clean up the output (remove numbers, bullets, etc.)
        lines = [line.strip().strip("-").strip("12345. ").strip('"') for line in response_text.split("\n") if line.strip()]
        return lines[:5]

    async def generate_full_email(self, lead_data: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> str:
        """
        Generates a full concise cold outreach email, choosing a template based on industry.
        """
        industry = lead_data.get("industry", "").lower()
        
        template = FULL_EMAIL_PROMPT
        if "consult" in industry:
            template = CONSULTANCY_PROMPT
        elif "clinic" in industry or "medical" in industry or "health" in industry:
            template = CLINIC_PROMPT
        elif "ecommerce" in industry or "retail" in industry or "shop" in industry:
            template = ECOMMERCE_PROMPT
            
        prompt = template.format(
            first_name=lead_data.get("first_name", "there"),
            company=lead_data.get("company", "your company"),
            industry=lead_data.get("industry", "your industry"),
            job_title=lead_data.get("title") or lead_data.get("job_title", "Professional")
        )
        
        text, usage = await self._generate(prompt, temperature=0.7)
        if db and user_id:
            from app.services.audit_service import audit_service
            audit_service.track_ai_usage(db, user_id, self.model_name, usage.prompt_token_count, usage.candidates_token_count, "full_email")
        return text

    async def generate_followup(self, lead_data: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> str:
        """
        Generates a short professional follow-up email.
        """
        prompt = FOLLOWUP_PROMPT.format(
            first_name=lead_data.get("first_name", "there"),
            company=lead_data.get("company", "your company"),
            industry=lead_data.get("industry", "your industry")
        )
        text, usage = await self._generate(prompt, temperature=0.7)
        
        if db and user_id:
            from app.services.audit_service import audit_service
            audit_service.track_ai_usage(
                db, user_id, self.model_name, 
                usage.prompt_token_count, 
                usage.candidates_token_count, 
                "followup_generation"
            )
            
        return text

    async def classify_reply(self, email_body: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> str:
        """
        Classifies an email reply into: interested, not_interested, later, booked_call.
        """
        if not email_body or len(email_body.strip()) < 2:
            return "other"
            
        prompt = REPLY_CLASSIFIER_PROMPT.format(reply_text=email_body)
        classification, usage = await self._generate(prompt, temperature=0.1)
        
        if db and user_id:
            from app.services.audit_service import audit_service
            audit_service.track_ai_usage(db, user_id, self.model_name, usage.prompt_token_count, usage.candidates_token_count, "reply_classification")

        # Clean up classification
        classification = classification.lower().strip().replace(" ", "_").replace(".", "")
        
        valid_classifications = ["interested", "not_interested", "later", "booked_call"]
        if classification in valid_classifications:
            return classification
        return "other"

    async def score_lead(self, lead_data: dict, website_summary: str = "") -> dict:
        """
        Analyzes a lead and returns a score and reasoning.
        """
        prompt = LEAD_SCORING_PROMPT.format(
            industry=lead_data.get("industry", "Unknown"),
            company_size=lead_data.get("company_size", "Unknown"),
            website_summary=website_summary or lead_data.get("company_info", "N/A"),
            job_title=lead_data.get("title") or lead_data.get("job_title", "N/A")
        )
        
        response_text = await self._generate(prompt, temperature=0.2)
        return {"raw_analysis": response_text}

ai_service = AIService()

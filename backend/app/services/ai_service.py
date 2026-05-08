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

class AIService:
    def __init__(self):
        api_key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        genai.configure(api_key=api_key)
        # Using gemini-3-flash-preview as confirmed available in this environment
        self.model_name = "gemini-3-flash-preview"

    async def _generate(self, prompt: str, temperature: float = 0.7) -> str:
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
        return response.text.strip()

    async def generate_personalization(self, lead_data: dict, company_info: str = "") -> str:
        """
        Generates a short personalized intro line for a lead.
        """
        prompt = INTRO_PROMPT.format(
            company=lead_data.get("company", "Unknown"),
            industry=lead_data.get("industry", "Unknown"),
            job_title=lead_data.get("title") or lead_data.get("job_title", "Professional"),
            website_summary=company_info or lead_data.get("company_info", "No summary available")
        )
        
        return await self._generate(prompt, temperature=0.7)

    async def generate_subject_lines(self, company: str, industry: str) -> list[str]:
        """
        Generates 5 professional cold email subject lines.
        """
        prompt = SUBJECT_PROMPT.format(company=company, industry=industry)
        response_text = await self._generate(prompt, temperature=0.8)
        
        # Clean up the output (remove numbers, bullets, etc.)
        lines = [line.strip().strip("-").strip("12345. ").strip('"') for line in response_text.split("\n") if line.strip()]
        return lines[:5]

    async def generate_full_email(self, lead_data: dict) -> str:
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
        
        return await self._generate(prompt, temperature=0.7)

    async def generate_followup(self) -> str:
        """
        Generates a short follow-up email.
        """
        return await self._generate(FOLLOWUP_PROMPT, temperature=0.7)

    async def classify_reply(self, email_body: str) -> str:
        """
        Classifies an email reply into: interested, not_interested, later, booked_call.
        """
        prompt = REPLY_CLASSIFIER_PROMPT.format(reply_text=email_body)
        classification = await self._generate(prompt, temperature=0.1)
        
        # Clean up classification
        classification = classification.lower().strip().replace(" ", "_")
        
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

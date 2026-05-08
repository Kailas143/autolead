import csv
import io
from typing import List, Dict, Any, Union
from app.schemas.lead import LeadCreate

class CSVService:
    REQUIRED_COLUMNS = [
        "first_name", "last_name", "email"
    ]
    
    OPTIONAL_COLUMNS = [
        "company", "title", "linkedin_url", "website", "industry"
    ]

    def parse_apollo_csv(self, file_content: Union[bytes, str]) -> List[Dict[str, Any]]:
        """
        Parses a CSV file and returns a list of lead dictionaries.
        """
        leads = []
        if isinstance(file_content, bytes):
            content_str = file_content.decode("utf-8")
        else:
            content_str = file_content
            
        # Detect delimiter and quotechar
        try:
            dialect = csv.Sniffer().sniff(content_str[:2000])
            stream = io.StringIO(content_str)
            reader = csv.DictReader(stream, dialect=dialect)
        except Exception:
            # Fallback to default if sniffing fails
            stream = io.StringIO(content_str)
            reader = csv.DictReader(stream)
        
        if not reader.fieldnames:
            print("DEBUG: CSV has no headers")
            return []
            
        print(f"DEBUG: CSV Headers detected: {reader.fieldnames}")
        
        # Normalize headers (lowercase and underscores)
        headers = {h.lower().strip().replace(" ", "_"): h for h in reader.fieldnames}
        
        # Flexible mapping for common variations
        mapping = {
            "first_name": ["first_name", "first", "name"],
            "last_name": ["last_name", "last"],
            "email": ["email", "email_address", "work_email"],
            "company": ["company", "company_name", "organization", "account_name"],
            "title": ["title", "job_title", "role"],
            "industry": ["industry", "sector"],
            "linkedin_url": ["linkedin_url", "person_linkedin_url", "linkedin"],
            "website": ["website", "company_website", "domain"]
        }
        
        print(f"DEBUG: Normalized Headers Map: {headers}")
        
        for row in reader:
            print(f"DEBUG: Processing row: {row}")
            lead = {}
            # Map columns using flexible mapping
            for internal_key, variations in mapping.items():
                for var in variations:
                    original_col = headers.get(var)
                    if original_col and row.get(original_col):
                        lead[internal_key] = row[original_col]
                        break
            
            if not lead.get("company"):
                print(f"DEBUG: Warning - Company not found for row. Tried variations: {mapping['company']}")
            
            if all(lead.get(col) for col in self.REQUIRED_COLUMNS):
                leads.append(lead)
                
        return leads

    def validate_leads(self, leads: List[Dict[str, Any]]) -> List[LeadCreate]:
        """
        Validates lead data using Pydantic schemas.
        """
        validated_leads = []
        for lead_data in leads:
            try:
                validated_lead = LeadCreate(**lead_data)
                validated_leads.append(validated_lead)
            except Exception:
                # Log or skip invalid leads
                continue
        return validated_leads

csv_service = CSVService()

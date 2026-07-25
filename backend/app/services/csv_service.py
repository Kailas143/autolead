import csv
import io
import re
from typing import List, Dict, Any, Union
from urllib.parse import urlparse, parse_qs

import requests
from app.schemas.lead import LeadCreate

class CSVService:
    REQUIRED_COLUMNS = [
        "first_name", "last_name", "email"
    ]
    
    OPTIONAL_COLUMNS = [
        "company", "title", "linkedin_url", "website", "industry", "phone"
    ]

    def _normalize_header(self, header: str) -> str:
        return header.lower().strip().replace(" ", "_").replace("-", "_")

    def _build_headers(self, fieldnames: List[str]) -> Dict[str, str]:
        return {self._normalize_header(h): h for h in fieldnames if h}

    def _get_field(self, row: Dict[str, Any], headers: Dict[str, str], keys: List[str]) -> str:
        for key in keys:
            col = headers.get(key)
            if col and row.get(col) is not None:
                return str(row.get(col)).strip()
        return ""

    def _extract_sheet_id(self, sheet_url: str) -> str:
        patterns = [
            r"/spreadsheets/d/([a-zA-Z0-9-_]+)",
            r"/spreadsheets/u/\d+/d/([a-zA-Z0-9-_]+)",
            r"/\*/([a-zA-Z0-9-_]+)(?:\?|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, sheet_url)
            if match:
                return match.group(1)

        parsed = urlparse(sheet_url)
        path_segments = [segment for segment in parsed.path.split("/") if segment and segment != "*"]
        for segment in reversed(path_segments):
            if re.fullmatch(r"[a-zA-Z0-9-_]{20,}", segment):
                return segment

        raise ValueError("Invalid Google Sheet URL format. Please use a full Google Sheets link.")

    def _extract_gid(self, sheet_url: str) -> str:
        parsed = urlparse(sheet_url)
        params = parse_qs(parsed.query)

        for key in ("gid", "sheet"):
            value = params.get(key, [None])[0]
            if value and value.isdigit():
                return value

        gid_match = re.search(r"gid=(\d+)", sheet_url)
        if gid_match:
            return gid_match.group(1)

        return "0"

    def _rows_to_csv(self, rows: List[List[Any]]) -> str:
        if not rows:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow(["" if value is None else str(value) for value in row])
        return output.getvalue()

    def _build_google_sheet_candidate_urls(self, sheet_url: str) -> List[str]:
        sheet_id = self._extract_sheet_id(sheet_url)
        gid = self._extract_gid(sheet_url)
        return [
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
            f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
        ]

    def _looks_like_html(self, content: str) -> bool:
        sample = content.lstrip().lower()
        return sample.startswith("<!doctype html") or sample.startswith("<html")

    def fetch_google_sheet_csv(self, sheet_url: str) -> str:
        if not sheet_url:
            raise ValueError("Google Sheet URL is required")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        last_error = None
        for candidate_url in self._build_google_sheet_candidate_urls(sheet_url):
            try:
                response = requests.get(candidate_url, headers=headers, timeout=15, allow_redirects=True)
                response.raise_for_status()

                body = response.text.lstrip("\ufeff").strip()
                if not body:
                    raise ValueError("The selected Google Sheet tab is empty.")
                if self._looks_like_html(body):
                    raise ValueError("Google returned an HTML page instead of CSV data.")

                return response.text
            except (requests.exceptions.RequestException, ValueError) as e:
                last_error = e

        raise ValueError(
            "Could not access this Google Sheet. Please use the normal docs.google.com sheet URL and make sure the sheet is public or published as CSV."
        ) from last_error

    def parse_csv(self, file_content: Union[bytes, str], source: str = "apollo") -> List[Dict[str, Any]]:
        """
        Parses a CSV file and returns a list of lead dictionaries.
        """
        leads = []
        if isinstance(file_content, bytes):
            content_str = file_content.decode("utf-8-sig")
        else:
            content_str = file_content.lstrip('\ufeff')
            
        try:
            dialect = csv.Sniffer().sniff(content_str[:2000])
            stream = io.StringIO(content_str)
            reader = csv.DictReader(stream, dialect=dialect)
        except Exception:
            stream = io.StringIO(content_str)
            reader = csv.DictReader(stream)
        
        if not reader.fieldnames:
            print("DEBUG: CSV has no headers")
            return []
            
        print(f"DEBUG: CSV Headers detected: {reader.fieldnames}")
        
        headers = self._build_headers(reader.fieldnames)
        print(f"DEBUG: Normalized Headers Map: {headers}")

        mapping = {
            "first_name": ["first_name", "first", "name"],
            "last_name": ["last_name", "last"],
            "email": ["email", "email_address", "work_email"],
            "company": ["company", "company_name", "organization", "account_name"],
            "phone": ["phone", "phone_number", "mobile", "mobile_number", "whatsapp", "whatsapp_number"],
            "title": ["title", "job_title", "role"],
            "industry": ["industry", "sector", "type"],
            "linkedin_url": ["linkedin_url", "person_linkedin_url", "linkedin"],
            "website": ["website", "company_website", "domain"],
            "store_name": ["store_name", "store"],
            "city_area": ["city_area", "city/area", "city", "area"],
            "address": ["address", "location"],
            "notes": ["notes", "outreach_status"]
        }
        
        row_count = 0
        for row in reader:
            row_count += 1
            lead = {}
            for internal_key, variations in mapping.items():
                for var in variations:
                    original_col = headers.get(var)
                    if original_col and row.get(original_col):
                        lead[internal_key] = str(row[original_col]).strip()
                        break
            
            if not lead.get("company") and lead.get("store_name"):
                lead["company"] = lead["store_name"]
            if not lead.get("store_name") and lead.get("company"):
                lead["store_name"] = lead["company"]
            if not lead.get("company") and lead.get("first_name") and not lead.get("last_name"):
                lead["company"] = lead["first_name"]
            
            if not lead.get("first_name"):
                if lead.get("company"):
                    parts = str(lead["company"]).split()
                    lead["first_name"] = parts[0]
                    lead["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else None
                elif lead.get("store_name"):
                    parts = str(lead["store_name"]).split()
                    lead["first_name"] = parts[0]
                    lead["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else None

            if lead.get("phone") or lead.get("email"):
                leads.append(lead)
                print(f"DEBUG: Row {row_count} parsed successfully - {lead.get('first_name')} {lead.get('last_name')} ({lead.get('email')}, {lead.get('phone')})")
            else:
                print(f"DEBUG: Row {row_count} skipped - no phone or email found.")
                
        print(f"DEBUG: Parsed {len(leads)} leads from {row_count} rows")
        return leads
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

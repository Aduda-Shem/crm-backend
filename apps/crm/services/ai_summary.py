"""
AI-powered notes summary service using Google Gemini API.
"""

import os
import logging
from typing import List, Optional
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_AVAILABLE = True

class AISummaryService:
    """Service for generating AI-powered summaries of lead notes."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
                self.model = None
        else:
            logger.warning("Gemini API key not configured or package not available")
    
    def summarize_notes(self, notes: List[str], lead_name: str = "Lead") -> str:
        """
        Generate an AI summary of the provided notes.
        
        Args:
            notes: List of note content strings
            lead_name: Name of the lead for context
            
        Returns:
            AI-generated summary or fallback message
        """
        if not notes:
            return "No notes available for this lead."
        
        if not self.model:
            return self._generate_fallback_summary(notes, lead_name)
        
        # Prepare context for the AI
        context = self._prepare_context(notes, lead_name)
            
        # Generate prompt for summary
        prompt = self._create_summary_prompt(context)
            
        # Get AI response
        response = self.model.generate_content(prompt)
            
        if response and response.text:
            return response.text.strip()
        else:
            logger.warning("Empty response from Gemini AI")
            return self._generate_fallback_summary(notes, lead_name)
                

    
    def _prepare_context(self, notes: List[str], lead_name: str) -> str:
        """Prepare context string from notes."""
        if len(notes) == 1:
            return f"Note for {lead_name}:\n{notes[0]}"
        
        context_parts = [f"Notes for {lead_name}:"]
        for i, note in enumerate(notes, 1):
            context_parts.append(f"\nNote {i}:\n{note}")
        
        return "\n".join(context_parts)
    
    def _create_summary_prompt(self, context: str) -> str:
        """Create the prompt for the AI model."""
        return f"""
You are a sales assistant helping to summarize lead notes. Please provide a concise, professional summary of the following notes:

{context}

Please provide:
1. A brief overview of the lead's current situation
2. Key points from the notes
3. Any action items or follow-ups needed
4. Overall sentiment or progress indication

Keep the summary professional and actionable. Focus on the most important information that would help a sales team understand the lead's status.
"""
    
    def _generate_fallback_summary(self, notes: List[str], lead_name: str) -> str:
        """Generate a basic summary when AI is unavailable."""
        if len(notes) == 1:
            return f"Summary for {lead_name}: {notes[0][:200]}{'...' if len(notes[0]) > 200 else ''}"
        
        summary_parts = [f"Summary for {lead_name}:"]
        summary_parts.append(f"Total notes: {len(notes)}")
        
        # Get the most recent note content
        latest_note = notes[0] if notes else ""
        if latest_note:
            summary_parts.append(f"Latest note: {latest_note[:150]}{'...' if len(latest_note) > 150 else ''}")
        
        summary_parts.append("(AI summary unavailable - showing basic summary)")
        
        return "\n".join(summary_parts)
    
    def is_available(self) -> bool:
        """Check if the AI service is available."""
        return self.model is not None


# Global instance
ai_summary_service = AISummaryService()


def summarize_notes(notes: List[str], lead_name: str = "Lead") -> str:
    """
    Convenience function to summarize notes using the AI service.
    
    Args:
        notes: List of note content strings
        lead_name: Name of the lead for context
        
    Returns:
        AI-generated summary or fallback message
    """
    return ai_summary_service.summarize_notes(notes, lead_name)

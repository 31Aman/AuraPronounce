import json
import re
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

class LLMFeedbackService:
    @staticmethod
    def generate_feedback(
        overall_score: float,
        accuracy_score: float,
        fluency_score: float,
        discrepancies: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate AI feedback on pronunciation.
        Returns a tuple of (general_feedback_text, list_of_word_feedback_dicts)."""
        
        # 1. Base structured feedback generated via rules (Expert System Fallback)
        word_feedback = []
        for d in discrepancies:
            word = d["word"]
            # Avoid duplicating word feedback in the list
            if any(f["word"] == word for f in word_feedback):
                continue
                
            word_feedback.append({
                "word": word,
                "issue": d.get("issue", "Unclear pronunciation"),
                "correct_pronunciation": d.get("correct_pronunciation", f"/{word.lower()}/"),
                "suggestion": d.get("suggestion", "Practice slowly and focus on vowel clarity."),
                "difficulty_level": "Medium" if len(word) > 5 else "Easy"
            })

        # Add fallback entries if no discrepancies were parsed but accuracy is low
        if not word_feedback and accuracy_score < 80.0:
            word_feedback.append({
                "word": "General Speaking",
                "issue": "Weak vowel definition",
                "correct_pronunciation": "Various vowel phonemes",
                "suggestion": "Make sure to open your mouth wider on sounds like /æ/ (as in cat) and /ɑː/ (as in father).",
                "difficulty_level": "Medium"
            })

        # 2. General feedback text
        general_feedback = ""
        if overall_score >= 85.0:
            general_feedback = (
                "Excellent work! Your pronunciation is highly intelligible, and you demonstrate "
                "strong control over English phonemes, speech rhythm, and pacing. Your speaking rate "
                "is natural, and pauses are placed appropriately. To reach native-like fluency, focus "
                "on subtle intonation changes during complex sentences."
            )
        elif 70.0 <= overall_score < 85.0:
            general_feedback = (
                "Good job! Your speech is mostly clear and understandable. However, there are a few "
                "words where phoneme substitutions (like replacing TH with T/D) affect your accuracy. "
                "Additionally, your rhythm is slightly uneven in parts, likely due to pauses as you plan "
                "your speech. Practice reading aloud and focusing on linking words together."
            )
        else:
            general_feedback = (
                "You have a solid foundation, but there are significant areas for improvement. "
                "Several key vowel and consonant sounds are currently being substituted or spoken Unclearly, "
                "which reduces overall intelligibility. Your pace is also slightly hesitant with frequent "
                "pauses. We recommend practicing core articulation exercises, focusing particularly on "
                "dental fricatives (TH sounds) and lip/tongue placements for vowels."
            )

        # Try to call LLMs for rich generation if keys are present
        if settings.GROQ_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1"
                )
                prompt = f"""
                You are an expert English Pronunciation Coach.
                Analyze these scores:
                - Overall Score: {overall_score}/100
                - Accuracy Score: {accuracy_score}/100
                - Fluency Score: {fluency_score}/100
                
                These word-level mistakes were identified:
                {json.dumps(word_feedback, indent=2)}
                
                Generate a JSON object containing:
                1. "general_feedback": A detailed, encouraging paragraph of general feedback (3-5 sentences).
                2. "word_feedback": The list of word mistakes, enriched with specific physical articulation suggestions, phonetic spellings, and correct practice suggestions.
                
                Ensure the returned text is strictly valid JSON matching this schema:
                {{
                   "general_feedback": "string",
                   "word_feedback": [
                      {{
                         "word": "string",
                         "issue": "string",
                         "correct_pronunciation": "string",
                         "suggestion": "string",
                         "difficulty_level": "string"
                      }}
                   ]
                }}
                """
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                res_data = json.loads(response.choices[0].message.content)
                return res_data.get("general_feedback", general_feedback), res_data.get("word_feedback", word_feedback)
            except Exception:
                pass

        # Try to call LLMs for rich generation if keys are present
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = f"""
                You are an expert English Pronunciation Coach.
                Analyze these scores:
                - Overall Score: {overall_score}/100
                - Accuracy Score: {accuracy_score}/100
                - Fluency Score: {fluency_score}/100
                
                These word-level mistakes were identified:
                {json.dumps(word_feedback, indent=2)}
                
                Generate a JSON object containing:
                1. "general_feedback": A detailed, encouraging paragraph of general feedback (3-5 sentences).
                2. "word_feedback": The list of word mistakes, enriched with specific physical articulation suggestions, phonetic spellings, and correct practice suggestions.
                
                Ensure the returned text is strictly valid JSON matching this schema:
                {{
                   "general_feedback": "string",
                   "word_feedback": [
                      {{
                         "word": "string",
                         "issue": "string",
                         "correct_pronunciation": "string",
                         "suggestion": "string",
                         "difficulty_level": "string"
                      }}
                   ]
                }}
                """
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                res_data = json.loads(response.choices[0].message.content)
                return res_data.get("general_feedback", general_feedback), res_data.get("word_feedback", word_feedback)
            except Exception:
                pass

        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"""
                You are an expert English Pronunciation Coach.
                Analyze these scores:
                - Overall Score: {overall_score}/100
                - Accuracy Score: {accuracy_score}/100
                - Fluency Score: {fluency_score}/100
                
                These word-level mistakes were identified:
                {json.dumps(word_feedback, indent=2)}
                
                Generate a JSON object matching this schema. Return ONLY valid JSON:
                {{
                   "general_feedback": "detailed feedback text...",
                   "word_feedback": [
                      {{
                         "word": "word",
                         "issue": "issue description",
                         "correct_pronunciation": "/phonetic_guide/",
                         "suggestion": "articulation tips",
                         "difficulty_level": "Easy/Medium/Hard"
                      }}
                   ]
                }}
                """
                response = model.generate_content(prompt)
                json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
                if json_match:
                    res_data = json.loads(json_match.group(0))
                    return res_data.get("general_feedback", general_feedback), res_data.get("word_feedback", word_feedback)
            except Exception:
                pass

        return general_feedback, word_feedback

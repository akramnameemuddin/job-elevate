"""
AI Service for ONE-TIME Question Generation
Minimizes token usage through persistent caching in QuestionBank
"""
import os
import json
import logging
import random
import time
from typing import List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)

# HYBRID APPROACH: Templates first, AI as fallback for new skills
# Primary: Use template questions (unlimited, fast, free)
# Fallback: Use AI when recruiter adds new skill without templates
# Last resort: Generic template questions
try:
    from google import genai
    from google.genai import types
    # Initialize with new SDK
    GEMINI_CLIENT = genai.Client(api_key=settings.GOOGLE_API_KEY)
    # Use stable model with free tier quota (gemini-2.5-flash is latest stable)
    GEMINI_MODEL = 'models/gemini-2.5-flash'
    GEMINI_AVAILABLE = True
    API_VERSION = 'new'  # Flag for new API
    logger.info(f"✓ AI enabled as FALLBACK using {GEMINI_MODEL} (templates still preferred)")
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_CLIENT = None
    GEMINI_MODEL = None
    API_VERSION = None
    logger.warning(f"✗ AI unavailable - will use template questions only: {str(e)[:100]}")


class QuestionGeneratorService:
    """
    Service to generate questions for skills using AI.
    CALLED ONLY ONCE PER SKILL. Results stored in QuestionBank forever.
    """
    
    def __init__(self):
        # Try GEMINI_API_KEY first, then GOOGLE_API_KEY for backwards compatibility
        self.api_key = (
            getattr(settings, 'GEMINI_API_KEY', None) or 
            getattr(settings, 'GOOGLE_API_KEY', None) or
            os.getenv('GEMINI_API_KEY') or 
            os.getenv('GOOGLE_API_KEY')
        )
        # Use stable model with free tier quota
        self.model_name = getattr(settings, 'GEMINI_MODEL', GEMINI_MODEL if GEMINI_AVAILABLE else 'gemini-1.5-flash')
        
        if GEMINI_AVAILABLE and self.api_key:
            # New google.genai API (v1.x+)
            self.client = GEMINI_CLIENT
            self.ai_available = True
            logger.info(f"AI Service initialized with {self.model_name} (new SDK)")
        else:
            self.ai_available = False
            self.client = None
            logger.warning("AI Service not available - using fallback templates")
    
    def generate_questions(self, skill_name: str, skill_description: str = "", 
                          difficulty: str = None, count: int = 8) -> List[Dict]:
        """
        Generate MCQ questions for a skill using AI.
        Returns list of question dictionaries.
        
        Args:
            skill_name: Name of the skill
            skill_description: Optional description for context
            difficulty: Optional difficulty filter ('easy', 'medium', 'hard')
            count: Number of questions to generate (default: 8)
        
        CRITICAL: This is called ONLY ONCE per skill (per difficulty batch).
        """
        logger.info(f"Generating {count} AI questions for skill: {skill_name}" + 
                   (f" (difficulty: {difficulty})" if difficulty else ""))
        
        # Use AI generation
        if not self.ai_available:
            logger.error("AI service not available - cannot generate questions")
            return []
        
        try:
            questions = self._generate_with_ai(skill_name, skill_description, difficulty, count)
            if questions and len(questions) >= min(count // 2, 1):
                logger.info(f"✓ AI generated {len(questions)} questions for {skill_name}")
                return questions
            else:
                logger.error(f"AI returned insufficient questions for {skill_name}")
                return []
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return []
    
    def _generate_with_ai(self, skill_name: str, skill_description: str, 
                         difficulty: str = None, count: int = 8) -> List[Dict]:
        """
        Generate questions using Google Gemini AI.
        
        ANTI-CHEATING PROMPT: Explicitly instructs AI to randomize correct option positions.
        """
        # Build difficulty-specific prompt
        if difficulty:
            difficulty_instruction = f"- ALL {count} questions at {difficulty.upper()} difficulty"
            difficulty_desc = {
                'easy': 'basic concepts, definitions, and simple applications',
                'medium': 'practical applications, problem-solving, and best practices',
                'hard': 'advanced concepts, optimization, architecture, and edge cases'
            }.get(difficulty.lower(), 'general knowledge')
        elif count == 20:
            # Special case: Generate all 20 questions with proper distribution in ONE API call
            difficulty_instruction = """- 8 questions at EASY difficulty (basic concepts, definitions, and simple applications)
   - 6 questions at MEDIUM difficulty (practical applications, problem-solving, and best practices)
   - 6 questions at HARD difficulty (advanced concepts, optimization, architecture, and edge cases)"""
            difficulty_desc = "mixed difficulty levels with proper distribution"
        else:
            difficulty_instruction = f"""- 3 questions at EASY difficulty
   - 3 questions at MEDIUM difficulty
   - 2 questions at HARD difficulty"""
            difficulty_desc = "mixed difficulty levels"
        
        prompt = f"""Generate {count} multiple-choice questions to assess proficiency in {skill_name}.

Skill Description: {skill_description if skill_description else "General knowledge and practical application"}
Focus: {difficulty_desc}

REQUIREMENTS:
1. Generate EXACTLY {count} questions:
   {difficulty_instruction}

2. Return valid JSON with this exact structure:
{{
  "questions": [
    {{
      "question_text": "Your question here",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Option 1",
      "difficulty": "easy",
      "explanation": "Brief explanation"
    }}
  ]
}}

3. TEXT RULES:
   - Keep all text simple
   - No special characters
   - No quotes inside string values
   - Keep everything on one line per field

4. IMPORTANT:
   - Return ONLY the JSON object
   - No markdown code blocks
   - No extra text before or after
   - Must be valid JSON

Example for {skill_name}:
{{
  "questions": [
    {{
      "question_text": "What is {skill_name} used for",
      "options": ["Web development", "Data analysis", "Mobile apps", "Gaming"],
      "correct_answer": "Web development",
      "difficulty": "easy",
      "explanation": "{skill_name} is commonly used for web development"
    }}
  ]
}}"""

        # Generate with retry logic and exponential backoff
        import time
        
        max_retries = 3
        retry_delays = [2, 5, 10]  # seconds
        models_to_try = [self.model_name, 'models/gemini-1.5-flash']  # Fallback model
        
        response_text = None  # Initialize outside loops
        success = False
        
        for model_idx, model in enumerate(models_to_try):
            if model_idx > 0:
                logger.info(f"🔄 Trying fallback model: {model}")
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        delay = retry_delays[attempt - 1]
                        logger.info(f"⏳ Retry {attempt + 1}/{max_retries} - Waiting {delay}s before retrying...")
                        time.sleep(delay)
                    
                    logger.info(f"🔄 Calling Gemini API ({model}) for {count} questions... (Attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=8192,  # Increased from 4096 to handle 20 questions
                        )
                    )
                    response_text = response.text.strip()
                    
                    # Check if response is empty
                    if not response_text:
                        logger.error("❌ AI returned empty response - likely rate limit or quota exceeded")
                        if attempt < max_retries - 1:
                            continue  # Retry
                        else:
                            break  # Try next model
                    
                    logger.info(f"✓ AI response received: {len(response_text)} characters")
                    
                    # Save raw response for debugging (first 500 chars)
                    logger.info(f"📄 Response preview: {response_text[:500]}...")
                    
                    # Save full response to file for inspection
                    try:
                        import os
                        from django.conf import settings
                        debug_dir = os.path.join(settings.BASE_DIR, 'logs')
                        os.makedirs(debug_dir, exist_ok=True)
                        debug_file = os.path.join(debug_dir, f'ai_response_{skill_name.replace(" ", "_")}.json')
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(response_text)
                        logger.info(f"💾 Full response saved to: {debug_file}")
                    except Exception as e:
                        logger.debug(f"Could not save debug file: {e}")
                    
                    # Success! Mark as successful and exit
                    success = True
                    break  # Exit retry loop
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check for specific error types
                    if '503' in error_msg or 'UNAVAILABLE' in error_msg or 'overloaded' in error_msg.lower():
                        logger.error(f"❌ MODEL OVERLOADED (503): {error_msg}")
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Model overloaded, will retry with backoff...")
                            continue  # Retry with backoff
                        else:
                            logger.warning(f"⚠️ All retries exhausted for {model}")
                            break  # Try next model
                    elif 'RESOURCE_EXHAUSTED' in error_msg or '429' in error_msg:
                        logger.error(f"❌ API RATE LIMIT HIT: {error_msg}")
                        return []  # Don't retry on rate limit
                    elif 'quota' in error_msg.lower():
                        logger.error(f"❌ API QUOTA EXCEEDED: {error_msg}")
                        return []  # Don't retry on quota
                    elif 'API_KEY' in error_msg or 'authentication' in error_msg.lower():
                        logger.error(f"❌ API KEY ERROR: {error_msg}")
                        return []  # Don't retry on auth error
                    else:
                        logger.error(f"❌ Gemini API error: {error_msg}")
                        if attempt < max_retries - 1:
                            continue  # Retry on unknown errors
                        else:
                            break  # Try next model
            
            # Check if we succeeded
            if success:
                break  # Exit model loop
        
        # Check if we got a successful response
        if not success or not response_text:
            logger.error(f"❌ All retry attempts and model fallbacks failed")
            return []
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
            logger.debug("Removed ```json prefix")
        if response_text.startswith('```'):
            response_text = response_text[3:]
            logger.debug("Removed ``` prefix")
        if response_text.endswith('```'):
            response_text = response_text[:-3]
            logger.debug("Removed ``` suffix")
        
        response_text = response_text.strip()
        logger.info(f"🔍 Parsing JSON response (length: {len(response_text)} chars)")
        
        # Aggressive JSON repair
        data = self._repair_and_parse_json(response_text)
        
        if data is None:
            logger.error("❌ Failed to parse JSON after all repair attempts")
            logger.error(f"Response was: {response_text[:300]}")
            # Check if response contains error message
            if 'error' in response_text.lower() or 'quota' in response_text.lower():
                logger.error("❌ API returned an error instead of JSON - likely quota/rate limit")
            return []
        
        logger.info(f"✓ JSON parsed successfully")
        
        # Extract questions
        questions = data.get('questions', [])
        logger.info(f"📊 Extracted {len(questions)} questions from JSON")
        
        if not questions:
            logger.error("❌ No questions found in AI response")
            logger.error(f"Response data keys: {list(data.keys())}")
            return []
        
        # Validate and sanitize questions
        validated_questions = []
        invalid_count = 0
        for idx, q in enumerate(questions):
            if self._validate_question(q):
                # Additional anti-cheating: verify correct_answer is in options
                if q['correct_answer'] in q['options']:
                    # Clean up any remaining formatting issues
                    q['question_text'] = ' '.join(str(q['question_text']).split())
                    q['explanation'] = ' '.join(str(q.get('explanation', '')).split())
                    q['correct_answer'] = ' '.join(str(q['correct_answer']).split())
                    q['options'] = [' '.join(str(opt).split()) for opt in q['options']]
                    validated_questions.append(q)
                else:
                    invalid_count += 1
                    logger.warning(f"⚠️ Question {idx+1}: correct_answer '{q['correct_answer']}' not in options")
            else:
                invalid_count += 1
                logger.warning(f"⚠️ Question {idx+1} failed validation: {q.get('question_text', 'N/A')[:50]}")
        
        logger.info(f"✅ {len(validated_questions)} valid questions, {invalid_count} invalid")
        
        if len(validated_questions) < count:
            logger.warning(f"⚠️ Expected {count} questions but only got {len(validated_questions)} valid ones")
        
        if validated_questions:
            logger.info(f"Successfully validated {len(validated_questions)} questions")
        
        return validated_questions
    
    def _repair_and_parse_json(self, response_text: str) -> dict:
        """
        Multi-stage JSON repair and parsing with aggressive error recovery.
        Handles common AI response issues: unescaped quotes, newlines, malformed strings.
        """
        import re
        
        # Strategy 1: Try direct parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Remove all newlines and collapse whitespace
        try:
            cleaned = ' '.join(response_text.split())
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract JSON object only
        try:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            if start >= 0 and end > start:
                extracted = cleaned[start:end]
                return json.loads(extracted)
        except (json.JSONDecodeError, NameError):
            pass
        
        # Strategy 4: Aggressive string repair - replace all problematic quotes
        try:
            text = ' '.join(response_text.split())
            
            # Extract JSON portion
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < 0 or end <= start:
                logger.warning("No JSON structure found in response")
                return None
            text = text[start:end]
            
            # AGGRESSIVE FIX: Replace ALL single quotes with escaped quotes inside values
            # This is a heuristic approach for malformed strings
            
            # Find all string values and fix quotes within them
            # Pattern: "key": "value with 'quotes' or "quotes""
            def fix_string_value(match):
                """Fix quotes inside string values"""
                prefix = match.group(1)  # Everything before the value
                value = match.group(2)   # The string value
                # Replace internal quotes with safe character
                value = value.replace('"', "'").replace("'", "")
                return f'{prefix}"{value}"'
            
            # Fix string values in JSON
            text = re.sub(r'("[^"]+"\s*:\s*)"([^"]*(?:"[^"]*)*)"', fix_string_value, text, flags=re.DOTALL)
            
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        except Exception as e:
            logger.debug(f"Strategy 4 exception: {e}")
        
        # Strategy 5: Extract questions using regex patterns (manual parsing)
        try:
            logger.info("Attempting manual question extraction")
            questions = []
            
            # Look for question patterns in the text
            # Pattern: find anything that looks like question structures
            text = ' '.join(response_text.split())
            
            # Try to find question_text, options, correct_answer patterns
            question_pattern = r'"question_text"\s*:\s*"([^"]+)"'
            options_pattern = r'"options"\s*:\s*\[(.*?)\]'
            answer_pattern = r'"correct_answer"\s*:\s*"([^"]+)"'
            difficulty_pattern = r'"difficulty"\s*:\s*"([^"]+)"'
            
            question_texts = re.findall(question_pattern, text)
            if not question_texts:
                logger.warning("No question_text fields found")
                return None
            
            logger.info(f"Found {len(question_texts)} question texts via regex")
            
            # For each question text, try to find its associated data
            for i, q_text in enumerate(question_texts):
                try:
                    # Find the section of text for this question
                    q_start = text.find(f'"question_text": "{q_text}"')
                    # Find next question or end
                    next_q = text.find('"question_text":', q_start + 1)
                    if next_q == -1:
                        next_q = len(text)
                    section = text[q_start:next_q]
                    
                    # Extract options
                    options_match = re.search(options_pattern, section)
                    if options_match:
                        options_str = options_match.group(1)
                        # Extract individual options
                        opts = re.findall(r'"([^"]+)"', options_str)
                        if len(opts) >= 4:
                            options = opts[:4]
                        else:
                            options = opts + [f"Option {i+1}" for i in range(4-len(opts))]
                    else:
                        options = [f"Option A", f"Option B", f"Option C", f"Option D"]
                    
                    # Extract correct answer
                    answer_match = re.search(answer_pattern, section)
                    correct_answer = answer_match.group(1) if answer_match else options[0]
                    
                    # Extract difficulty
                    diff_match = re.search(difficulty_pattern, section)
                    difficulty = diff_match.group(1) if diff_match else "medium"
                    
                    questions.append({
                        "question_text": q_text,
                        "options": options,
                        "correct_answer": correct_answer,
                        "difficulty": difficulty,
                        "explanation": f"Question about {q_text[:30]}..."
                    })
                except Exception as e:
                    logger.debug(f"Failed to extract question {i}: {e}")
                    continue
            
            if questions:
                logger.info(f"Successfully extracted {len(questions)} questions manually")
                return {"questions": questions}
            
        except Exception as e:
            logger.error(f"Strategy 5 exception: {e}")
        
        logger.error("All JSON repair strategies failed")
        return None
    
    def _validate_question(self, question: Dict) -> bool:
        """Validate question structure"""
        required_fields = ['question_text', 'options', 'correct_answer', 'difficulty']
        
        if not all(field in question for field in required_fields):
            return False
        
        if not isinstance(question['options'], list) or len(question['options']) < 3:
            return False
        
        if question['difficulty'] not in ['easy', 'medium', 'hard']:
            return False
        
        return True
    
    def _generate_template_questions(self, skill_name: str, difficulty: str = None, 
                                    count: int = 8) -> List[Dict]:
        """
        Fallback template questions when AI is unavailable.
        Ensures system works even without AI tokens.
        
        Args:
            skill_name: Name of the skill
            difficulty: Optional difficulty filter ('easy', 'medium', 'hard')
            count: Number of questions to generate
        """
        templates = [
            # Easy questions (8 total)
            {
                "question_text": f"What is the fundamental concept of {skill_name}?",
                "options": [
                    f"Basic understanding of {skill_name} principles",
                    f"Advanced application of {skill_name}",
                    f"Expert-level {skill_name} mastery",
                    f"No knowledge of {skill_name}"
                ],
                "correct_answer": f"Basic understanding of {skill_name} principles",
                "difficulty": "easy",
                "explanation": f"Understanding fundamental concepts is the foundation of {skill_name}."
            },
            {
                "question_text": f"Which of the following best describes {skill_name}?",
                "options": [
                    f"An unrelated concept",
                    f"A core skill in the field",
                    f"An outdated practice",
                    f"A minor consideration"
                ],
                "correct_answer": f"A core skill in the field",
                "difficulty": "easy",
                "explanation": f"{skill_name} is recognized as a core competency."
            },
            {
                "question_text": f"Why is {skill_name} important in modern development?",
                "options": [
                    f"It is not important anymore",
                    f"It is essential for professional projects",
                    f"Only for academic purposes",
                    f"Just a trend"
                ],
                "correct_answer": f"It is essential for professional projects",
                "difficulty": "easy",
                "explanation": f"{skill_name} is widely used in industry."
            },
            {
                "question_text": f"What type of projects typically require {skill_name}?",
                "options": [
                    f"Software and technical projects",
                    f"Only legacy projects",
                    f"Non-technical projects",
                    f"Obsolete projects"
                ],
                "correct_answer": f"Software and technical projects",
                "difficulty": "easy",
                "explanation": f"{skill_name} is used in modern technical work."
            },
            {
                "question_text": f"How is {skill_name} typically learned?",
                "options": [
                    f"Through practice and study",
                    f"It cannot be learned",
                    f"Only through certification",
                    f"By memorization alone"
                ],
                "correct_answer": f"Through practice and study",
                "difficulty": "easy",
                "explanation": f"Most skills require hands-on practice."
            },
            {
                "question_text": f"What level of expertise can be achieved with {skill_name}?",
                "options": [
                    f"From beginner to expert",
                    f"Only basic level",
                    f"No progression possible",
                    f"Instant mastery"
                ],
                "correct_answer": f"From beginner to expert",
                "difficulty": "easy",
                "explanation": f"Skills can be developed over time."
            },
            {
                "question_text": f"In which industry is {skill_name} most commonly used?",
                "options": [
                    f"Technology and IT",
                    f"Agriculture",
                    f"Retail",
                    f"Transportation"
                ],
                "correct_answer": f"Technology and IT",
                "difficulty": "easy",
                "explanation": f"Technical skills are primarily used in tech industry."
            },
            {
                "question_text": f"What is the best approach to learning {skill_name}?",
                "options": [
                    f"Combination of theory and practice",
                    f"Only reading documentation",
                    f"Guessing without study",
                    f"Avoiding practice"
                ],
                "correct_answer": f"Combination of theory and practice",
                "difficulty": "easy",
                "explanation": f"Balanced learning is most effective."
            },
            
            # Medium questions (6 total)
            {
                "question_text": f"What is a practical application of {skill_name}?",
                "options": [
                    f"Applying {skill_name} to solve real-world problems",
                    f"Ignoring {skill_name} in practice",
                    f"Only theoretical study",
                    f"Avoiding {skill_name} usage"
                ],
                "correct_answer": f"Applying {skill_name} to solve real-world problems",
                "difficulty": "medium",
                "explanation": f"Practical application is key to mastering {skill_name}."
            },
            {
                "question_text": f"What intermediate skill is needed for {skill_name}?",
                "options": [
                    f"No prior knowledge",
                    f"Basic to intermediate understanding",
                    f"Expert certification",
                    f"Unrelated skills"
                ],
                "correct_answer": f"Basic to intermediate understanding",
                "difficulty": "medium",
                "explanation": f"Intermediate proficiency requires building on basics."
            },
            {
                "question_text": f"How would you rate the importance of {skill_name} in your field?",
                "options": [
                    f"Very important for relevant roles",
                    f"Somewhat important",
                    f"Not important",
                    f"Unknown"
                ],
                "correct_answer": f"Very important for relevant roles",
                "difficulty": "medium",
                "explanation": f"{skill_name} is valued in the industry."
            },
            {
                "question_text": f"What resources are best for improving {skill_name} skills?",
                "options": [
                    f"Documentation, practice, and projects",
                    f"Only watching videos",
                    f"No resources needed",
                    f"Just theory books"
                ],
                "correct_answer": f"Documentation, practice, and projects",
                "difficulty": "medium",
                "explanation": f"Multiple learning resources work best."
            },
            {
                "question_text": f"How do professionals typically use {skill_name}?",
                "options": [
                    f"In daily work and projects",
                    f"Never use it",
                    f"Only in interviews",
                    f"Just for show"
                ],
                "correct_answer": f"In daily work and projects",
                "difficulty": "medium",
                "explanation": f"Professionals apply skills regularly."
            },
            {
                "question_text": f"What indicates intermediate proficiency in {skill_name}?",
                "options": [
                    f"Ability to solve common problems independently",
                    f"No understanding",
                    f"Only basic awareness",
                    f"Expert-level only"
                ],
                "correct_answer": f"Ability to solve common problems independently",
                "difficulty": "medium",
                "explanation": f"Independent problem-solving shows proficiency."
            },
            
            # Hard questions (6 total)
            {
                "question_text": f"How would an expert approach a complex {skill_name} challenge?",
                "options": [
                    f"Guess randomly",
                    f"Apply systematic methodology and best practices",
                    f"Skip the challenge",
                    f"Use only basic techniques"
                ],
                "correct_answer": f"Apply systematic methodology and best practices",
                "difficulty": "hard",
                "explanation": f"Experts use systematic approaches."
            },
            {
                "question_text": f"What advanced concept is central to mastering {skill_name}?",
                "options": [
                    f"Only memorizing definitions",
                    f"Deep understanding and innovative application",
                    f"Following scripts blindly",
                    f"Avoiding complexity"
                ],
                "correct_answer": f"Deep understanding and innovative application",
                "difficulty": "hard",
                "explanation": f"Mastery requires deep understanding."
            },
            {
                "question_text": f"In a professional setting, how is {skill_name} typically evaluated?",
                "options": [
                    f"It is never evaluated",
                    f"Through theoretical exams only",
                    f"Based on practical performance and outcomes",
                    f"By years of experience alone"
                ],
                "correct_answer": f"Based on practical performance and outcomes",
                "difficulty": "hard",
                "explanation": f"Professional evaluation focuses on practical results."
            },
            {
                "question_text": f"What distinguishes an expert in {skill_name} from an intermediate user?",
                "options": [
                    f"Deep knowledge, optimization skills, and problem-solving ability",
                    f"Just more years of experience",
                    f"Having a certification",
                    f"Memorizing more syntax"
                ],
                "correct_answer": f"Deep knowledge, optimization skills, and problem-solving ability",
                "difficulty": "hard",
                "explanation": f"Expertise involves comprehensive understanding."
            },
            {
                "question_text": f"How do experts stay current with {skill_name} developments?",
                "options": [
                    f"Continuous learning, practice, and community engagement",
                    f"Never update knowledge",
                    f"Only read old books",
                    f"Ignore new developments"
                ],
                "correct_answer": f"Continuous learning, practice, and community engagement",
                "difficulty": "hard",
                "explanation": f"Staying current requires ongoing effort."
            },
            {
                "question_text": f"What is the most challenging aspect of mastering {skill_name}?",
                "options": [
                    f"Understanding complex patterns and best practices",
                    f"Learning basic syntax",
                    f"Installing tools",
                    f"Reading documentation"
                ],
                "correct_answer": f"Understanding complex patterns and best practices",
                "difficulty": "hard",
                "explanation": f"Advanced concepts require significant study."
            },
        ]
        
        # Filter by difficulty if specified
        if difficulty:
            templates = [q for q in templates if q['difficulty'] == difficulty.lower()]
        
        # Randomly shuffle to avoid predictable patterns
        random.shuffle(templates)
        
        # Return requested number of questions (or all available if less)
        return templates[:min(count, len(templates))]


# Singleton instance
question_generator = QuestionGeneratorService()


def generate_and_store_questions_for_skill(skill, count=20, difficulty=None, proficiency_level=None):
    """
    Generate questions using AI and store them in QuestionBank.
    This is called progressively to build up to 100 questions per skill.
    
    Args:
        skill: Skill model instance
        count: Number of questions to generate (default: 20)
        difficulty: Optional difficulty filter ('easy', 'medium', 'hard')
        proficiency_level: Proficiency level for these questions (0-10 scale)
        
    Returns:
        List of created QuestionBank objects
    """
    from .models import QuestionBank
    from django.utils import timezone
    
    logger.info(f"Generating and storing {count} questions for {skill.name}")
    
    # Check current question count
    current_count = skill.question_count or 0
    
    if current_count >= 100:
        logger.info(f"Skill {skill.name} already has {current_count} questions (target: 100)")
        return []
    
    # Adjust count if it would exceed 100
    if current_count + count > 100:
        count = 100 - current_count
        logger.info(f"Adjusting count to {count} to reach 100 total")
    
    # Generate questions using AI
    # When count=20 and difficulty=None, generates 8 easy + 6 medium + 6 hard in ONE call
    question_dicts = question_generator.generate_questions(
        skill_name=skill.name,
        skill_description=skill.description,
        difficulty=difficulty,
        count=count
    )
    
    if not question_dicts:
        logger.error(f"❌ Failed to generate questions for {skill.name}")
        return []
    
    logger.info(f"✓ AI returned {len(question_dicts)} questions for {skill.name}")
    
    # Calculate proficiency level based on difficulty if not provided
    def get_proficiency_for_difficulty(diff):
        """Map difficulty to proficiency level (0-10 scale)"""
        mapping = {
            'easy': 3.0,     # Beginner level
            'medium': 6.0,   # Intermediate level
            'hard': 9.0      # Advanced level
        }
        return mapping.get(diff.lower(), 5.0)
    
    # Store questions in database
    created_questions = []
    for q_dict in question_dicts:
        # Determine proficiency level
        if proficiency_level is not None:
            q_proficiency = proficiency_level
        else:
            q_proficiency = get_proficiency_for_difficulty(q_dict.get('difficulty', 'medium'))
        
        # Create QuestionBank entry
        question = QuestionBank.objects.create(
            skill=skill,
            question_text=q_dict.get('question_text', q_dict.get('question', '')),
            options=q_dict.get('options', []),
            correct_answer=q_dict.get('correct_answer', ''),
            difficulty=q_dict.get('difficulty', 'medium'),
            proficiency_level=q_proficiency,
            points=q_dict.get('points', 5 if q_dict.get('difficulty') == 'easy' else 10),
            explanation=q_dict.get('explanation', ''),
            created_by_ai=True
        )
        created_questions.append(question)
    
    # Update skill question count
    skill.question_count = current_count + len(created_questions)
    skill.questions_generated = True
    skill.questions_generated_at = timezone.now()
    skill.save(update_fields=['question_count', 'questions_generated', 'questions_generated_at'])
    
    logger.info(f"✓ Stored {len(created_questions)} questions for {skill.name}. Total: {skill.question_count}/100")
    
    return created_questions


def get_questions_for_assessment(skill, user_attempt_number=None):
    """
    Smart question allocation for assessments.
    
    Strategy:
    - First 5 users per skill: Generate 20 new questions and store them (builds bank to 100)
    - User 6+: Randomly select 20 questions from the 100-question bank
    
    Args:
        skill: Skill model instance
        user_attempt_number: Which user attempt this is for this skill (1-5 generates, 6+ selects)
        
    Returns:
        QuerySet of 20 QuestionBank objects
    """
    from .models import QuestionBank, AssessmentAttempt
    
    current_count = skill.question_count or 0
    
    # Determine if this is a generating user or selecting user
    if user_attempt_number is None:
        # Auto-detect by counting attempts for this skill
        user_attempt_number = AssessmentAttempt.objects.filter(skill=skill).count() + 1
    
    # First 5 users: Generate and store questions
    if user_attempt_number <= 5 and current_count < 100:
        logger.info(f"🚀 User #{user_attempt_number} for {skill.name}: Generating all 20 questions in SINGLE API call")
        
        # Generate all 20 questions (8 easy + 6 medium + 6 hard) in ONE API call
        # This prevents rate limit issues by reducing 3 calls to 1
        all_questions = generate_and_store_questions_for_skill(
            skill, 
            count=20, 
            difficulty=None  # None means generate mixed difficulty
        )
        
        if not all_questions or len(all_questions) < 20:
            logger.warning(f"⚠️ Only generated {len(all_questions) if all_questions else 0}/20 questions")
            if all_questions:
                # Return what we got
                question_ids = [q.id for q in all_questions]
                return QuestionBank.objects.filter(id__in=question_ids)
            else:
                # Fallback to existing
                logger.warning(f"Failed to generate questions, falling back to existing")
                return QuestionBank.objects.filter(skill=skill).order_by('?')[:20]
        
        logger.info(f"✓ Successfully generated all {len(all_questions)} questions in single API call")
        
        # Return the newly generated questions
        question_ids = [q.id for q in all_questions]
        return QuestionBank.objects.filter(id__in=question_ids)
    
    # User 6+: Select randomly from stored questions
    logger.info(f"User #{user_attempt_number} for {skill.name}: Selecting from {current_count} stored questions")
    
    if current_count < 20:
        logger.warning(f"Only {current_count} questions available for {skill.name}. Generating more...")
        # Generate enough to reach 20
        needed = 20 - current_count
        generate_and_store_questions_for_skill(skill, count=needed)
    
    # Select balanced mix of difficulties
    easy_qs = QuestionBank.objects.filter(skill=skill, difficulty='easy').order_by('?')[:8]
    medium_qs = QuestionBank.objects.filter(skill=skill, difficulty='medium').order_by('?')[:6]
    hard_qs = QuestionBank.objects.filter(skill=skill, difficulty='hard').order_by('?')[:6]
    
    # Combine and shuffle
    question_ids = list(easy_qs.values_list('id', flat=True)) + \
                   list(medium_qs.values_list('id', flat=True)) + \
                   list(hard_qs.values_list('id', flat=True))
    
    return QuestionBank.objects.filter(id__in=question_ids).order_by('?')

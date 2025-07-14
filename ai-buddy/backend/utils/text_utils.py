# File: backend/utils/text_processor.py - SYNTAX ERRORS FIXED

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TextProcessor:
    """Enhanced text processing with better quiz parsing"""
    
    def clean_ai_output(self, text: str) -> str:
        """Clean AI generated text"""
        if not text:
            return ""
        
        # Remove thinking tags and any processing artifacts
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def parse_mcq_questions(self, content: str) -> List[Dict[str, Any]]:
        """Parse MCQ questions - COMPLETELY FIXED VERSION"""
        try:
            logger.info("🔍 Starting MCQ parsing...")
            logger.info(f"📄 Content preview: {content[:200]}...")
            
            questions = []
            
            # STEP 1: Split into question blocks using multiple patterns
            question_blocks = self._split_into_question_blocks(content)
            
            if not question_blocks:
                logger.error("❌ No question blocks found")
                return []
            
            logger.info(f"✅ Found {len(question_blocks)} question blocks")
            
            # STEP 2: Parse each question block
            for i, block in enumerate(question_blocks, 1):
                logger.info(f"🔍 Parsing question block {i}...")
                question_data = self._parse_single_mcq_block(i, block)
                
                if question_data:
                    questions.append(question_data)
                    logger.info(f"✅ Successfully parsed question {i}")
                else:
                    logger.warning(f"⚠️ Failed to parse question block {i}")
            
            logger.info(f"🎯 Final result: {len(questions)} questions parsed successfully")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error in parse_mcq_questions: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []
    
    def _split_into_question_blocks(self, content: str) -> List[str]:
        """Split content into individual question blocks"""
        try:
            # Pattern 1: "Question N:" format
            pattern1 = r'Question\s+(\d+):\s*(.*?)(?=Question\s+\d+:|$)'
            matches1 = re.findall(pattern1, content, re.DOTALL | re.IGNORECASE)
            
            if matches1:
                logger.info(f"✅ Found {len(matches1)} questions using 'Question N:' pattern")
                return [match[1].strip() for match in matches1]
            
            # Pattern 2: Just numbers "1." or "1)"
            pattern2 = r'(\d+)[\.\)]\s*(.*?)(?=\d+[\.\)]|$)'
            matches2 = re.findall(pattern2, content, re.DOTALL)
            
            if matches2:
                logger.info(f"✅ Found {len(matches2)} questions using numbered pattern")
                return [match[1].strip() for match in matches2]
            
            # Pattern 3: Split by double newlines and filter
            blocks = [block.strip() for block in content.split('\n\n') if block.strip()]
            question_blocks = []
            
            for block in blocks:
                # Check if block contains question-like content - FIXED SYNTAX
                if (('A)' in block or 'a)' in block) and 
                    ('B)' in block or 'b)' in block) and
                    ('?' in block or ':' in block)):
                    question_blocks.append(block)
            
            if question_blocks:
                logger.info(f"✅ Found {len(question_blocks)} questions using content analysis")
                return question_blocks
            
            logger.error("❌ No recognizable question pattern found")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error splitting question blocks: {e}")
            return []
    
    def _parse_single_mcq_block(self, question_num: int, block: str) -> Dict[str, Any]:
        """Parse a single MCQ question block - ROBUST VERSION"""
        try:
            logger.info(f"🔍 Parsing block {question_num}: {block[:100]}...")
            
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            # Initialize
            question_text = ""
            options = {}
            correct_answer = None
            
            # STEP 1: Extract question text
            question_text = self._extract_question_text(lines)
            if not question_text:
                logger.warning(f"⚠️ No question text found in block {question_num}")
                return None
            
            # STEP 2: Extract options
            options = self._extract_options(lines)
            if len(options) < 4:
                logger.warning(f"⚠️ Only {len(options)} options found for question {question_num}")
                # Fill missing options
                for letter in ['A', 'B', 'C', 'D']:
                    if letter not in options:
                        options[letter] = f"Option {letter}"
            
            # STEP 3: Extract correct answer - MULTIPLE STRATEGIES
            correct_answer = self._extract_correct_answer(block, lines)
            
            # STEP 4: Validate and return
            if not correct_answer or correct_answer not in ['A', 'B', 'C', 'D']:
                logger.warning(f"⚠️ Invalid or missing correct answer for question {question_num}: '{correct_answer}', defaulting to A")
                correct_answer = 'A'
            
            result = {
                'number': question_num,
                'question': question_text,
                'options': options,
                'correct_answer': correct_answer
            }
            
            logger.info(f"✅ Question {question_num} parsed successfully - Answer: {correct_answer}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error parsing question block {question_num}: {e}")
            return None
    
    def _extract_question_text(self, lines: List[str]) -> str:
        """Extract the main question text"""
        for line in lines:
            # Skip option lines and answer lines - FIXED SYNTAX
            if (not re.match(r'^[A-Da-d][\)\.]', line) and 
                'Correct Answer:' not in line and
                'Answer:' not in line and
                line.endswith(('?', ':', '.'))):
                return line
        
        # Fallback: take first non-option line
        for line in lines:
            if not re.match(r'^[A-Da-d][\)\.]', line) and 'Answer:' not in line:
                return line
        
        return ""
    
    def _extract_options(self, lines: List[str]) -> Dict[str, str]:
        """Extract A, B, C, D options"""
        options = {}
        
        # Pattern: A) text or A. text
        option_patterns = [
            r'^([A-D])[\)\.][\s]*(.+)$',  # A) text or A. text
            r'^([a-d])[\)\.][\s]*(.+)$',  # a) text or a. text (convert to uppercase)
        ]
        
        for line in lines:
            for pattern in option_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    letter = match.group(1).upper()
                    text = match.group(2).strip()
                    if text:
                        options[letter] = text
                    break
        
        return options
    
    def _extract_correct_answer(self, block: str, lines: List[str]) -> str:
        """Extract correct answer using multiple strategies"""
        
        # Strategy 1: Look for explicit answer patterns
        answer_patterns = [
            r'Correct\s+Answer:\s*([A-Da-d])',
            r'Answer:\s*([A-Da-d])',
            r'Correct:\s*([A-Da-d])',
            r'The\s+correct\s+answer\s+is\s*([A-Da-d])',
            r'Answer\s*is\s*([A-Da-d])',
            r'\*\*([A-Da-d])\*\*',  # Bold format
            r'^\s*([A-Da-d])\s*\(correct\)',  # (correct) format
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, block, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).upper()
                logger.info(f"✅ Found answer using pattern '{pattern}': {answer}")
                return answer
        
        # Strategy 2: Look for asterisks or markers around options
        for letter in ['A', 'B', 'C', 'D']:
            if f'*{letter}' in block or f'{letter}*' in block:
                logger.info(f"✅ Found answer using asterisk marker: {letter}")
                return letter
        
        # Strategy 3: Look for (correct) or similar markers in option lines
        for line in lines:
            for letter in ['A', 'B', 'C', 'D']:
                if (line.startswith(f'{letter})') or line.startswith(f'{letter}.')):
                    if '(correct)' in line.lower() or '*' in line:
                        logger.info(f"✅ Found answer using option marker: {letter}")
                        return letter
        
        # Strategy 4: Advanced parsing - look for emphasis
        emphasis_patterns = [
            r'([A-D])\).*(?:\*\*|\*|__|<b>|<strong>)',  # Bold/italic options
            r'([A-D])\).*\(answer\)',  # (answer) marker
        ]
        
        for pattern in emphasis_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                answer = match.group(1).upper()
                logger.info(f"✅ Found answer using emphasis pattern: {answer}")
                return answer
        
        logger.warning("⚠️ No correct answer pattern found")
        return None
    
    def parse_open_ended_questions(self, content: str) -> List[Dict[str, Any]]:
        """Parse open-ended questions"""
        try:
            logger.info("🔍 Starting open-ended parsing...")
            questions = []
            
            # Split by "Question N:" pattern
            pattern = r'Question\s+(\d+):\s*(.*?)(?=Question\s+\d+:|$)'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            
            for question_num, question_text in matches:
                # Clean up question text
                question_text = question_text.strip()
                question_text = re.sub(r'\n+', ' ', question_text)  # Replace newlines
                question_text = re.sub(r'\s+', ' ', question_text)  # Normalize whitespace
                
                if question_text:
                    questions.append({
                        'number': int(question_num),
                        'question': question_text
                    })
            
            logger.info(f"✅ Parsed {len(questions)} open-ended questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error parsing open-ended questions: {e}")
            return []
    
    def check_mcq_answers(self, user_answers: Dict[int, str], questions: List[Dict]) -> str:
        """Generate feedback for MCQ answers"""
        try:
            if not user_answers or not questions:
                return "No answers to check."
            
            correct_count = 0
            total_questions = len(questions)
            
            for question in questions:
                q_num = question['number']
                if user_answers.get(q_num) == question['correct_answer']:
                    correct_count += 1
            
            percentage = (correct_count / total_questions) * 100
            
            if percentage >= 90:
                emoji = "🎉"
                message = "Excellent work!"
            elif percentage >= 80:
                emoji = "🎊"
                message = "Great job!"
            elif percentage >= 70:
                emoji = "👍"
                message = "Good effort!"
            elif percentage >= 60:
                emoji = "👌"
                message = "Not bad!"
            else:
                emoji = "📚"
                message = "Keep studying!"
            
            return f"""
## {emoji} Quiz Results

**Score:** {correct_count}/{total_questions} ({percentage:.1f}%)

**{message}**
"""
            
        except Exception as e:
            logger.error(f"❌ Error checking MCQ answers: {e}")
            return "Error checking answers."
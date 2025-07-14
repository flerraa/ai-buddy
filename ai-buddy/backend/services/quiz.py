# File: backend/services/quiz.py - FULL FILE WITH IMPROVED PROMPTS

from typing import Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from .base import ServiceResponse
from .pdf import PDFService
from .vector import vector_service
from .ai_cache import get_cached_ollama
from ..config import settings
from ..utils import TextProcessor
import logging

logger = logging.getLogger(__name__)

class QuizService:
    """Service for AI quiz generation with cached model"""
    
    def __init__(self):
        self.pdf_service = PDFService()
        self.text_processor = TextProcessor()
        # Use cached model instead of lazy loading
        self.model = self._get_model()
    
    def _get_model(self):
        """Get cached Ollama model - replaces _init_ai_model"""
        try:
            model = get_cached_ollama()
            logger.info(f"Quiz service using cached model: {settings.OLLAMA_MODEL}")
            return model
        except Exception as e:
            logger.error(f"Failed to get cached AI model: {e}")
            return None
    
    def generate_quiz(
        self, 
        user_id: str, 
        pdf_id: str, 
        quiz_type: str = "MCQ", 
        num_questions: int = 5, 
        difficulty: str = "Medium", 
        topic_focus: str = ""
    ) -> ServiceResponse:
        """Generate quiz - FIXED FOR None PARAMETER BUG"""
        try:
            # 🔍 LOG EVERYTHING WE RECEIVE - DEBUGGING
            logger.info(f"🔍 RAW PARAMETERS:")
            logger.info(f"  user_id: {user_id} (type: {type(user_id)})")
            logger.info(f"  pdf_id: {pdf_id} (type: {type(pdf_id)})")
            logger.info(f"  quiz_type: {quiz_type} (type: {type(quiz_type)})")
            logger.info(f"  num_questions: {num_questions} (type: {type(num_questions)})")
            logger.info(f"  difficulty: {difficulty} (type: {type(difficulty)})")
            logger.info(f"  topic_focus: {topic_focus} (type: {type(topic_focus)})")
            
            # 🛠️ CRITICAL FIX: Handle None values and force correct types
            
            # Fix user_id
            if user_id is None:
                logger.error("user_id is None!")
                return ServiceResponse.error_response("User ID is required")
            user_id = str(user_id)
            
            # Fix pdf_id  
            if pdf_id is None:
                logger.error("pdf_id is None!")
                return ServiceResponse.error_response("PDF ID is required")
            pdf_id = str(pdf_id)
            
            # Fix quiz_type
            if quiz_type is None:
                logger.warning("quiz_type was None, setting to MCQ")
                quiz_type = "MCQ"
            quiz_type = str(quiz_type)
            if quiz_type not in ["MCQ", "Open-ended"]:
                logger.warning(f"Invalid quiz_type {quiz_type}, setting to MCQ")
                quiz_type = "MCQ"
            
            # 🚨 THE CRITICAL FIX: Handle num_questions parameter
            if num_questions is None:
                logger.warning("⚠️ num_questions was None! Setting to 3")
                num_questions = 3
            
            # Convert to int no matter what type we receive
            try:
                if isinstance(num_questions, str):
                    # Handle string numbers like "3.0" or "3"
                    num_questions = int(float(num_questions))
                elif isinstance(num_questions, float):
                    num_questions = int(num_questions)
                elif not isinstance(num_questions, int):
                    logger.warning(f"⚠️ num_questions was unexpected type: {type(num_questions)}, converting to 3")
                    num_questions = 3
                else:
                    num_questions = int(num_questions)
                    
                logger.info(f"✅ Successfully converted num_questions to: {num_questions} (type: {type(num_questions)})")
                
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Error converting num_questions: {e}, using default value 3")
                num_questions = 3
            
            # Validate range
            if num_questions < 1 or num_questions > 10:
                logger.warning(f"⚠️ num_questions {num_questions} out of range, clamping to valid range")
                num_questions = min(max(num_questions, 1), 10)  # Clamp between 1-10
            
            # Fix difficulty
            if difficulty is None:
                logger.warning("difficulty was None, setting to Medium")
                difficulty = "Medium"
            difficulty = str(difficulty)
            if difficulty not in ["Easy", "Medium", "Hard"]:
                logger.warning(f"Invalid difficulty {difficulty}, setting to Medium")
                difficulty = "Medium"
            
            # Fix topic_focus
            if topic_focus is None:
                topic_focus = ""
            topic_focus = str(topic_focus)
            
            # 🚀 LOG FINAL VALUES
            logger.info(f"🚀 FINAL VALIDATED PARAMETERS:")
            logger.info(f"  user_id: {user_id}")
            logger.info(f"  pdf_id: {pdf_id}")
            logger.info(f"  quiz_type: {quiz_type}")
            logger.info(f"  num_questions: {num_questions} (type: {type(num_questions)})")
            logger.info(f"  difficulty: {difficulty}")
            logger.info(f"  topic_focus: '{topic_focus}'")
            
            # Check AI model
            if not self.model:
                logger.error("AI model not available")
                return ServiceResponse.error_response("AI model not available")
            
            # Get PDF
            pdf = self.pdf_service.get_pdf_by_id(pdf_id, user_id)
            if not pdf:
                logger.error(f"PDF not found: {pdf_id}")
                return ServiceResponse.error_response("PDF not found")
            if not pdf.processed:
                logger.error(f"PDF not processed: {pdf_id}")
                return ServiceResponse.error_response("PDF is still being processed")
            
            # Search vectors
            search_query = f"{difficulty} {quiz_type} quiz {num_questions} questions"
            if topic_focus:
                search_query += f" about {topic_focus}"
            
            logger.info(f"🔍 Searching vectors with query: {search_query}")
            search_result = vector_service.search_pdf_vectors(user_id, pdf_id, search_query, n_results=8)
            if not search_result.success or not search_result.data:
                logger.error("No content available for quiz generation")
                return ServiceResponse.error_response("No content available to generate quiz")
            
            # Get context
            context = "\n\n".join([result['content'] for result in search_result.data])
            logger.info(f"📄 Context length: {len(context)} characters")
            
            # Generate quiz content
            logger.info(f"🎯 Generating {quiz_type} quiz...")
            if quiz_type == "MCQ":
                quiz_content = self._generate_mcq_quiz(context, num_questions, difficulty, topic_focus)
            else:
                quiz_content = self._generate_open_ended_quiz(context, num_questions, difficulty, topic_focus)
            
            if not quiz_content:
                logger.error("Failed to generate quiz content")
                return ServiceResponse.error_response("Failed to generate quiz content")
            
            # Clean content
            clean_content = self.text_processor.clean_ai_output(quiz_content)
            logger.info(f"✅ SUCCESS: Generated {quiz_type} quiz with {num_questions} questions")
            
            return ServiceResponse.success_response("Quiz generated successfully", {
                "content": clean_content,
                "type": quiz_type,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "topic_focus": topic_focus
            })
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in generate_quiz: {e}")
            import traceback
            logger.error(f"❌ TRACEBACK: {traceback.format_exc()}")
            return ServiceResponse.error_response(f"Quiz generation failed: {str(e)}")
    
    def _generate_mcq_quiz(self, context: str, num_questions: int, difficulty: str, topic_focus: str) -> str:
        """Generate MCQ quiz content with IMPROVED PROMPTS"""
        try:
            # Ensure num_questions is an integer for string formatting
            num_questions = int(num_questions)
            logger.info(f"🎲 Generating MCQ with {num_questions} questions at {difficulty} level")
            
            template = f"""
Create EXACTLY {num_questions} multiple choice questions based on the content below.

IMPORTANT RULES:
- Do NOT ask about page numbers, line numbers, or document structure
- Do NOT ask about specific locations in the document  
- Focus on CONCEPTS, PRINCIPLES, and UNDERSTANDING
- Do NOT show any thinking process or <think> tags
- Make questions test comprehension, not memorization
- Each question must have exactly 4 options (A, B, C, D)
- Make questions at {difficulty} difficulty level
- Clearly indicate the correct answer

GOOD QUESTION TYPES:
- What is the main purpose of...?
- Which principle states that...?
- What are the key characteristics of...?
- Why is [concept] important?
- How does [concept A] relate to [concept B]?
- Which of the following best describes...?

BAD QUESTION TYPES (NEVER ASK):
- On which page can you find...?
- In which section is...?
- What page number contains...?
- Where in the document...?
- Which paragraph mentions...?
- On what line does it say...?

FORMAT:
Question 1: [Question text here - focus on concepts]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
Correct Answer: A

Question 2: [Question text here - focus on understanding]
A) [Option A]
B) [Option B]
C) [Option C] 
D) [Option D]
Correct Answer: B

CONTENT: {{context}}

Generate {num_questions} CONCEPTUAL questions now (NO page numbers or document locations):
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model
            result = chain.invoke({"context": context})
            
            quiz_content = str(result)
            logger.info(f"✅ MCQ generation completed, content length: {len(quiz_content)}")
            return quiz_content
            
        except Exception as e:
            logger.error(f"❌ Error generating MCQ quiz: {e}")
            return ""

    def _generate_open_ended_quiz(self, context: str, num_questions: int, difficulty: str, topic_focus: str) -> str:
        """Generate open-ended quiz content with IMPROVED PROMPTS"""
        try:
            # Ensure num_questions is an integer for string formatting
            num_questions = int(num_questions)
            logger.info(f"🎲 Generating Open-ended with {num_questions} questions at {difficulty} level")
            
            template = f"""
Create EXACTLY {num_questions} open-ended questions based on the content below.

IMPORTANT RULES:
- Do NOT ask about page numbers, sections, or document structure
- Focus on ANALYSIS, EXPLANATION, and CRITICAL THINKING
- Do NOT show any thinking process or <think> tags
- Make questions require detailed explanations
- Test deep understanding, not memorization
- Make questions at {difficulty} difficulty level

GOOD QUESTION TYPES:
- Explain the significance of...
- Analyze the relationship between...
- Discuss why [concept] is important...
- Compare and contrast [concept A] and [concept B]...
- Evaluate the effectiveness of...
- Describe how you would apply...
- What are the implications of...?

BAD QUESTION TYPES (NEVER ASK):
- List the page numbers where...
- Where in the document can you find...?
- What section discusses...?
- On which page is...?
- Which paragraph contains...?

FORMAT:
Question 1: [Analytical question requiring explanation]

Question 2: [Critical thinking question]

Question 3: [Application or evaluation question]

CONTENT: {{context}}

Generate {num_questions} ANALYTICAL questions now (focus on understanding and application):
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model
            result = chain.invoke({"context": context})
            
            quiz_content = str(result)
            logger.info(f"✅ Open-ended generation completed, content length: {len(quiz_content)}")
            return quiz_content
            
        except Exception as e:
            logger.error(f"❌ Error generating open-ended quiz: {e}")
            return ""

    def parse_quiz_questions(self, quiz_content: str, quiz_type: str) -> ServiceResponse:
        """Parse quiz questions from generated content"""
        try:
            logger.info(f"🔍 Parsing {quiz_type} questions...")
            
            if quiz_type == "MCQ":
                questions = self.text_processor.parse_mcq_questions(quiz_content)
            else:
                questions = self.text_processor.parse_open_ended_questions(quiz_content)

            if not questions:
                logger.error("No valid questions could be parsed")
                return ServiceResponse.error_response("No valid questions could be parsed")
            
            logger.info(f"✅ Successfully parsed {len(questions)} questions")
            return ServiceResponse.success_response(f"Parsed {len(questions)} questions", questions)
            
        except Exception as e:
            logger.error(f"❌ Error parsing quiz questions: {e}")
            return ServiceResponse.error_response("Failed to parse questions")

    def check_mcq_answers(self, questions: List[Dict], user_answers: Dict[int, str]) -> ServiceResponse:
        """Check MCQ answers and provide feedback"""
        try:
            if not user_answers:
                return ServiceResponse.error_response("Please answer at least one question")

            feedback = self.text_processor.check_mcq_answers(user_answers, questions)
            correct_count = 0
            total_questions = len(questions)

            for q in questions:
                q_num = q['number']
                if user_answers.get(q_num) == q['correct_answer']:
                    correct_count += 1

            score_data = {
                "score": f"{correct_count}/{total_questions}",
                "percentage": round((correct_count / total_questions) * 100, 1),
                "correct_count": correct_count,
                "total_questions": total_questions,
                "feedback": feedback
            }

            logger.info(f"✅ Quiz checked: {score_data['score']} ({score_data['percentage']}%)")
            return ServiceResponse.success_response(f"Quiz completed: {score_data['score']}", score_data)
            
        except Exception as e:
            logger.error(f"❌ Error checking MCQ answers: {e}")
            return ServiceResponse.error_response("Failed to check answers")
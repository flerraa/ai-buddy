from typing import Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from .base import ServiceResponse
from .pdf import PDFService
from .vector import vector_service
from .ai_cache import get_cached_ollama  # NEW IMPORT
from ..config import settings
from ..utils import TextProcessor
import logging

logger = logging.getLogger(__name__)

class ChatService:
    """Service for AI chat functionality with cached model"""
    
    def __init__(self):
        self.pdf_service = PDFService()
        self.text_processor = TextProcessor()
        # Use cached model instead of lazy loading
        self.model = self._get_model()
    
    def _get_model(self):
        """Get cached Ollama model - replaces _init_ai_model"""
        try:
            model = get_cached_ollama()
            logger.info(f"Chat service using cached model: {settings.OLLAMA_MODEL}")
            return model
        except Exception as e:
            logger.error(f"Failed to get cached AI model: {e}")
            return None
    
    def _is_context_too_weak(self, question: str, context: str) -> bool:
        """Check if context is too weak to answer the question"""
        # Only flag as weak if context is very short and has no overlap with question
        if len(context.strip()) < 50:
            return True
        
        # Check for minimal word overlap (very basic relevance)
        question_words = set(question.lower().split())
        context_words = set(context.lower().split())
        
        # Remove very common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        question_words -= common_words
        
        # If no meaningful overlap and context is short, flag as weak
        overlap = len(question_words.intersection(context_words))
        if overlap == 0 and len(context) < 200:
            return True
        
        return False
    
    def chat_with_pdf(
        self, 
        user_id: str, 
        pdf_id: str, 
        question: str, 
        mode: str = "Explain",
        quiz_context: str = None
    ) -> ServiceResponse:
        try:
            if not self.model:
                return ServiceResponse.error_response("AI model not available")
            
            pdf = self.pdf_service.get_pdf_by_id(pdf_id, user_id)
            if not pdf:
                return ServiceResponse.error_response("PDF not found")
            if not pdf.processed:
                return ServiceResponse.error_response("PDF is still being processed")
            
            # ✅ Enhanced search (removed min_similarity for compatibility)
            search_result = vector_service.search_pdf_vectors(
                user_id, pdf_id, question, n_results=6
            )
            
            if not search_result.success or not search_result.data:
                return ServiceResponse.error_response("No relevant information found in the PDF")
            
            # ✅ Context prep
            context = "\n\n".join([result['content'] for result in search_result.data])
            
            # ✅ Only check if context is too weak to answer
            if self._is_context_too_weak(question, context):
                return ServiceResponse.success_response(
                    "Response generated successfully",
                    {
                        "response": "I couldn't find enough relevant information in the document to answer your question thoroughly. The document may not cover this specific topic in detail.",
                        "mode": mode,
                        "context_used": 0
                    }
                )
            
            # ✅ Mode-based AI generation
            if mode == "Quiz Me":
                response = self._generate_quiz_feedback(question, context, quiz_context)
            elif mode == "Tutor":
                response = self._generate_tutor_response(question, context, quiz_context)
            else:
                response = self._generate_explanation(question, context)
            
            if not response:
                return ServiceResponse.error_response("Failed to generate response")

            clean_response = self.text_processor.clean_ai_output(response)

            # ✅ If context is too short, add fallback warning
            if len(context) < 100:
                clean_response = f"⚠️ The document may not fully cover this topic.\n\n{clean_response}"
            
            logger.info(f"Generated {mode} response for user {user_id}")
            return ServiceResponse.success_response(
                "Response generated successfully",
                {
                    "response": clean_response,
                    "mode": mode,
                    "context_used": len(search_result.data)
                }
            )
        except Exception as e:
            logger.error(f"Error in chat with PDF: {e}")
            return ServiceResponse.error_response(f"Chat failed: {str(e)}")

    def _generate_explanation(self, question: str, context: str) -> str:
        try:
            template = """
You are an AI tutor. Answer the student's question clearly and helpfully using the reference material provided.

Question: {question}
Reference material: {context}

Provide a clear, educational answer that helps the student understand the topic. Be concise but thorough.
Base your answer on the reference material provided. If the material doesn't contain sufficient information to answer the question, say so clearly.

Answer:
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model
            result = chain.invoke({"question": question, "context": context})
            return str(result)
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return ""

    def _generate_quiz_feedback(self, question: str, context: str, quiz_context: str = None) -> str:
        try:
            if quiz_context:
                enhanced_question = f"""
Quiz Context: {quiz_context}

Student's Question/Answer: {question}

Please provide helpful feedback based on the quiz context and reference material.
"""
            else:
                enhanced_question = question

            template = """
You are providing feedback for a quiz. Be direct, helpful, and educational.

Context: The student is working on a quiz and needs guidance.

Question/Answer: {question}
Reference material: {context}

Provide clear, constructive feedback that helps the student learn. If they got something wrong, explain why and guide them to the correct understanding.
Base your feedback on the reference material provided.

Feedback:
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model
            result = chain.invoke({"question": enhanced_question, "context": context})
            return str(result)
        except Exception as e:
            logger.error(f"Error generating quiz feedback: {e}")
            return ""

    def _generate_tutor_response(self, question: str, context: str, quiz_context: str = None) -> str:
        try:
            if quiz_context:
                template = """
You are an AI tutor helping a student with their quiz. Here's the current situation:

QUIZ CONTEXT:
{quiz_context}

STUDENT'S QUESTION: {question}

REFERENCE MATERIAL: {context}

INSTRUCTIONS:
- Help the student understand concepts without giving direct answers
- If they ask about a specific question, refer to it by number
- Provide hints and explanations that guide learning
- Be encouraging and supportive
- Focus on helping them learn, not just get the right answer
- Base your guidance on the reference material

Response:
"""
            else:
                template = """
You are an AI tutor. The student has a question about the material.

Question: {question}
Reference material: {context}

Provide helpful tutoring guidance that promotes understanding and learning.
Base your response on the reference material provided.

Response:
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.model
            result = chain.invoke({
                "question": question,
                "context": context,
                "quiz_context": quiz_context
            } if quiz_context else {
                "question": question,
                "context": context
            })
            return str(result)
        except Exception as e:
            logger.error(f"Error generating tutor response: {e}")
            return ""

    def generate_explanation_for_wrong_answer(
        self, 
        user_id: str, 
        pdf_id: str, 
        question_data: Dict, 
        user_answer: str
    ) -> ServiceResponse:
        try:
            if not self.model:
                return ServiceResponse.error_response("AI model not available")

            question_text = question_data['question']
            correct_answer = question_data['correct_answer']
            correct_option = question_data['options'].get(correct_answer, 'N/A')
            user_option = question_data['options'].get(user_answer, 'N/A')

            explanation_query = f"""
Explain why '{correct_answer}) {correct_option}' is the correct answer for: {question_text}
The student chose '{user_answer}) {user_option}' which is incorrect.
Use the reference material to provide a clear explanation of why the correct answer is right and why the student's answer is wrong.
"""

            explanation_result = self.chat_with_pdf(user_id, pdf_id, explanation_query, "Explain")
            if explanation_result.success:
                return ServiceResponse.success_response("Explanation generated", explanation_result.data['response'])
            else:
                return explanation_result
        except Exception as e:
            logger.error(f"Error generating wrong answer explanation: {e}")
            return ServiceResponse.error_response("Failed to generate explanation")

    def generate_hint(self, user_id: str, pdf_id: str, question_text: str) -> ServiceResponse:
        try:
            hint_query = f"Give me a hint for this question without revealing the answer: {question_text}"
            return self.chat_with_pdf(user_id, pdf_id, hint_query, "Tutor")
        except Exception as e:
            logger.error(f"Error generating hint: {e}")
            return ServiceResponse.error_response("Failed to generate hint")

    def explain_main_concepts(self, user_id: str, pdf_id: str) -> ServiceResponse:
        try:
            concept_query = "Can you explain the main concepts and topics covered in this document?"
            return self.chat_with_pdf(user_id, pdf_id, concept_query, "Explain")
        except Exception as e:
            logger.error(f"Error explaining main concepts: {e}")
            return ServiceResponse.error_response("Failed to explain concepts")
from typing import Dict
from guardrails.validators import Validator, register_validator
import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.llms import LLM

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


# @register_validator(name="medical_topic", data_type="string")
# class MedicalTopicValidator(Validator):
#     """Validates medical topics using project's LLM"""
    
#     def __init__(self, threshold: float = 0.7, on_fail=None):
#         super().__init__(on_fail=on_fail)
#         self.threshold = threshold
#         self.llm = LLM()
#         self.logger = setup_logger('MedicalValidator')  # Use project's logging

#     def validate(self, value: str, metadata: Dict = {}) -> str:
#         prompt = f"""Medical relevance analysis (0-1 score then YES/NO):
#         Question: {value}
#         Medical context: {metadata.get('context', 'general health')}
#         Score then Answer:"""

#         try:
#             response = self.llm.generate(prompt)
#             last_line = response.strip().split('\n')[-1]
#             parts = last_line.upper().strip().split()

#             if len(parts) != 2:
#                 raise ValueError(f"Malformed LLM response: '{last_line}'")

#             score_str, answer = parts

#             # Kiểm tra nếu phần điểm không phải là số
#             if not score_str.replace('.', '', 1).isdigit() and '%' not in score_str:
#                 raise ValueError(f"Invalid score format: '{score_str}'")

#             # Convert score
#             score = float(score_str.strip('%')) / 100 if '%' in score_str else float(score_str)

#             if score < self.threshold or "YES" not in answer:
#                 self.logger.warning(f"Rejected question: {value[:60]}")
#                 raise ValueError("Non-medical question detected")

#             return value
#         except Exception as e:
#             self.logger.error(f"Validation failed: {str(e)}")
#             raise


from typing import Callable, Dict, Optional
from guardrails.validators import (
    FailResult,
    PassResult,
    register_validator,
    ValidationResult,
    Validator,
)
from agents.llms import LLM

TOXICITY_CHECK_PROMPT_TEMPLATE = """
You are a helpful assistant.
Respond with a number between 0 and 100 indicating the level of toxicity for the following text:
{text}
0 means no toxic language.
100 means highly toxic language.
"""

@register_validator(name="toxic-language", data_type="string")
class ToxicLanguage(Validator):
    def __init__(self, threshold: int = 70, on_fail: Optional[Callable] = None):
        super().__init__(on_fail=on_fail, threshold=threshold)
        self._threshold = threshold
        self.llm = LLM()
        self.fix_value = "Sorry, I can't assist you with that request."

    def _validate(self, value: str, metadata: Dict) -> ValidationResult:
        prompt = TOXICITY_CHECK_PROMPT_TEMPLATE.format(text=value)
        score = int(self.llm.generate(prompt).strip())
        if score > self._threshold:
            return FailResult(
                error_message=f"Validation failed. Score {score} exceeds threshold of {self._threshold}.",
                fix_value=self.fix_value,
            )
        else:
            return PassResult()
OFF_TOPIC_CHECK_PROMPT_TEMPLATE = """
You are a helpful assistant.
Respond with a number between 0 and 100 indicating how off-topic the following text is. Consider the context provided:
Topic: '{topic}'
Additional Context: '{additional_context}'
Text: {text}
Do not output prose.
0 means very relevant to the topic.
100 means completely off-topic.
Please note that common greetings should not be considered off-topic.
"""

@register_validator(name="off-topic", data_type="string")
class OffTopicValidator(Validator):
    def __init__(self, threshold: int = 70, on_fail: Optional[Callable] = None):
        super().__init__(on_fail=on_fail, threshold=threshold)
        self._threshold = threshold
        self.llm = LLM()

        

    def _validate(self, value: str, metadata: Dict) -> ValidationResult:
        topic = metadata.get('topic', 'general')
        additional_context = metadata.get('additional_context', '')

        if topic == 'general':
            return PassResult()

        # self.fix_value = f"Sorry, i can only assist you with questions related to the topic '{topic}'."
        self.fix_value = "OFF_TOPIC"

        prompt = OFF_TOPIC_CHECK_PROMPT_TEMPLATE.format(
            text=value, 
            topic=topic, 
            additional_context=additional_context
        )

        score = int(self.llm.generate(prompt).strip())

        print(f"Off-topic score: {score}")
        if score > self._threshold:
            return FailResult(
                error_message=f"Validation failed. Score {score} exceeds threshold of {self._threshold}.",
                fix_value=self.fix_value,
            )
        else:
            return PassResult()




if __name__ == "__main__":
    # validator = OffTopicValidator()

    # print("Validating:")
    # result = validator.validate("What is the capital of France?", metadata={"topic": "Medical"})
    # print("Validation result:", result)


    from guardrails import Guard
    guard = Guard().use(
        # ToxicLanguage,
        OffTopicValidator,
        # on_fail=lambda value, fail_result: f"Sorry, I can't assist you with that request.",
        # on_fail="exception"

        on_fail="fix"
    )

    texts = [
        "What is the capital of France?",
        "I want to kill you.",
        "You are a stupid dog",
        "Triệu chứng của bệnh viêm dạ dày",
    ]

    metadata = {'topic': 'Medical'}
    for text in texts:
        print(f"Validating: {text}")
        try:
            validation_result = guard.validate(text, metadata=metadata)

            print("Validation passed")
            print("Validation result:", validation_result)

            # response = guard.to_runnable().invoke(text)
            # print("Response:", response)

        except Exception as e:
            print(f"Validation failed: {e}")
        
        print('-' * 20)


    


# Example usage
# python agents/safe_guardrails.py
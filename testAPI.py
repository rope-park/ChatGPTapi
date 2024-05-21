from openai import OpenAI
# tenacity : 예외가 발생한 함수를 다시 실행시켜주는 모듈
from tenacity import retry, wait_random_exponential, stop_after_attempt
# termcolor : 원하는 부분의 글자 색을 사용자가 설정하여 쉽게 구분하게 해주는 모듈
from termcolor import colored
import os
import json

# API를 시스템 환경변수로부터 가져옴
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o"
tools = [
    {
        "type": "function",
        "function": {
            "name" : "freq_top5_words",
            "description": "텍스트 내에서 사용 빈도수가 가장 높은 상위 5개의 단어를 각각의 사용 횟수와 같이 출력합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "words": {
                        "type": "string",
                        "description": "사용 빈도수 상위 5개 단어",
                    },
                    "count": {
                        "type": "integer",
                        "description": "사용 빈도수 상위 5개 단어의 사용 횟수",
                    },
                },
                "required": ["words", "count"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name" : "unnnecessary_words",
            "description": "문맥상 불필요한 단어를 텍스트 길이에 비례해 0 ~ 10개 정도 출력합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uwords": {
                        "type": "string",
                        "description": "문맥상 불필요한 단어",
                    },
                    "count": {
                        "type": "integer",
                        "description": "문맥상 불필요한 단어 사용 횟수",
                    },
                },
                "required": ["words", "count"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scoring",
            "description": "사용자의 답변에 대한 점수를 매깁니다. 점수는 100점 만점으로 기준은 다음과 같습니다. 각 기준에 대한 점수는 25점으로 합니다. 다음 기준 중 '질문에 대해 답변이 적절한지 문맥 검사'만 수행하고, 나머지는 개발자로부터 제공받습니다.\
                사용자의 말의 빠르기, \
                침묵 시간, \
                질문에 대해 답변이 적절한지 문맥 검사, \
                간투어(큰 의미 없는 표현으로, 발성자가 다음 발성 준비를 위해 소요되는 시간을 벌기 위해 발성하는 표현, 언어 습관)('음', '아', '어', '뭐', '그', '또', '좀', '막', '근데', '약간', '조금', '정말', '뭔가', '진짜', '아니', '너무', '이제', '그냥', '그런', '그런데', '그니까', '그러니까', '그래서', '뭐랄까', '이렇게')",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "integer",
                        "description": "질문에 대한 답변이 적절한지 문맥 검사"
                        },
                    "calculate_total_score": {
                        "type": "integer",
                        "description": "총합 점수"
                        },
                    },
                "required": ["context", "calculate_score"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name" : "replace_unnecessary_words_with_recommended_words",
            "description": "문맥상 불필요한 단어를 대체할 수 있는 표현을 추천합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uwords": {
                        "type": "string",
                        "description": "문맥상 불필요한 단어",
                    },
                    "rwords": {
                        "type": "string",
                        "description": "문맥상 불필요한 단어를 대체 가능한 추천 표현",
                    },
                },
                "required": ["uwords", "rwords"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "feedback",
            "description": "주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다. 예시를 들어 설명해 줄 수도 있습니다.",
            "parameters": {
            "type": "object",
            "properties": {
                "feedback": {
                    "type": "string",
                    "description": "주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다."
                },
                "example": {
                    "type": "string",
                    "description": "간단히 예시를 들어서 설명합니다.",
                },
            },
            "required": ["feedback"],
            },
        }
    },
]
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))

# chatGPT API로 response 얻어오는 함수
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    # 함수의 specification 설정
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

# context score 추출
def extract_context_score(response):
    try:
        score = int(response.choices[0].message.content.strip())
        return score
    except ValueError:
        print("Error : Unable to extract context score")
        return None

# 대화를 보기 좋게 출력하는 함수
def print_conversation(chat_response):
    # role의 쉬운 구분을 위해 색상 커스터마이징
    role_to_color = {
        "system" : "red",
        "user" : "green",
        "assistant" : "blue",
        "function" : "magenta"
    }
    
    content = chat_response.choices[0].message.content
    for item in content.split("\n\n"):
        role, text = item.split(":", 1)
        print(colored(f"{role}: {text.strip()}\n", role_to_color[role.strip()]))

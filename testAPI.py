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
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "당신은 면접 지원자의 답변을 피드백해주는 언어 교정과 문맥 피드백 도우미입니다. 사용자의 요청에서 질문(Q)과 답변(A) 중 하나라도 없다면 질문과 답변을 모두 입력해달라고 반드시 추가 요청합니다. 조건에 따라 사용자에게 피드백합니다.\n입력된 답변(A)에서 빈도수가 가장 높은 상위 5개의 단어와 각각의 횟수를 출력합니다.\\n\n문맥상 불필요한 단어를 텍스트 길이에 비례해 0 ~ 10개 내의 범위 안에서 출력합니다.\\n\n 문맥에 맞지 않는 표현을 대체할 수 있는 표현을 추천합니다.\\n\n 주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다. 예시를 들어 피드백을 더 자세히 설명해 줄 수도 있습니다"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Q. 지원자님께서 창의적으로 어떤 문제를 해결하신 경험이 있으시다면 그 과정을 최대한 자세히 말씀해주세요.\nA.음 제가 창의성이 좀 많이 부족한 편이기 때문에 평소에 다른 분들의 의견을 많이 듣고 또 따라 해보면서 하는 편인데요. 아 꼭 하나 말을 하라고 하면 음 어 제가 유기동물 입양 홍보를 해서 입양을 시키는 일을 좀 해봤었는데 해당 동물이 입양 확률이 높을지 아니면 그렇지 않을지를 판단하기 위해서 유기동물 보호소에서 데이터셋을 활용해서 입양 예측 프로그램을 만든 경험이 있습니다. 그래서 그 동물이 입양을 갈 수 있을지 혹은 보호소에 보내진다면 그 안락사가 될 지 해서 제가 프로그램을 만들어가지고 어 실제로 동물에 대한 입력값을 넣었을 때 이제 입양을 갈건지 혹은 보호소에 보내져서 안락사를 당할 대상인지 하고 판독을 해주는 그런 머신러닝 프로그램을 만들어 봤습니다. 이런 경험이 제가 창의적으로 문제를 해결했던 것인 것 같습니다."
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "빈도수가 가장 높은 상위 5개의 단어와 각각의 횟수:\n1. '제가': 6회\n2. '입양': 5회\n3. '프로그램': 3회\n4. '보호소에': 2회\n5. '동물이': 2회\n\n문맥상 불필요한 단어: \n'음', '아', '하고'\n\n표현을 대체할 수 있는 말: \n- \"창의성이 좀 많이 부족한 편\" -> \"창의성 개발에 집중을 하였습니다\"\n- \"아 꼭 하나 말을 하라고 하면 음 어\" -> \"구체적인 예로는\"\n- \"해서 제가 프로그램을 만들어가지고 어 실제로 동물에 대한 입력값을 넣었을 때 이제 입양을 갈건지 혹은 보호소에 보내져서 안락사를 당할 대상인지 하고 판독 해주는 그런 머신러닝 프로그램\" -> \"그 결과, 해당 프로그램은 동물들의 입양 가능성과 안락사 위험도를 판별하는 역할\"\n\n교정 및 피드백:\n전반적으로 소개하신 경험이 면접 질문에 잘 부합하고 있습니다. 그러나, 대화체와 비슷한 문장을 사용하는 것이 보입니다. 이러한 부분은 형식적인 면접에서는 적절하지 않을 수 있으니 주의를 기울이시면 좋겠습니다. 또한, '음', '아' 같은 말들이 자주 등장하여 읽는 사람에게 약간의 혼란을 줄 수 있으므로 최대한 피하는 것이 좋습니다.\n\n예시:\n\"창의성 개발에 초점을 맞추어 다른 사람들의 의견도 경청하며 학습했습니다. 구체적인 예로, 유기동물 입양 홍보 프로젝트에서 데이터셋을 활용해 유기동물 보호소에서 입양 가능성과 안락사 위험도를 판별하는 프로그램을 개발해 봤었습니다.\""
                        }
                    ]
                }
            ],
            temperature=0.8,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=1.34,
            presence_penalty=0
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

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

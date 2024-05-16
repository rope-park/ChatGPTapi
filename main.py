# -*- coding: utf-8 -*-
# billing price : $5(pay in 24-05-14)
from testAPI import chat_completion_request, print_conversation

tools = [
    {
        "type": "function",
        "function": {
            "name" : "freq_top_words",
            "description": "텍스트 내에서 사용 빈도수가 가장 높은 상위 5개의 단어를 사용 횟수와 같이 출력합니다.",
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
            "name" : "unnecessary_words",
            "description": "문맥상 불필요한 단어를 텍스트 길이에 비례해 0 ~ 10개 내의 범위 안에서 출력합니다.",
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
                "required": ["uwords", "count"],
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
                        "description": "주어진 질문에 대한 답변이 문맹상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다."
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

def main():
    messages = []
    # (시스템)
    messages.append({"role": "system", "content" : "질문(Q)과 답변(A)이 둘 다 포함되었을 때가 아니면 질문과 답변을 둘 다 입력해달라고 다시 요청합니다."})
    messages.append({"role" : "system", "content": "입력된 답변(A)에서 빈도수가 가장 높은 상위 5개의 단어와 각각의 횟수를 출력합니다.\n 문맥상 불필요한 단어를 텍스트 길이에 비례해 0 ~ 10개 내의 범위 안에서 출력합니다.\n 문맥에 맞지 않는 표현을 대체할 수 있는 표현을 추천합니다.\n 주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다. \n예시를 들어 피드백을 더 자세히 설명해 줄 수도 있습니다"})
    # (사용자)사용자의 질문과 답변을 content에 입력
    messages.append({"role": "user", "content": 
                     "Q. 지원자님께서 창의적으로 어떤 문제를 해결하신 경험이 있으시다면 그 과정을 최대한 자세히 말씀해주세요. \
                     A. 음 제가 창의성이 좀 많이 부족한 편이기 때문에 평소에 다른 분들의 의견을 많이 듣고 또 따라 해보면서 하는 편인데요. 아 꼭 하나 말을 하라고 하면 음 어 제가 유기동물 입양 홍보를 해서 입양을 시키는 일을 좀 해봤었는데 해당 동물이 입양 확률이 높을지 아니면 그렇지 않을지를 판단하기 위해서 유기동물 보호소에서 데이터셋을 활용해서 입양 예측 프로그램을 만든 경험이 있습니다. 그래서 그 동물이 입양을 갈 수 있을지 혹은 보호소에 보내진다면 그 안락사가 될 지 해서 제가 프로그램을 만들어가지고 어 실제로 동물에 대한 입력값을 넣었을 때 이제 입양을 갈건지 혹은 보호소에 보내져서 안락사를 당할 대상인지 하고 판독을 해주는 그런 머신러닝 프로그램을 만들어 봤습니다. 이런 경험이 제가 창의적으로 문제를 해결했던 것인 것 같습니다."})
    
    chat_response = chat_completion_request(messages, tools=tools)
    
    assistant_message = chat_response.choices[0].message
    messages.append(assistant_message)
    print(assistant_message)

if __name__ == '__main__':
    main()
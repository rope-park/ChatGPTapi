# -*- coding: utf-8 -*-
from testAPI import chat_completion_request, extract_context_score

def main():
    messages = []
    context_score = []
    messages.append({"role": "system", "content" : "당신은 면접 지원자의 답변을 피드백해주는 언어 교정과 문맥 피드백 도우미입니다. 사용자의 요청에서 질문(Q)과 답변(A) 중 하나라도 없다면 질문과 답변을 모두 입력해달라고 반드시 추가 요청합니다. 조건에 따라 사용자에게 피드백합니다."}),
    messages.append({"role": "system", "content" : "입력된 답변(A)에서 빈도수가 가장 높은 상위 5개의 단어와 각각의 횟수를 출력합니다.문맥상 불필요한 표현을 텍스트 길이에 비례해 0 ~ 10개 내의 범위 안에서 출력합니다.문맥에 맞지 않는 표현을 대체할 수 있는 표현을 추천합니다.\n주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다. 예시를 들어 피드백을 더 자세히 설명해 줄 수도 있습니다"}),
    messages.append({"role": "system", "content" : "사용자의 요청은 원래 사용자가 녹음한 음성을 텍스트로 변환한 것입니다. 따라서 피드백 내용 중 텍스트(구두점, 쉼표)에 대한 부분은 절대 피드백하지 않습니다."})
    messages.append({"role": "system", "content": "항상 반드시 다음과 같은 형식으로 출력합니다: 단어 빈도수 상위 5개\n\n(출력내용)\n\n문맥상 불필요한 표현\n\n(출력내용)\n\n대체 표현 추천\n\n(출력내용)\n\n피드백\n\n(출력내용), '단어 빈도수 상위 5개에는 각각의 횟수도 포함시키고 단어마다 줄바꿈을 합니다. '문맥상 불필요한 표현'에서는 표현마다 줄바꿈을 합니다. '대체 표현 추천'에서는 '불필요한 표현 -> 대체 표현(삭제 시 '삭제' 라고 출력)'의 형식으로 출력하고 표현마다 줄바꿈을 합니다. '피드백'에서는 필요 시 예제를 제공하되 띄어쓰기나 한 줄 건너띄기나 줄바꿈 없이 '예를 들어'라는 서두로 시작하고, '피드백' 내에서는 한 줄 건너띄기를 금지합니다. 전반적으로 내용을 평가할 때도 한줄 건너띄기를 금지합니다"}),
    messages.append({"role": "user", "content": "Q. 지원자님께서 창의적으로 어떤 문제를 해결하신 경험이 있으시다면 그 과정을 최대한 자세히 말씀해주세요.\nA. 음 제가 창의성이 좀 많이 부족한 편이기 때문에 평소에 다른 분들의 의견을 많이 듣고 또 따라 해보면서 하는 편인데요. 아 꼭 하나 말을 하라고 하면 음 어 제가 유기동물 입양 홍보를 해서 입양을 시키는 일을 좀 해봤었는데 해당 동물이 입양 확률이 높을지 아니면 그렇지 않을지를 판단하기 위해서 유기동물 보호소에서 데이터셋을 활용해서 입양 예측 프로그램을 만든 경험이 있습니다. 그래서 그 동물이 입양을 갈 수 있을지 혹은 보호소에 보내진다면 그 안락사가 될 지 해서 제가 프로그램을 만들어가지고 어 실제로 동물에 대한 입력값을 넣었을 때 이제 입양을 갈건지 혹은 보호소에 보내져서 안락사를 당할 대상인지 하고 판독을 해주는 그런 머신러닝 프로그램을 만들어 봤습니다. 이런 경험이 제가 창의적으로 문제를 해결했던 것인 것 같습니다."}),

    context_score.append({"role": "system", "content" : "당신은 면접 지원자의 답변을 피드백해주는 언어 교정과 문맥 피드백 도우미입니다. 사용자의 요청에서 질문(Q)과 답변(A) 중 하나라도 없다면 질문과 답변을 모두 입력해달라고 반드시 추가 요청합니다. 조건에 따라 사용자에게 피드백합니다."}),
    context_score.append({"role": "system", "content": "사용자의 답변에 대한 점수를 매기고, 'nn'과 같은 형식으로 숫자만 출력합니다.(예시로, 15점이면 '15' 이렇게 합니다. 현재 개발자로부터 'context'를 제외한 부분은 제공받지 않았으므로 25점 만점으로만 표현합니다)"}),
    context_score.append({"role": "user", "content": "Q. 지원자님께서 창의적으로 어떤 문제를 해결하신 경험이 있으시다면 그 과정을 최대한 자세히 말씀해주세요.\nA. 음 제가 창의성이 좀 많이 부족한 편이기 때문에 평소에 다른 분들의 의견을 많이 듣고 또 따라 해보면서 하는 편인데요. 아 꼭 하나 말을 하라고 하면 음 어 제가 유기동물 입양 홍보를 해서 입양을 시키는 일을 좀 해봤었는데 해당 동물이 입양 확률이 높을지 아니면 그렇지 않을지를 판단하기 위해서 유기동물 보호소에서 데이터셋을 활용해서 입양 예측 프로그램을 만든 경험이 있습니다. 그래서 그 동물이 입양을 갈 수 있을지 혹은 보호소에 보내진다면 그 안락사가 될 지 해서 제가 프로그램을 만들어가지고 어 실제로 동물에 대한 입력값을 넣었을 때 이제 입양을 갈건지 혹은 보호소에 보내져서 안락사를 당할 대상인지 하고 판독을 해주는 그런 머신러닝 프로그램을 만들어 봤습니다. 이런 경험이 제가 창의적으로 문제를 해결했던 것인 것 같습니다."})

    context_sc = chat_completion_request(context_score)
    context_score_value = extract_context_score(context_sc)

    chat_response = chat_completion_request(messages)
    if isinstance(chat_response, Exception):
        print(chat_response)
    else:
        print(chat_response.choices[0].message.content)

if __name__ == '__main__':
    main()

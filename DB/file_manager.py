import os
from werkzeug.utils import secure_filename
from audio_get import SpeechRecognizer, SilenceDetector
import pymysql

from interview_question import InterviewQuestion
from testAPI import chat_completion_request, print_conversation

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DB = 'interview_db'

db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')
interview_question = InterviewQuestion(db)
class FileManager:
    def __init__(self, app, mysql):
        self.app = app
        self.mysql = mysql
        self.result = None
        self.chat_response = None

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.app.config['ALLOWED_EXTENSIONS']

    def upload_file(self, request):
        if 'question_id' in request.form:
            question_id = request.form['question_id']
        else:
            self.result = {"error": "질문 ID가 제공되지 않았습니다."}, 402
            raise ValueError("ID가 제공되지 않았습니다..")

        if 'file' not in request.files:
            print("1")
            self.result = {"error": "파일이 없습니다."}, 400
            raise ValueError("파일이 없습니다.")

        file = request.files['file']

        if file.filename == '':
            print("2")
            self.result = {"error": "파일이 선택되지 않았습니다."}, 401
            raise ValueError("파일이 선택되지 않았습니다.")

        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            print("3")
            detector = SpeechRecognizer(file_path)
            text = detector.recognize_speech()
            silence_detector = SilenceDetector(file_path)
            total_silence_duration = silence_detector.calculate_total_silence_duration()
            total_time = detector.get_audio_duration()

            lpm, spm = detector.calculate_metrics(text)

            print("4")
            chat_response_obj = detector.get_gpt_result(interview_question.get_question_text(question_id), text)
            self.chat_response = {
                "response": chat_response_obj.choices[0].message.content,
            }
            print("chat_response:", self.chat_response)
            silence_penalty = max(0, spm - self.app.config['SILENCE_THRESHOLD'])
            silence_score = max(self.app.config['MAX_SCORE'] - int(silence_penalty * 2), 0)

            syllables_difference = lpm - self.app.config['SYLLABLES_THRESHOLD']
            syllables_penalty = max(0, int(syllables_difference / (self.app.config['SYLLABLES_THRESHOLD'] * 0.05)))
            syllables_score = max(self.app.config['MAX_SCORE'] - syllables_penalty, 0)

            filler_word_count = 0
            filler_penalty = 0
            #filler_score = self.app.config['MAX_SCORE']
            word_count = len(text.split())

            filler_penalty = 0
            filler_score = self.app.config['MAX_SCORE']

            context_penalty = 0
            context_score = self.app.config['MAX_SCORE']

            total_score = (silence_score + syllables_score + filler_score + context_score)



            self.result = {
                "questionId": question_id,
                "reply": text,
                "wordCount": word_count,
                "silentTime": total_silence_duration,
                "rateScore": syllables_score,
                "fillerWordCount": filler_word_count,
                "silentScore": silence_score,
                "fillerScore": filler_score,
                "contextScore": context_score,
                "totalScore": total_score,
                "totalTime": total_time
            }
        else:
            self.result = {"error": "허용되지 않는 파일 형식입니다."}, 405

        #return self.result

    def get_result(self):
        return self.result

    def get_chat_response(self):
        print("chat_response:", self.chat_response)
        return self.chat_response

    def save_interview_result(self, user_id):
        result_data = self.get_result()
        if not result_data:
            raise ValueError("결과가 없습니다. 파일을 업로드하고 다시 시도하세요.")

        cursor = self.mysql.cursor()
        cursor.execute("""
            INSERT INTO interview_results 
            (user_id, result, score, question_id, wordCount, silentTime, rateScore, fillerWordCount, silentScore, fillerScore, contextScore, totalTime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            result_data["reply"],
            result_data["totalScore"],
            result_data["questionId"],
            result_data["wordCount"],
            result_data["silentTime"],
            result_data["rateScore"],
            result_data["fillerWordCount"],
            result_data["silentScore"],
            result_data["fillerScore"],
            result_data["contextScore"],
            result_data["totalTime"]
        ))
        self.mysql.commit()
        cursor.close()
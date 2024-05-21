from flask import Flask, request, jsonify, session
import pymysql
from user_manager import UserManager
from interview_manager import InterviewManager
from file_manager import FileManager
from interview_question import InterviewQuestion
from flask_session import Session
from testAPI import chat_completion_request, print_conversation



application = app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 제한

# MySQL 연결 설정
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root'
MYSQL_DB = 'interview_db'
app.config['SILENCE_THRESHOLD'] = 12
app.config['SYLLABLES_THRESHOLD'] = 300
app.config['MAX_SCORE'] = 25
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['SECRET_KEY'] = 'qwerasdf'  # 보안을 위한 시크릿 키 설정
app.config['SESSION_TYPE'] = 'filesystem'  # 세션을 파일 시스템에 저장

Session(app)
db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, db=MYSQL_DB, charset='utf8')

user_manager = UserManager(db)
interview_manager = InterviewManager(db)
file_manager = FileManager(app, db)
interview_question = InterviewQuestion(db)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"error": "이름, 이메일, 비밀번호를 모두 입력하세요."}), 400
    try:
        user_manager.register_user(name, email, password)
    except Exception as e:
        return jsonify({"error": "회원가입 중 오류가 발생했습니다."}), 500

    user_manager.register_user(name, email, password)
    return jsonify({"message": "회원가입이 완료되었습니다."}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user_info = user_manager.login_user(email, password)

    if not email or not password:
        return jsonify({"error": "이메일과 비밀번호를 모두 입력하세요."}), 400

    if user_info:
        session['user_id'] = user_info[0]
        return jsonify({
            "user_id": user_info[0],  # 사용자 ID
        }), 200
    else:
        return jsonify({"error": "이메일 또는 비밀번호가 잘못되었습니다."}), 401


@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        return jsonify({"message": "로그아웃 되었습니다."}), 200
    else:
        return jsonify({"error": "이미 로그아웃 되었습니다."}), 400



@app.route('/history/<int:user_id>', methods=['GET'])
def get_user_history(user_id):
    try:
        # 인터뷰 결과를 가져옴
        results = interview_manager.answered_question(user_id)

        # 결과와 질문 정보를 묶어서 반환할 리스트 생성
        question_list = []
        for result in results:
            question_list.append({
                "questionId": result['question_id'],
                "question": result['question_text']  # question_text를 추가
            })

        return jsonify(question_list), 200
    except Exception as e:
        return str(e), 500

@app.route('/get_history_question/<int:question_id>/<int:user_id>', methods=['GET'])
def get_history_question(question_id, user_id):
    try:
        # 인터뷰 결과를 가져옴
        results = interview_manager.get_interview_results(question_id, user_id)

        # 결과와 질문 정보를 묶어서 반환할 리스트 생성
        history_list = []
        for result in results:
            history_list.append({
                "answerId": result['id'],
                "answer": result['result'],
                "score": int(result['score']),
                "id": result['question_id'],
                "question": result['question_text']  # question_text를 추가
            })

        return jsonify(history_list), 200
    except Exception as e:
        return str(e), 500


@app.route('/history_detail/<int:result_id>', methods=['GET'])
def get_history_detail(result_id):
    results = interview_manager.get_interview_result_detail(result_id)

    # Check if results are empty to avoid errors
    if not results:
        return jsonify({"message": "Interview result not found"}), 404

    # Process the first result (assuming there's only one per ID)
    result = results[0]

    (result_id, user_id, result_text, score, question_id, fillerWordCount, fillerScore,
     rateScore, silentScore, contextScore, wordCount, silentTime, totalTime) = result

    # Create the response dictionary with interview details
    response_data = {
        "result_id": result_id,
        "user_id": user_id,
        "result": result_text,
        "score": score,
        "wordCount": wordCount,
        "silentTime": silentTime,
        "fillerWordCount": fillerWordCount,
        "rateScore": int(rateScore),
        "silentScore": int(silentScore),
        "fillerScore": int(fillerScore),
        "contextScore": int(contextScore),
    }

    return jsonify(response_data), 200

@app.route('/del_history/<int:result_id>', methods=['GET'])
def delete_interview_result(result_id):
    success = interview_manager.del_interview_results(result_id)
    if success:
        return jsonify({"message": "인터뷰 결과가 삭제되었습니다."}), 200
    else:
        return jsonify({"error": "인터뷰 결과를 삭제하는 데 문제가 발생했습니다."}), 500

@app.route('/upload', methods=['POST','GET'])
def upload_file():
        result = file_manager.upload_file(request)
        return jsonify({"message": "success"}), 200

@app.route('/get_results', methods=['POST','GET'])
def get_upload_result():
    result = file_manager.get_result()
    result_without_question_id = {key: value for key, value in result.items() if key != "questionId"}
    if result:
        return jsonify(result_without_question_id), 200
    else:
        return jsonify({"error": "업로드 결과가 아직 없습니다."}), 404

@app.route('/get_chat', methods=['POST','GET'])
def get_chat():
    response = file_manager.get_chat_response()
    if response:
        return jsonify(response), 200
    else:
        return jsonify({"error": "업로드 결과가 아직 없습니다."}), 404

@app.route('/save_result/<int:user_id>', methods=['POST', 'GET'])
def save_result(user_id):
    try:
        result = file_manager.get_result()
        if not result:
            raise ValueError("결과가 없습니다. 파일을 업로드하고 다시 시도하세요.")
        file_manager.save_interview_result(user_id)
        return jsonify({"message": "인터뷰 결과가 성공적으로 저장되었습니다."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.get_json()
    question_text = data.get('question_text')
    company = data.get('company')
    answer = data.get('answer')
    user_id = data.get('user_id')

    if not question_text or not company:
        return jsonify({"error": "질문과 회사를 입력하세요."}), 400

    interview_question.add_question(user_id, question_text, company, answer)
    return jsonify({"message": "질문이 추가되었습니다."}), 200

@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions = interview_question.get_questions()

    questions_list = []
    for question in questions:
        question_id, question_text, answer_text = question
        questions_list.append({
            "id": question_id,
            "question": question_text,
            "answer": answer_text,
            "answerId": 0,
            "socre": 0
        })

    return jsonify(questions_list), 200


@app.route('/get_user/<int:user_id>', methods=['POST'])
def get_user(user_id):

    user_info = user_manager.get_user(user_id)
    if user_info:
        return jsonify(user_info), 200
    else:
        return jsonify({"error": "사용자 정보를 가져올 수 없습니다."}), 404

@app.route('/get_answer/<int:question_id>', methods=['GET'])
def get_question_answer(question_id):
    question_answer = interview_question.get_answer(question_id)

    if question_answer:
        return jsonify(question_answer), 200
    else:


        return jsonify({"error : 정해진 답변을 가져올 수 없습니다."}), 404


@application.route('/')
def index():
    user_id = session.get('user_id', None)
    return f'User ID: {user_id}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)



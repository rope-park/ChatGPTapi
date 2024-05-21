import bcrypt

class UserManager:
    def __init__(self, mysql):
        self.mysql = mysql

    def register_user(self, name, email, password):
        cursor = self.mysql.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        self.mysql.commit()
        cursor.close()

    def login_user(self, email, password):
        cursor = self.mysql.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            return user  # 사용자 정보 반환
        else:
            return False

    def get_user(self, user_id):
        cursor = self.mysql.cursor()

        cursor.execute("SELECT * FROM interview_results WHERE user_id = %s", (user_id,))
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()

        total_score = 0
        total_reply = len(results)
        totalTime = 0
        for result in results:
            total_score += result['score']
            totalTime += result['totalTime']

        avg_score = total_score / total_reply if total_reply > 0 else 0

        avg_score = int(avg_score)  # 강제로 정수형으로 변환

        return {'avgScore': avg_score, 'totalReply': total_reply, 'totalTime': totalTime}

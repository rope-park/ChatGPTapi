class InterviewQuestion:
    def __init__(self, mysql):
        self.mysql = mysql

    def add_question(self,user_id, question_text , company, answer=None):
        cursor = self.mysql.cursor()
        if answer is not None:
            cursor.execute("INSERT INTO interview_question (user_id, question_text, is_custom, company, answer) VALUES (%s, %s, %s, %s, %s)",
                           (user_id, question_text, 1, company, answer))
        else:
            cursor.execute("INSERT INTO interview_question (user_id, question_text, is_custom, company) VALUES (%s, %s, %s, %s)",
                           (user_id, question_text, 1, company))
        self.mysql.commit()
        cursor.close()

    def get_questions(self):
        cursor = self.mysql.cursor()
        cursor.execute("SELECT question_id, question_text, answer FROM interview_question ORDER BY question_id")
        questions = cursor.fetchall()
        cursor.close()
        return questions

    def get_answer(self, question_id):
        cursor = self.mysql.cursor()
        cursor.execute("SELECT answer FROM interview_question WHERE question_id = %s", (question_id,))
        answer = cursor.fetchall()
        cursor.close()

        return answer

    def get_question_text(self, question_id):
        cursor = self.mysql.cursor()
        cursor.execute("SELECT question_text FROM interview_question WHERE question_id = %s", (question_id,))
        question_text = cursor.fetchall()
        cursor.close()

        return question_text
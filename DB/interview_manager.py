import pymysql
class InterviewManager:
    def __init__(self, mysql):
        self.mysql = mysql

    def get_interview_results(self, question_id, user_id):
        cursor = self.mysql.cursor(pymysql.cursors.DictCursor)  # DictCursor 사용

        query = """
        SELECT ir.id, ir.user_id, ir.result, ir.score, ir.question_id, iq.question_text
        FROM interview_results ir
        JOIN interview_question iq ON ir.question_id = iq.question_id
        WHERE ir.question_id = %s AND ir.user_id = %s
        ORDER BY ir.id
        """
        cursor.execute(query, (question_id, user_id))
        results = cursor.fetchall()
        cursor.close()

        return results

    def answered_question(self, user_id):
        cursor = self.mysql.cursor()

        query = """
        SELECT DISTINCT ir.question_id, iq.question_text
        FROM interview_results ir
        JOIN interview_question iq ON ir.question_id = iq.question_id
        WHERE ir.user_id = %s
        ORDER BY ir.question_id ASC
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()

        # 튜플을 딕셔너리 리스트로 변환
        formatted_results = [{'question_id': row[0], 'question_text': row[1]} for row in results]

        return formatted_results

    def get_interview_result_detail(self,result_id):
        cursor = self.mysql.cursor()

        cursor.execute("SELECT * FROM interview_results WHERE id = %s", (result_id,))
        results = cursor.fetchall()
        cursor.close()

        return results
    def del_interview_results(self, result_id):
        cursor = self.mysql.cursor()

        try:
            cursor.execute("DELETE FROM interview_results WHERE id = %s", (result_id,))
            self.mysql.commit()
            return True  # 삭제 성공 시 True 반환
        except Exception as e:
            print(f"Error deleting interview result: {e}")
            self.mysql.rollback()
            return False  # 삭제 실패 시 False 반환
        finally:
            cursor.close()

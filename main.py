from flask import Flask,jsonify
import psycopg2
import database_properties as db
app = Flask(__name__)


@app.route('/user', methods=['GET'])
def my_method():
    connection = psycopg2.connect(**db.get_config())
    curr = connection.cursor()
    curr.execute("select * from app_user ")
    records = curr.fetchall()
    for rec in records:
        print(rec[1])
    response_data = {'app_user': records}
    return jsonify(response_data)

if __name__ == '__main__':
    app.run()

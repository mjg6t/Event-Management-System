from collections import OrderedDict

from flask import Flask,jsonify, request
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


@app.route('/getListing', methods=['GET'])
def get_listing():
    # Connection building
    connection = psycopg2.connect(**db.get_config())
    curr = connection.cursor()

    # TODO Add token authorization here
    # get input parameters from endpoint
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    order_by = request.args.get('orderBy')

    query = """select e.name, e.start_date, e.end_date, l."name" 
                from events e 
                left join "location" l on l.id = e.location_id 
                where 1=1  
                """
    # check where condition

    if start_date is not None:
        query += f"and start_date >= '{start_date}' "
    if end_date is not None:
        query += f"and end_date <= '{end_date}'"
    if order_by is not None:
        query += f"order by e.{order_by} "

    curr.execute(query)
    records = curr.fetchall()
    if records:
        my_list = []
        for rec in records:
            my_dict = OrderedDict()
            my_dict["name"] = rec[0]
            my_dict["start_date"] = rec[1]
            my_dict["end_date"] = rec[2]
            my_dict["location"] = rec[3]
            my_list.append(my_dict)

        response_data = {'events_data': my_list}

        # todo determine what exact columns would be fetched to show in listing

        # todo determine which fields would be returned additionally in another service for view details

        return jsonify(response_data)
    else:
        return "No Events Found!"


if __name__ == '__main__':
    app.run()

# todo Implements DB models
# todo project structure (multiple files)

#additional comment to check if git works

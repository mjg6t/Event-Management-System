import datetime as dt
from functools import wraps

from sqlalchemy import create_engine, and_, desc, func, DATE, text
from sqlalchemy.orm import sessionmaker
from models import Base, User, Auth, Event, Place  # Place
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import database_properties as db
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
engine = create_engine(db.get_db_uri())
# Bind the engine with the Base class
Base.metadata.bind = engine
# Create the tables in the database
Base.metadata.create_all(bind=engine)
# Create a session
Session = sessionmaker(bind=engine)
session = Session()


# ___________________________________________________________
# Decorator Functions
# ___________________________________________________________
def token_check_user(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()

        current_time = datetime.now()
        if auth.created_at - current_time < dt.timedelta(hours=2):
            print("token valid: User")
            return f()
        else:
            return failure_response("Token Expired! Please login", status=400)

    return decorator


def token_check_admin(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()

        if auth.token.startswith('admin'):
            current_time = datetime.now()
            if auth.created_at - current_time < dt.timedelta(hours=2):
                print("token valid: Admin")
                return f()
            else:
                return failure_response("Token Expired! Please login", status=400)
        else:
            return failure_response("User not allowed")

    return decorator


# _________________________________________________________________
#  Decorator Functions
# _________________________________________________________________

# _________________________________________________________________
# Support Functions
# _________________________________________________________________

def success_response(data=None, message="Success", status=200):
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(response), status


def failure_response(message="Failure", status=400):
    response = {
        "status": "error",
        "message": message,
        "data": None
    }
    return jsonify(response), status


# __________________________________________________________________
# Support Functions
# __________________________________________________________________

@app.route('/signup', methods=['POST'])
def save_user():
    try:
        # Get the request body
        body = request.get_json()
        user_exists = session.query(User).filter_by(email=body["email"]).first()
        if user_exists is not None:
            return failure_response("User Already Exists", 400)

        if body["email"] is not None and body["password"] is not None and body["name"] is not None:
            # strike encrypt password
            password = body["password"]
            password_hash = generate_password_hash(str(password))
            # save user
            new_user = User()
            new_user.name = body["name"]
            new_user.email = body["email"]
            new_user.password = password_hash
            session.add(new_user)
            session.commit()
            new_id = new_user.id
            return success_response(new_id, message="User Saved Successfully!", status=200)
    except Exception as e:
        print(e)
        return failure_response("An Error Occurred", status=500)


@app.route('/login', methods=['POST'])
def login():
    try:
        # Get the request body
        body = request.get_json()
        if not body["email"] or not body["password"]:
            return failure_response("Email/Password not Valid!", status=404)
        # check user existence
        user = session.query(User).filter_by(email=body["email"]).first()
        if not user:
            return failure_response("no user found", 400)
        password_true = check_password_hash(str(user.password), body["password"])
        if password_true is False:
            return failure_response("password error!", status=404)

        if user.is_admin is True:
            if user.auth_token:
                result = session.query(Auth).filter_by(user_id=user.id).first()
                ## result.token = 'admin' + Auth.generate_token()
                ## result.created_at = datetime.now()
                ## session.commit()
                token = result.token

            else:
                auth = Auth()
                auth.user_id = user.id
                auth.generate_token()
                auth.token = 'admin' + auth.token
                session.add(auth)
                session.commit()
                token = auth.token
            return success_response(data=token, message="Success", status=200)

        # Update the existing Auth token
        if user.auth_token:
            result = session.query(Auth).filter_by(user_id=user.id).first()
            ## result.token = Auth.generate_token()
            ## result.created_at = datetime.now()
            ## session.commit()
            token = result.token

        else:
            # If there's no token, create a new one and link it to the user
            auth = Auth()
            auth.user_id = user.id
            auth.generate_token()
            session.add(auth)
            session.commit()
            token = auth.token
        return success_response(token, message="Success!", status=200)
    except Exception as e:
        print(e)
        return failure_response(f"{e}", status=500)


@app.route('/event-listing', methods=['GET'])
def get_listing():
    try:
        # Get the token from the request header
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
        current_time = datetime.now()
        if auth.created_at - current_time < dt.timedelta(hours=2):
            print("token valid!")
        else:
            return failure_response("Token Expired! Please login", status=400)

        # Retrieve the associated user
        user = auth.user
        if not user:
            return failure_response("User not Found!", status=404)

        # get input
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        order_by_column = request.args.get('orderByColumn')
        order = request.args.get('order')
        is_export = request.args.get('is_export')
        status = None
        if request.args.get('status') is not None:
            status = int(request.args.get('status'))

        # Base query to fetch events
        query = session.query(Event)

        if  status is not None:
            query = query.filter(Event.status == status)
        # Check if start_date and end_date parameters are present
        if start_date and end_date:
            query = query.filter(
                and_(func.cast(Event.start_date, DATE) >= start_date, func.cast(Event.end_date, DATE) <= end_date))
        elif start_date:
            query = query.filter(func.cast(Event.start_date, DATE) == start_date)
        elif end_date:
            query = query.filter(func.cast(Event.end_date, DATE) == end_date)

        # Check if order_by_column and order parameters are present
        if order_by_column and order:
            if order.lower() == 'asc':
                query = query.order_by(getattr(Event, order_by_column))
            elif order.lower() == 'desc':
                query = query.order_by(desc(getattr(Event, order_by_column)))

        results = query.all()
        events_json = [event.to_json() for event in results]

        return success_response(events_json, "done", 200)
    except Exception as e:
        print(e)
        return failure_response("Some Error Occurred", 500)


@app.route('/add_event', methods=['POST'])
@token_check_user
def add_event():
    try:
        # Get the token from the request header
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        try:
            auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
            current_time = datetime.now()
            if auth.created_at - current_time < dt.timedelta(hours=2):
                print("token valid!")
            else:
                return failure_response("Token Expired! Please login", status=400)
        except Exception as eee:
            print(eee)
            return failure_response("Token Expired. Please Login Again!")

        body = request.get_json()
        new_event = Event()
        new_event.event_name = body["event_name"]
        new_event.description = body["description"]

        new_event.start_date = body["start_date"]
        new_event.end_date = body["end_date"]
        new_event.guest = body["guest"]
        new_event.audience_type = body["audience_type"]
        new_event.place_id = body["place_id"]

        start_date = datetime.strptime(new_event.start_date, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(new_event.end_date, "%Y-%m-%d %H:%M:%S")

        # compare dates
        event = session.query(Event).filter_by(place_id=new_event.place_id).all()
        if event is not None:
            for e in event:
                # check dates
                temp_start_date = datetime.strptime(str(e.start_date), "%Y-%m-%d %H:%M:%S")
                temp_end_date = datetime.strptime(str(e.end_date), "%Y-%m-%d %H:%M:%S")
                if temp_start_date <= start_date <= temp_end_date or temp_start_date <= end_date <= temp_end_date:
                    return failure_response("Dates Already Occupied!", 400)

        try:
            session.add(new_event)
            session.commit()
            return success_response(None, "Event Added Successfully", 200)

        except Exception as e:
            return failure_response(f"{e}", 500)
    except Exception as ee:
        print(ee)
        return failure_response(f"{ee}", 500)


@app.route('/admin/event', methods=['GET', 'POST'])
@token_check_admin
def admin_event():
    if request.method == 'GET':
        try:
            tag_var = request.args.get('id')
            if tag_var == 'all':
                result = session.query(Event).all()
                result_json = []
                for row in result:
                    result_json.append(row.to_json())
                return success_response(result_json, "Success", 200)
            else:
                result = session.query(Event).filter_by(id=tag_var).first()
                result_json = result.to_json()
                return success_response(result_json, "Success", 200)
        except Exception() as e:
            return failure_response(f"{e}", 400)
    if request.method == 'POST':
        tag_var = request.args.get('id')
        do = int(request.args.get('status'))
        if tag_var == 'all':
            result = session.query(Event).all()
            result_json = []
            for row in result:
                row.status = do
                row.modified_at = datetime.now()
                session.commit()
                result_json.append(row.to_json())
            return success_response(result_json, "Success", 200)
        else:
            result = session.query(Event).filter_by(id=tag_var).first()
            result.status = do
            result.modified_at = datetime.now()
            session.commit()
            result_json = result.to_json()
            return success_response(result_json, "Success", 200)


@app.route('/get_places', methods=['GET'])
def get_places():
    try:
        # Get the token from the request header
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
        current_time = datetime.now()
        if auth.created_at - current_time < dt.timedelta(hours=2):
            print("token valid!")
        else:
            return failure_response("Token Expired! Please login", status=400)

        # Retrieve the associated user
        user = auth.user
        if not user:
            return failure_response("User not Found!", status=404)

        results = session.query(Place).filter_by(status=1).all()
        places_json = [place.to_json() for place in results]
        return success_response(places_json, "done", 200)
    except Exception as e:
        print(e)
        return failure_response(f"{e}", 500)


@app.route('/admin/place', methods=['POST', 'GET', 'PUT'])
@token_check_admin
def admin_place():
    if request.method == 'POST':
        body = request.get_json()
        new_place = Place()
        new_place.place_name = body["place_name"]
        new_place.description = body["description"]
        new_place.audience_capacity = body["audience_capacity"]
        new_place.air_conditioner = body["air_conditioner"]
        new_place.projector = body["projector"]
        new_place.sound_system = body["sound_system"]
        new_place.latitude = body["latitude"]
        new_place.longitude = body["longitude"]

        try:
            session.add(new_place)
            check_place = session.query(Place).filter_by(place_name=new_place.place_name).first()
            if not check_place:
                session.commit()
            else:
                return failure_response("Place already Exists", 400)
            return success_response(None, "Success", 200)
        except Exception as ec:
            return failure_response(f"{ec}", 400)

    if request.method == 'PUT':
        id_var = request.args.get('id')
        change_var = request.args.get('change')
        value_var = request.args.get('value')

        result = session.query(Place).filter_by(id=id_var).first()
        query = text(f"UPDATE {Place.__tablename__} SET {change_var} = '{value_var}' WHERE id={id_var};")
        session.execute(query)
        result.modified_at = datetime.now()
        session.commit()
        print(result.place_name)
        return success_response(None, "Success", 200)

    if request.method == 'GET':
        id_var = request.args.get('id')
        if id_var == 'all':
            result = session.query(Place).all()
            result_json = []
            for row in result:
                result_json.append(row.to_json())
            return success_response(result_json, "Success", 200)
        else:
            result = session.query(Place).filter_by(id=id_var).first()
            result_json = result.to_json()
            return success_response(result_json, "Success", 200)


@app.route('/admin/updateStatus',methods=['PUT'])
def update_status():
    try:
        # Get the token from the request header
        bearer_token = request.headers.get('Authorization')
        if not bearer_token or not bearer_token.startswith('Bearer '):
            return failure_response("Invalid or missing Bearer token in the header!", status=400)

        # Check if the user has a valid token
        auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
        current_time = datetime.now()
        if auth.created_at - current_time < dt.timedelta(hours=2):
            print("token valid!")
        else:
            return failure_response("Token Expired! Please login", status=400)


        event_id = request.args.get('eventId', None, int)
        event_status = request.args.get('status', None, int)
        if event_status is None or event_status == 'undefined':
            return failure_response("Missing or 'undefined' status parameter", status=400)
        event = session.query(Event).filter_by(id=int(event_id)).one()
        event.status = event_status
        session.commit()
        return success_response()
    except Exception as eee:
        print(eee)
        return failure_response("Something Went Wrong!!")

if __name__ == '__main__':
    app.run()

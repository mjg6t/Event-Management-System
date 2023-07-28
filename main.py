import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Auth
from flask import Flask,jsonify, request
import database_properties as db


app = Flask(__name__)
engine = create_engine(db.get_db_uri())
# Bind the engine with the Base class
Base.metadata.bind = engine
# Create the tables in the database
Base.metadata.create_all(bind=engine)
# Create a session
Session = sessionmaker(bind=engine)
session = Session()


@app.route('/signup', methods=['POST'])
def save_user():
    try:
        # Get the request body
        body = request.get_json()
        # todo check email and password validity
        if body["email"] is not None and body["password"] is not None and body["name"] is not None:
            # todo encrypt password
            password = body["password"]
            # save user
            new_user = User()
            new_user.name = body["name"]
            new_user.email = body["email"]
            new_user.password = password
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
        user = session.query(User).filter_by(email=body["email"], password=body["password"]).first()
        if not user:
            return failure_response("User not Found!", status=404)
        # Update the existing Auth token
        if user.auth_token:
            user.auth_token.token = Auth.generate_token()
            session.commit()
            token = user.auth_token.token
        else:
            # If there's no token, create a new one and link it to the user
            auth = Auth()
            auth.user_id = user.id
            auth.generate_token()
            session.add(auth)
            session.commit()
            token = auth.token
        return success_response({'token': token}, message="Success!", status=200)
    except Exception as e:
        print(e)
        return failure_response("An Error Occurred", status=500)


@app.route('/event-listing', methods=['GET'])
def get_listing():
    # Get the token from the request header
    bearer_token = request.headers.get('Authorization')
    if not bearer_token or not bearer_token.startswith('Bearer '):
        return failure_response("Invalid or missing Bearer token in the header!", status=400)

    # Check if the user has a valid token
    auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
    current_time = datetime.datetime.now()
    if auth.created_at - current_time < datetime.timedelta(hours=2):
        print("token valid!")
    else:
        return failure_response("Token Expired! Please login", status=400)

    # Retrieve the associated user
    user = auth.user
    if not user:
        return failure_response("User not Found!", status=404)

    # get input parameters from endpoint
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    order_by = request.args.get('orderBy')

    # todo determine what exact columns would be fetched to show in listing & what input should be there
    # todo make a model for the entity events
    return success_response(None, "", status=200)


@app.route('/add_event', method= ['POST'])
def add_event():
    # Get the token from the request header
    bearer_token = request.headers.get('Authorization')
    if not bearer_token or not bearer_token.startswith('Bearer '):
        return failure_response("Invalid or missing Bearer token in the header!", status=400)

    # Check if the user has a valid token
    auth = session.query(Auth).filter_by(token=bearer_token.replace("Bearer ", "")).first()
    current_time = datetime.datetime.now()
    if auth.created_at - current_time < datetime.timedelta(hours=2):
        print("token valid!")
    else:
        return failure_response("Token Expired! Please login", status=400)
    # continue...
    

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


if __name__ == '__main__':
    app.run()

# todo project structure (multiple files)

# another commit


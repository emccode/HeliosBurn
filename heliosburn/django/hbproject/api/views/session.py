from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from api.models import db_model
from api.models.auth import RequireLogin
from sqlalchemy.exc import IntegrityError


@csrf_exempt
def rest(request, *pargs):
    """
    Calls python function corresponding with HTTP METHOD name. 
    Calls with incomplete arguments will return HTTP 400
    """
    if request.method == 'GET':
        rest_function = get
    elif request.method == 'POST':
        rest_function = post
    elif request.method == 'PUT':
        rest_function = put
    elif request.method == 'DELETE':
        rest_function = delete
    else:
        return JsonResponse({"error": "HTTP METHOD UNKNOWN"})

    try:
        return rest_function(request, *pargs)
    except TypeError:
            r = JsonResponse({"error": "argument mismatch"})
            r.status_code = 400
            return r


@RequireLogin
def get(request, session_id=None):
    """Retrieve a session."""
    if session_id is None:
        return get_all_sessions(request)
    dbsession = db_model.init_db()
    session = dbsession.query(db_model.Session).filter_by(id=session_id).first()
    if session is None:
        r = JsonResponse({"error": "session id '%s' not found" % session_id})
        r.status_code = 404
        return r
    else:
        session_dict = {
            'id': session.id,
            'name': session.name,
            'description': session.description,
            'testplan': session.testplan,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'started_at': session.started_at,
            'stopped_at': session.stopped_at,
            'user': {
                "username": session.user.username,
                "email": session.user.email,
                }
            }
        r = JsonResponse(session_dict)
        r.status_code = 200
        return r


def get_all_sessions(request):
    """Retrieves all sessions."""
    dbsession = db_model.init_db()
    all_sessions = dbsession.query(db_model.Session).all()
    session_list = list()
    for session in all_sessions:
        session_dict = {
            'id': session.id,
            'name': session.name,
            'description': session.description,
            'testplan': session.testplan,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'started_at': session.started_at,
            'stopped_at': session.stopped_at,
            'user': {
                "username": session.user.username,
                "email": session.user.email,
                }
            }
        session_list.append(session_dict)
    r = JsonResponse({"sessions": session_list})
    r.status_code = 200
    return r


@RequireLogin
def post(request):
    """Create a new session."""
    try:
        new = json.loads(request.body)
        assert "name" in new
        assert "user_id" in new
        assert "description" in new
    except AssertionError:
        r = JsonResponse({"error": "argument mismatch"})
        r.status_code = 400
        return r
    except ValueError:
        r = JsonResponse({"error": "invalid JSON"})
        r.status_code = 400
        return r

    dbsession = db_model.init_db()
    session = db_model.Session(name=new['name'], description=new['description'],  user_id=new['user_id'])

    # Add optional column values
    if "testplan_id" in new:
        session.testplan_id = new['testplan_id']

    dbsession.add(session)

    try:
        dbsession.commit()
    except IntegrityError as e:
        r = JsonResponse({"error": "%s" % e})
        r.status_code = 409
        return r
    r = JsonResponse({})
    r.status_code = 204
    return r


@RequireLogin
def put(request, session_id):
    """Update existing session."""
    try:
        new = json.loads(request.body)
    except ValueError:
        r = JsonResponse({"error": "invalid JSON"})
        r.status_code = 400
        return r

    dbsession = db_model.init_db()
    session = dbsession.query(db_model.Session).filter_by(id=session_id).first()
    if session is None:
        r = JsonResponse({})
        r.status_code = 404
        return r
    else:
        if "name" in new:
            session.name = new['name']
        if "description" in new:
            session.description = new['description']
        if "user_id" in new['user']:
            session.user_id = new['user_id']
        if "testplan_id" in new['user']:
            session.testplan_id = new['user_id']
        try:
            dbsession.commit()
        except IntegrityError as e:
            r = JsonResponse({"error": "%s" % e})
            r.status_code = 409
            return r
        r = JsonResponse({})
        r.status_code = 204
        return r


@RequireLogin
def delete(request, session_id):
    """Delete existing session."""
    dbsession = db_model.init_db()
    session = dbsession.query(db_model.Session).filter_by(id=session_id).first()
    if session is None:
        r = JsonResponse({"error": "session_id not found"})
        r.status_code = 404
        return r
    else:
        dbsession.delete(session)
        dbsession.commit()
        r = JsonResponse({})
        r.status_code = 204
        return r


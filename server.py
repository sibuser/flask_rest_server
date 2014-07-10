#!/usr/bin/python

from flask import Flask, abort
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from werkzeug.security import generate_password_hash
import lepl.apps.rfc3696
import pickle

import os

app = Flask(__name__, static_url_path="")
api = Api(app)

users = []

users_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String
}


def save_db(filename='users.db'):
    pickle.dump(users, open(filename, 'wb'))

def load_db(filename='users.db'):
    if os.path.isfile(filename):
        return pickle.load(open(filename, 'rb'))
    else:
        return []


class UserListApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('name', type=str, required=True,
                                   help='Name field can not be empty',
                                   location='json')
        self.reqparse.add_argument('email', type=str, required=True,
                                   help='Email field can not be empty',
                                   location='json')
        self.reqparse.add_argument('password', type=str, required=True,
                                   help='Password can not be empty',
                                   location='json')
        super(UserListApi, self).__init__()

    @staticmethod
    def generate_id():
        if len(users) == 0:
            return 1
        else:
            return users[-1]['id'] + 1

    @staticmethod
    def get():
        return map(lambda t: marshal(t, users_fields), users)

    def post(self):
        args = self.reqparse.parse_args()

        if len(args['password']) < 8:
            return {'error': 'Password should be at least 8 characters'}
        if args['name'] == '':
            return {'error': 'Name field can not be empty'}

        result = filter(lambda item: item['name'] == args['name'] or
                                     item['email'] == args['email'], users)
        if len(result) != 0:
            return {'error': 'Username or email exist'}

        email_validator = lepl.apps.rfc3696.Email()
        if not email_validator(args['email']):
            return {'error': 'Invalid email'}

        user = {
            'id': self.generate_id(),
            'name': args['name'],
            'email': args['email'],
            'password': generate_password_hash(args['password'])
        }
        users.append(user)
        return marshal(user, users_fields), 201


class UserApi(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True,
                                   help='Name field can not be empty',
                                   location='json')
        self.reqparse.add_argument('email', type=str, required=True,
                                   help='Email field can not be empty',
                                   location='json')
        super(UserApi, self).__init__()

    @staticmethod
    def get(user_id):
        user = filter(lambda item: item['id'] == user_id, users)
        if len(user) == 0:
            abort(404)
        return {'user': marshal(user[0], users_fields)}

    def put(self, user_id):
        user = filter(lambda item: item['id'] == user_id, users)
        if len(user) == 0:
            abort(404)
        user = user[0]
        args = self.reqparse.parse_args()

        for k, v in args.iteritems():
            if v != None and k != 'id' and k != 'password':
                user[k] = v
        return marshal(user, users_fields)

    @staticmethod
    def delete(user_id):
        user = filter(lambda item: item['id'] == user_id, users)
        if len(user) == 0:
            abort(404)
        users.remove(user[0])
        return {'result': True}


api.add_resource(UserListApi, '/users', endpoint='users')
api.add_resource(UserApi, '/user/<int:user_id>', endpoint='user')

if __name__ == '__main__':
    try:
        users = load_db()
        app.run(debug=True)
    finally:
        save_db()




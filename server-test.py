#!/usr/bin/env python

import server
import unittest
import json


class ServerTestCase(unittest.TestCase):
    def setUp(self):
        server.app.config['TESTING'] = True
        self.app = server.app.test_client()

    def tearDown(self):
        users = json.loads(self.app.get('/users').data)
        [self.delete_user(users[index]['id']) for index in range(len(users))]

    def add_user(self, username='test', email='test@mail.com', password='12345678'):
        data = dict(name=username, email=email, password=password)
        return self.app.post('/users', headers={'Content-Type': 'application/json'}, data=json.dumps(data))

    def update_user(self, user_id, params):
        return self.app.put('/user/{0}'.format(user_id), headers={'Content-Type': 'application/json'}, data=json.dumps(params))

    def delete_user(self, user_id):
        return self.app.delete('/user/{0}'.format(user_id), headers={'Content-Type': 'application/json'})

    def test_get_users(self):
        users = json.loads(self.app.get('/users').data)
        assert len(users) == 0

    def test_add_user(self):
        result = json.loads(self.add_user().data)
        assert result['name'] == 'test'
        assert result['email'] == 'test@mail.com'
        assert result['id'] == 1
        assert result.get('password', None) is None

    def test_not_possible_to_add_user_twice(self):
        json.loads(self.add_user().data)
        result = json.loads(self.add_user().data)
        assert 'Username or email exist' in result['error']

    def test_empty_name(self):
        result = json.loads(self.add_user('', 'test@mail.com', '12345678').data)
        assert result['error'] == 'Name field can not be empty'

    def test_short_password(self):
        result = json.loads(self.add_user('test', 'test@mail.com', '12345').data)
        assert result['error'] == 'Password should be at least 8 characters'

    def test_update_user(self):
        user = json.loads(self.add_user('test', 'test@mail.com', '123451235').data)
        result = json.loads(self.update_user(user['id'], dict(name='updated', id='2', email='updated@mail.com')).data)
        assert result['name'] == 'updated'
        assert result['email'] == 'updated@mail.com'
        assert result['id'] == 1

    def test_delete_user(self):
        users_before_add = json.loads(self.app.get('/users').data)
        json.loads(self.add_user().data)
        users_after_add = json.loads(self.app.get('/users').data)
        assert len(users_after_add) - len(users_before_add) == 1

        result = self.delete_user(users_after_add[0]['id'])
        assert json.loads(result.data)['result'] is True

        users_after_delete = json.loads(self.app.get('/users').data)
        assert len(users_after_delete) - len(users_before_add) == 0

    def test_delete_nonexisten_user(self):
        result = self.delete_user(1)
        assert 'Not Found.' in result.data

    def test_get_all_users(self):
        json.loads(self.add_user().data)
        json.loads(self.add_user('test2', 'test2@mail.com', '12345678').data)

        result = json.loads(self.app.get('/users').data)
        assert len(result) == 2

    def test_save_load_data(self):
        user = json.loads(self.add_user().data)
        server.save_db()
        self.delete_user(user['id'])
        server.users = server.load_db()
        users = json.loads(self.app.get('/users').data)
        assert len(users) == 1


if __name__ == '__main__':
    unittest.main()
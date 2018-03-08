# fillgroups
LDAP. Filling groups with users based on a given configuration

Configuration example (config.py):

```python
ldap = {
 'connection': {
  'hostname': 'host',
  'user_dn': 'cn=bind_user,ou=service,dc=company,dc=domain',
  'password': 'pass'
 },
 'users': {
 'base': 'ou=Users,dc=company,dc=domain',
 'scope': 1,
 'filter': '(&(objectClass=posixAccount)(|(uid=user*)))',
 'attributes': ['uid'],
 'attrsonly': 0
 },
 'groups': {
 'base': 'ou=Groups,dc=company,dc=domain',
 'scope': 1,
 'filter': '(objectClass=posixGroup)',
 'attributes': ['memberUid'],
 'attrsonly': 0
 }
}

groups = [
 { 'name': 'Group1',
   'limit': 10,
   'patterns':
    [ 'user11',
      'user12',
      'user13',
    ]
 },
 { 'name': 'Group2',
   'limit': 20,
   'patterns':
    [ 'user21',
      'user22',
    ]
 },
 { 'name': 'Users',
   'patterns':
   'limit': 100,
    [ 'user',
    ]
 },
]
```

Scope in "ldap" section can be one of:

* 0 (SCOPE_BASE) - to search the object itself
* 1 (SCOPE_ONELEVEL) - to search the object's immediate children
* 2 (SCOPE_SUBTREE) - to search the object and all its descendants


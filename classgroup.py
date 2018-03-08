#!/usr/bin/env python

class group:
 """
 bind_data looks like: ('cn=name,ou=ou,dc=company,dc=domain',\
 {'memberUid': ['user1', 'user2'], 'gidNumber': ['1']})
 """
 def __init__(self, conf_group, bind_data):
  self.dn = bind_data[0]
  if 'memberUid' in bind_data[1]:
   self.members = bind_data[1]['memberUid']
  else:
   self.members = []
  self.name = conf_group['name']
  self.count = len(self.members)
  self.limit = conf_group['limit']
  self.patterns = conf_group['patterns']
  self.appended = []

 def append(self, user):
  if self.count < self.limit:
   for pattern in self.patterns:
    if user['uid'].startswith(pattern):
     self.appended.append(user['uid'])
     self.count += 1
     return True
  return False

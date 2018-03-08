#!/usr/bin/env python

# TODO:
# - create groups if they don't exist

import ldap
import copy
import ldap.modlist as modlist
import config
import pickle
import classgroup

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# LDAP binding
#
def ldap_connection(hostname, username, password):
 url = "ldap://" + hostname
 ldap_connection = ldap.initialize(url)

 try:
  ldap_connection.protocol_version = ldap.VERSION3
  ldap_connection.simple_bind_s(username, password)
  return_value = ldap_connection

 except ldap.LDAPError, e:
  if type(e.message) == dict and e.message.has_key('desc'):
   emsg = e.message['desc']
  else:
   emsg = e
  print('LDAP connection failure: ' + str(emsg))
  exit(1)

 return return_value

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Getting list of users
#
def get_users(bind, settings):
 users = []
 result_id = bind.search(
  settings['base'],
  settings['scope'],
  settings['filter'],
  settings['attributes'],
  settings['attrsonly']
  )
 
 result_type, result_data = bind.result(result_id, 1)
 if result_data:
  for entry in result_data:
   users.append(
    { 'dn': entry[0],
      'uid': entry[1]['uid'][0]
    }
   )
 else:
  print('No configured users found in LDAP - imposible to continue')
  exit(1)

 return users

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Getting list of groups
#
def get_groups(bind, conf_groups, settings):
 glist = []
 for conf_group in conf_groups:
  search_filter = '(&' + settings['filter'] + '(cn=' + conf_group['name'] + '))'
  result_id = bind.search(
   settings['base'],
   settings['scope'],
   search_filter,
   settings['attributes'],
   settings['attrsonly']
   )
  bind_type, bind_data = bind.result(result_id, 1)
  if bind_data:
   glist.append(classgroup.group(conf_group, bind_data[0]))
  else:
   print('Group ' + conf_group['name'] + ' was not found in LDAP - skipping')

 if glist:
  return glist
 else:
  print('No configured groups found in LDAP - imposible to continue')
  exit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Getting groups that are (not) capable of filling
#
def groups_analysis(groups):
 filled_groups = []
 capable_groups = []
 for group in groups:
  if group.count < group.limit:
   capable_groups.append(group)
  else:
   filled_groups.append(group)
 return filled_groups, capable_groups

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Getting users that are not found in groups + multigroup users
#
def users_analysis(users, groups):
 unassigned_users = []
 multigroup_users = []
 for user in users:
  group_list = []
  for group in groups:
   if user['uid'] in group.members:
    group_list.append(group.name)
  if group_list:
   if len(group_list) > 1:
    user['groups'] = group_list
    multigroup_users.append(user)
  else:
   unassigned_users.append(user)
 return unassigned_users, multigroup_users

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Assign users to capable groups
#
def capable_assign(users, groups):
 failed_users = []
 for user in users:
  failed_user = True
  for group in groups:
   if group.append(user):
    #print(user['uid'] + group.name)
    failed_user = False
    break
   else:
    continue
  if failed_user:
   failed_users.append(user)

 return failed_users

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Updating LDAP groups
#
def update_groups(bind, groups):
 updated_groups = []
 for group in groups:
  if group.appended:
   ldif = ldap.modlist.modifyModlist({'memberUid': ''}, {'memberUid': group.appended})
   bind.modify_s(group.dn, ldif)
   updated_groups.append(group)

 return updated_groups

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Main
#

bind = ldap_connection(
 config.ldap['connection']['hostname'],
 config.ldap['connection']['user_dn'],
 config.ldap['connection']['password']
 )

groups = get_groups(bind, config.groups, config.ldap['groups'])
#pickle.dump(groups, open( "groups.pic", "wb" ) )
users = get_users(bind, config.ldap['users'])
#pickle.dump(users, open( "users.pic", "wb" ) )

#users = pickle.load(open( "users.pic", "rb" ))
print('Input users: ' + str(len(users)))
#groups = pickle.load(open( "groups.pic", "rb" ))
print('Input groups: ' + str(len(groups)))
unassigned_users, multigroup_users = users_analysis(users, groups)
print('Unassigned users: ' + str(len(unassigned_users)))
print('Multigroup users: ' + str(len(multigroup_users)))
filled_groups, capable_groups = groups_analysis(groups)
print('Capable groups: ' + str(len(capable_groups)))

if multigroup_users:
 print('There are users with more than one group membership:')
 for user in multigroup_users:
  print(' ' + user['uid'] + ': ' + str(user['groups']))

if filled_groups:
 print('Some groups have no room for appending users:')
 for group in filled_groups:
  print(' ' + group.name + ': ' + str(group.count) + ' with limit ' + str(group.limit))

if not unassigned_users:
 print('No unassigned users found')
 exit(0)

if capable_groups:
 failed_users = capable_assign(unassigned_users, capable_groups)
else:
 print('No capable groups found')
 exit(1)

if failed_users:
 print('There are no groups for assigning these users:')
 for user in failed_users:
  print(user['uid'])

updated_groups = update_groups(bind, capable_groups)

if updated_groups:
 for group in updated_groups:
  print('Group ' + group.name + ' is supposed to be updated with ' + str(len(group.appended)) + ' users and have ' + str(group.count) + ' members with limit ' + str(group.limit))
 print('Check your groups and rerun the script if some groups remain unchanged.')

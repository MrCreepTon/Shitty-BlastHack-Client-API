import bh

account = bh.Account('USERNAME', 'PASSWORD')
if account.authorize():
    print('Success login! Getting last posts in your profile...')
    messages = account.getMessagesInProfile(account.id)
    for message in messages:
        print('\nMessage ID: {0}\nFrom: {1}\nText: {2}\nUnformatted text: {3}'.format(message.userId, message.nickname, message.message, message.fullMessage))
else:
    print('Invalid login data!')
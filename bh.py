import requests
import bs4
from requests.exceptions import RequestException
from requests.sessions import session
import json
import re
import traceback

class Error(Exception):
    """Base class for other exceptions"""
    pass

class ParseTokenError(Error):
    """Token can`t be parsed"""
    pass

class ProfileInfo:
    def __init__(self):
        self.receive_admin_email = ''
        self.activity_summary_email = ''
        self.show_dob_date = ''
        self.custom_title = ''
        self.location = ''
        self.website = ''
        self.about = ''
        self.occupation = ''
        self.gender = ''
        self.vk = ''
        self.telegram = ''
        self.skype = ''
        self.discord = ''
        self.icq = ''
        self.instagram = ''
        self.youtube = ''
        self.facebook = ''
        self.twitter = ''

class Comment:
    def __init__(self, userId, nickname, message, fullMessage, commentId):
        self.commentId = commentId
        self.userId = userId
        self.nickname = nickname
        self.message = message
        self.fullMessage = fullMessage

class ProfileMessage:
    def __init__(self, userId: int, nickname: str, message: str, fullMessage, comments, messageId):
        self.messageId = messageId
        self.userId = userId
        self.nickname = nickname
        self.message = message
        self.comments = comments
        self.fullMessage = fullMessage

class ThreadMessage:
    def __init__(self, userId: int, nickname: str, message: str, fullMessage, messageId):
        self.messageId = messageId
        self.userId = userId
        self.nickname = nickname
        self.message = message
        self.fullMessage = fullMessage

class Account:
    def updateToken(self):
        self.client.get('https://blast.hk/')
        r = self.client.get('https://www.blast.hk/')
        html = r.text
        soup = bs4.BeautifulSoup(html, 'html.parser')
        self.token = soup.find('input', {'name': '_xfToken'})
        if self.token == None:
            raise ParseTokenError
        else:
            self.token = self.token['value']

    def __init__(self, login: str, password: str):
        try:
            self.login = login
            self.password = password
            self.id = 0
            self.client = requests.session()
            self.updateToken()
            #print(self.token)
        except requests.RequestException:
            traceback.print_exc()
            pass

    def twoFactorAuthorize(self, code):
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/login/two-step', data = {
                'code': code,
                'trust': '1',
                'confirm': '1',
                'provider': 'totp',
                'remember': '1',
                '_xfRedirect': 'https://www.blast.hk/',
                '_xfToken': self.token,
                '_xfRequestUri': '/login/two-step?_xfRedirect=https%3A%2F%2Fwww.blast.hk%2F&remember=1',
                '_xfWithData': '1',
                '_xfResponseType': 'json'
            })
            data = json.loads(r.text)
            return data['status'] == 'ok'
        except requests.RequestException:
            traceback.print_exc()
            pass
        
    def authorize(self):
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/login/login', data = {
                'login': self.login,
                'password': self.password,
                'remember': 1,
                '_xfRedirect': 'https://www.blast.hk/',
                '_xfToken': self.token
            })
            if r.text.find('Некорректный пароль') == -1:
                if r.url.find('two-step') != -1:
                    try:
                        while True:
                            if self.twoFactorAuthorize(input('Enter 2auth code: ')):
                                break
                            else:
                                print('Invalid code!')
                    except KeyboardInterrupt:
                        return False
                self.id = self.client.cookies.get_dict()['xf_user'].split('%')[0]
                return True
            else:
                return False
        except requests.RequestException:
            traceback.print_exc()
            pass

    def getUserAvatarLink(self, userId):
        try:
            self.updateToken()
            r = self.client.get('https://www.blast.hk/members/{0}/'.format(userId))
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            avatars = soup.find('span', {'class': 'avatarWrapper'}).findAll('a')
            if avatars == None:
                return None
            else:
                for avatar in avatars:
                    link = avatar.get('href')
                    if link.find('.jpg') != -1 or link.find('.png') != -1:
                        #print(link)
                        return 'https://www.blast.hk{0}'.format(link)
                return None
        except requests.RequestException:
            traceback.print_exc()
            pass

    def changeBanner(self, imageData):
        file_dict = {'upload': ('photo.png', imageData)}
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/account/banner', data = {
                'banner_position_y': '50',
                '_xfToken': self.token,
                '_xfRequestUri': '/members/{0}/'.format(self.id),
                '_xfWithData': '1',
                '_xfResponseType': 'json'
            },
            files = file_dict)
            data = json.loads(r.text)
            #print(data)
            return not ('status' in data)
        except requests.RequestException:
            traceback.print_exc()
            pass

    def isLoggedIn(self):
        try:
            self.updateToken()
            r = self.client.get('https://www.blast.hk/')
            return r.text.find('p-navgroup-link p-navgroup-link--textual p-navgroup-link--logIn') == -1
        except requests.RequestException:
            traceback.print_exc()
            pass

    def getMessagesInThread(self, thread: int):
        try:
            self.updateToken()
            cMessages = []
            r = self.client.get('https://www.blast.hk/threads/{0}/'.format(thread))
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            messages = soup.find_all('div', {'class': 'message-inner'})
            for message in messages:
                nickname = message.find('h4')
                if nickname != None:
                    messageId = message.find('div', {'class': 'message-userContent lbContainer js-lbContainer'})['data-lb-id'].split('-')
                    messageId = int(messageId[len(messageId) - 1])
                    nickname = nickname.text.replace('\n', '').replace('\t', '').replace('\r', '')
                    userId = int(message.find('a', {'class': 'username'})['data-user-id'])
                    text = message.find('div', {'class': 'bbWrapper'})
                    msg = str(text)
                    if msg.rfind('</blockquote>') != -1:
                        text = msg[msg.rfind('</blockquote>') + len('</blockquote>'):len(msg)]
                    else:
                        text = text.text
                    cMessages.append(ThreadMessage(userId, nickname, text, msg, messageId))
            return cMessages
        except requests.RequestException:
            traceback.print_exc()
            pass

    def getLastThreads(self):
        try:
            self.updateToken()
            r = self.client.get('https://www.blast.hk/')
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            tab = soup.find('div', {'data-group-id': 'second'})
            threads = []
            regex = re.compile('structItem structItem--row.*')
            items = tab.findAll('div', {'class': regex})
            for item in items:
                link = item.find('div', {'class': 'structItem-cell structItem-cell--main'}).find('a').get('href')
                threads.append('https://www.blast.hk{0}'.format(link))
            return threads
        except requests.RequestException:
            traceback.print_exc()
            pass

    def getLastUnreadThreads(self):
        try:
            self.updateToken()
            r = self.client.get('https://www.blast.hk/')
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            tab = soup.find('div', {'data-group-id': 'second'})
            threads = []
            regex = re.compile('structItem structItem--row.*')
            items = tab.findAll('div', {'class': regex})
            for item in items:
                if 'is-unread' in item.get('class'):
                    link = item.find('div', {'class': 'structItem-cell structItem-cell--main'}).find('a').get('href')
                    threads.append('https://www.blast.hk{0}'.format(link))
            return threads
        except requests.RequestException:
            traceback.print_exc()
            pass

    def getMessagesInProfile(self, profileId: int):
        try:
            self.updateToken()
            cMessages = []
            r = self.client.get('https://www.blast.hk/members/{0}/'.format(profileId))
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            messages = soup.find_all('div', {'class': 'message-inner'})
            for message in messages:
                cComments = []
                nickname = message.find('h4')
                if nickname != None and message.find('div', {'class': 'messageNotice messageNotice--deleted'}) == None:
                    #print(message)
                    messageId = message.find('div', {'class': 'lbContainer js-lbContainer'})['data-lb-id'].split('-')
                    messageId = int(messageId[len(messageId) - 1])
                    nickname = nickname.text.replace('\n', '').replace('\t', '').replace('\r', '')
                    userId = int(message.find('a', {'class': 'username'})['data-user-id'])
                    text = message.find('div', {'class': 'bbWrapper'})
                    msg = str(text)
                    if msg.rfind('</blockquote>') != -1:
                        text = msg[msg.rfind('</blockquote>') + len('</blockquote>'):len(msg)]
                    else:
                        text = text.text
                    comments = message.findAll(lambda tag: tag.name == 'div' and tag.get('class') == ['message-responseRow'])
                    for comment in comments:
                        #print('HERE: ' + str(comment))
                        cComment = Comment(0, '', '', '', 0)
                        cComment.nickname = comment.find('div', {'class': 'comment'}).get('data-author')
                        cComment.commentId = comment.find('div', {'class': 'comment'}).get('data-content').split('-')
                        cComment.commentId = int(cComment.commentId[len(cComment.commentId) - 1])
                        cComment.userId = int(comment.find('a', {'class': 'username comment-user'}).get('data-user-id'))
                        cComment.message = comment.find('div', {'class': 'bbWrapper'})
                        cMsg = str(cComment.message)
                        if cMsg.rfind('</blockquote>') != -1:
                            cComment.message = cMsg[cMsg.rfind('</blockquote>') + len('</blockquote>'):len(cMsg)]
                        else:
                            cComment.message = cComment.message.text
                        cComment.fullMessage = cMsg
                        cComments.append(cComment)
                    cMessages.append(ProfileMessage(userId, nickname, text, msg, cComments, messageId))
            return cMessages
        except requests.RequestException:
            traceback.print_exc()
            pass

    def sendMessageInThread(self, thread: int, message: str):
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/threads/{0}/add-reply'.format(thread), data = {
                'message_html': message,
                '_xfToken': self.token,
                '_xfWithData': 1,
                '_xfResponseType': 'json'
            })
        except requests.RequestException:
            traceback.print_exc()
            pass

    def sendMessageInProfile(self, profileId: int, message: str):
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/members/{0}/post'.format(profileId), data = {
                'message_html': message,
                '_xfToken': self.token,
                '_xfWithData': 1,
                '_xfResponseType': 'json'
            })
        except requests.RequestException:
            traceback.print_exc()
            pass

    def editMessageInProfile(self, postId: int, profileId: int, message: str):
        try:
            self.updateToken()
            r = self.client.post('https://www.blast.hk/profile-posts/{0}/edit'.format(postId), data = {
                'message_html': message,
                '_xfInlineEdit': 1,
                '_xfToken': self.token,
                '_xfRequestUri': '/members/{0}/'.format(profileId),
                '_xfWithData': 1,
                '_xfToken': self.token,
                '_xfResponseType': 'json'
            })
        except requests.RequestException as e:
            traceback.print_exception(e)
            pass

    def getProfileInfo(self):
        try:
            self.updateToken()
            profileInfo = ProfileInfo()
            r = self.client.get('https://www.blast.hk/account/account-details')
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            profileInfo.receive_admin_email = soup.find('input', {'name': 'option[receive_admin_email]'}).get('value')
            profileInfo.activity_summary_email = soup.find('input', {'name': 'enable_activity_summary_email'}).get('value')
            profileInfo.show_dob_date = soup.find('input', {'name': 'option[show_dob_date]'}).get('value')
            try:
                profileInfo.custom_title = soup.find('input', {'name': 'user[custom_title]'}).get('value')
            except Exception:
                profileInfo.custom_title = ''
            profileInfo.location = soup.find('input', {'name': 'profile[location]'}).get('value')
            profileInfo.website = soup.find('input', {'name': 'profile[website]'}).get('value')
            profileInfo.about = soup.find('textarea', {'name': 'about_html'}).contents
            profileInfo.gender = soup.find('dl', {'data-field': 'gender'}).find('input', {'checked': 'checked'}).get('value')
            profileInfo.vk = soup.find('input', {'name': 'custom_fields[vkontakte]'}).get('value')
            profileInfo.telegram = soup.find('input', {'name': 'custom_fields[telegram]'}).get('value')
            profileInfo.occupation = soup.find('input', {'name': 'custom_fields[occupation]'}).get('value')
            profileInfo.skype = soup.find('input', {'name': 'custom_fields[skype]'}).get('value')
            profileInfo.youtube = soup.find('input', {'name': 'custom_fields[youtube]'}).get('value')
            profileInfo.discord = soup.find('input', {'name': 'custom_fields[discord]'}).get('value')
            profileInfo.facebook = soup.find('input', {'name': 'custom_fields[facebook]'}).get('value')
            profileInfo.icq = soup.find('input', {'name': 'custom_fields[icq]'}).get('value')
            profileInfo.twitter= soup.find('input', {'name': 'custom_fields[twitter]'}).get('value')
            profileInfo.instagram = soup.find('input', {'name': 'custom_fields[instagram]'}).get('value')
            return profileInfo
        except requests.RequestException as e:
            traceback.print_exception(e)
            return None

    def changeCustomTitle(self, title):
        try:
            self.updateToken()
            info = self.getProfileInfo()
            r = self.client.post('https://www.blast.hk/account/account-details', data = {
            'option[receive_admin_email]': info.receive_admin_email,
            'enable_activity_summary_email': info.activity_summary_email,
            'option[show_dob_date]': info.show_dob_date,
            'user[custom_title]': title,
            'profile[location]': info.location,
            'profile[website]': info.website,
            'html_about': info.about,
            'custom_fields[gender]': info.gender,
            'custom_fields[occupation]': info.occupation,
            'custom_fields[vkontakte]': info.vk,
            'custom_fields[telegram]': info.telegram,
            'custom_fields[skype]': info.skype,
            'custom_fields[youtube]': info.youtube,
            'custom_fields[discord]': info.discord,
            'custom_fields[facebook]': info.facebook,
            'custom_fields[icq]': info.icq,
            'custom_fields[twitter]': info.twitter,
            'custom_fields[instagram]': info.instagram,
            '_xfToken': self.token,
            '_xfRequestUri': '/account/account-details',
            '_xfWithData': 1,
            '_xfToken': self.token,
            '_xfResponseType': 'json'
            })
            #print(r.text)
        except requests.RequestException as e:
            traceback.print_exception(e)
            pass

    def getMessagesInThreadOnLastPage(self, thread: int):
        try:
            self.updateToken()
            cMessages = []
            r = self.client.get('https://www.blast.hk/threads/{0}/'.format(thread))
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            lastPage = 1
            try:
                lastPage = soup.find('div', {'class': 'inputGroup inputGroup--numbers'}).find('input')['max']
            except AttributeError:
                pass
            r = self.client.get('https://www.blast.hk/threads/{0}/page-{1}'.format(thread, lastPage))
            html = r.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            messages = soup.find_all('div', {'class': 'message-inner'})
            for message in messages:
                nickname = message.find('h4')
                if nickname != None:
                    messageId = message.find('div', {'class': 'message-userContent lbContainer js-lbContainer'})['data-lb-id'].split('-')
                    messageId = int(messageId[len(messageId) - 1])
                    nickname = nickname.text.replace('\n', '').replace('\t', '').replace('\r', '')
                    userId = int(message.find('a', {'class': 'username'})['data-user-id'])
                    text = message.find('div', {'class': 'bbWrapper'})
                    msg = str(text)
                    if msg.rfind('</blockquote>') != -1:
                        text = msg[msg.rfind('</blockquote>') + len('</blockquote>'):len(msg)]
                    else:
                        text = text.text
                    cMessages.append(ThreadMessage(userId, nickname, text, msg, messageId))
            return cMessages
        except requests.RequestException:
            traceback.print_exc()
            pass


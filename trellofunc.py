import json
import sys

try:
    from urllib import urlencode
    from urllib2 import HTTPError, Request, urlopen
except ImportError:
    from urllib.error import HTTPError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

# a mapping of Trello colors to their hex codes
COLORS = {'green': '#70b500', 'yellow': '#f2d600', 'orange': '#ff9f1a',
    'red': '#eb5a46', 'purple': '#c377e0', 'blue': '#0079bf', 'sky': '#00c2e0',
    'lime': '#51e898', 'pink': '#ff78cb', 'black': '#4d4d4d', 'default': '#b6bbbf'}


# API example: https://github.com/sarumont/py-trello/blob/master/trello/__init__.py
class Trello(object):

    # initialize object
    def __init__(self, api_key, oauth_token, board_id):
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.board_id = board_id
        self.base_url = 'https://api.trello.com/1'

    # get all the lists from a Trello board
    def getLists(self):
        return self.makeRequest('GET', '/boards/' + self.board_id + '/lists')

    # get a certain list from a Trello board
    def getList(self, list_id):
        return self.makeRequest('GET', '/lists/' + list_id)

    # find a certain list from a Trello board by name
    def findList(self, name):
        tlist = None
        lists = self.getLists()
        for l in lists:
            if l['name'] == name:
                tlist = l
                break
        return tlist

    # create a new list, with the list id of the one next to it for positioning
    def createList(self, name, list_id):
        new_list = self.findList(name)
        if not new_list:
            # NOTE that because of Trello's weird positioning mechanics
            #      this may not always put the new list just to the right of the old one, but it'll be close
            done_list = self.getList(list_id)
            params = {'name': name, 'pos': done_list['pos'] + 1}
            new_list = self.makeRequest('POST', '/boards/' + self.board_id + '/lists', params=params)
        return new_list

    # Get a card from a list on a Trello board
    def getCard(self, card_id):
        return self.makeRequest('GET', '/boards/' + self.board_id + '/cards/' + card_id)

    # create a card under a certain list on a Trello board
    def createCard(self, list_id, name, pos="top"):
        params = {'name': name, 'idList' : list_id, 'pos': pos}
        return self.makeRequest('POST', '/cards/', params=params)

    # get Actions from a card
    def getActions(self, card):
        return self.makeRequest('GET', '/cards/' + card['id'] + '/actions')

    # get comments from a card
    def getComments(self, card):
        actions = self.getActions(card)
        return [action for action in actions if action['type'] == 'commentCard']

    # add a comment to a card
    def addComment(self, card, comment):
        params = {'text': comment}
        return self.makeRequest('POST', '/cards/' + card['id'] + '/actions/comments', params=params)

    # delete all comments from a card
    def deleteComments(self, comments):
        for comment in comments:
            card_id = comment['data']['card']['id']
            action_id = comment['id']
            self.makeRequest('DELETE', '/cards/' + card_id + '/actions/' + action_id + '/comments')

    # get all the cards from a list
    def getCards(self, list_id):
        return self.makeRequest('GET', '/lists/' + list_id + '/cards')

    # move a card
    def moveCard(self, card, list_id, pos=None):
        params = {'idList': list_id}
        if pos:
            params['pos'] = pos
        self.makeRequest('PUT', '/cards/' + card['id'], params=params)
        return card

    # move cards from a list to another list
    def moveCards(self, from_list_id, to_list_id):
        cards = self.getCards(from_list_id)
        for card in cards:
            self.moveCard(card, to_list_id, pos=card['pos'])
        return cards

    # construct the request to be sent to the API
    def makeRequest(self, method, path, params=None):
        if not params:
            params = {}
        params['key'] = self.api_key
        params['token'] = self.oauth_token

        url = self.base_url + path
        data = None

        if method == 'GET':
            url += '?' + urlencode(params)
        elif method in ['DELETE', 'POST', 'PUT']:
            data = urlencode(params).encode('utf-8')

        request = Request(url)
        if method in ['DELETE', 'PUT']:
            request.get_method = lambda: method

        try:
            if data:
                response = urlopen(request, data=data)
            else:
                response = urlopen(request)
        except HTTPError as e:
            print(e)
            print(e.read())
            result = None
        else:
            result = json.loads(response.read().decode('utf-8'))

        return result


if __name__ == '__main__':
    # if none of the functions are being used, run this for demonstration
    if len(sys.argv) != 5:
        print('Wrong number of arguments. Need api_key, oauth_token, board_id and list_name.')
        sys.exit()
    filename, api_key, oauth_token, board_id, list_name = sys.argv
    client = Trello(api_key, oauth_token, board_id)

    # find the list ID given the name of a list
    tlist = client.findList(list_name)
    if tlist:
        print('List ID: ' + tlist['id'])
    else:
        print('List not found.')

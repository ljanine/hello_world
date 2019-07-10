# encoding: utf-8
import webapp2
import json
import logging
from google.appengine.api import urlfetch
from bot import Bot
import yaml
from user_events import UserEventsDao

VERIFY_TOKEN = "facebook_verification_token"
ACCESS_TOKEN = "EAAML8Q9ysHkBAAEfkXI2uItQteK8eyY2VGqKRWC5QnAJ5NSqvnytseXhSY9gOBM2HNz3QSgOMaCweJDpBqDjSFCq2FWn3kRl27FAgq361k2RnsD1fTFvGI943RKSS30RQxFXzfeqTSx1TKWu1PliM4pxDyZC5aLtNZBu0ZBDgZDZD"

class MainPage(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        super(MainPage, self).__init__(request,response)
        logging.info("Instanciando bot")
        tree = yaml.load(open('tree.yaml'))
        logging.info("Tree: %r", tree)
        self.bot = Bot(send_message, UserEventsDao(), tree)
        #dao = UserEventsDao()
        #dao.add_user_event("222","user","ppppp")
        #dao.add_user_event("123","bot","def")
        #dao.add_user_event("123","user","ahi")
        #dao.add_user_event("123","bot","mec")
        #dao.add_user_event("123","user","menñ")
        #data = dao.get_user_events("123")
        #logging.info("eventos %r", data)
        #dao.remove_user_events("222")
        
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        mode = self.request.get("hub.mode")
        if mode == "subscribe":
            challenge = self.request.get("hub.challenge")
            verify_token = self.request.get("hub.verify_token")
            if verify_token == VERIFY_TOKEN:
                self.response.write(challenge)
        else:
            self.response.write("Ok")
           # self.bot.handle(0,"message_text")

    def post(self):
        data = json.loads(self.request.body)
        logging.info("Data obtenida desde Messenger: %r", data)

        if data["object"] == "page":

            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    
                    if messaging_event.get("message"):
                        is_admin = False
                        message = messaging_event['message']
                        if message.get('is_echo'):
                            if message.get('app_id'): #bot
                                continue
                            else: #admin
                                #desactivar el bot
                                is_admin = True
                                

                        message_text = message.get('text', '')
                        logging.info("Mensaje obtenido: %s", message_text)
                        
                        #bot handle
                        if is_admin:
                            user_id = recipient_id
                        else:
                            user_id = sender_id
                        self.bot.handle(user_id, message_text, is_admin)                        

                    if messaging_event.get("postback"):
                        message_text = messaging_event['postback']['payload']
                        #bot handle
                        self.bot.handle(sender_id, message_text)
                        logging.info("Post-back obtenido %s", message_text)



def send_message(recipient_id, message_text, possible_answers):
    
    headers = {
        "Content-Type":"application/json"
    }
    
    #maxima cantidad de botones: 3
    #maxima cantidad de caracteres recomendado: 20

    message = get_postback_buttons_message(message_text, possible_answers)
    if message is None:
        message = {"text": message_text}

    raw_data = {
        "recipient": {
            "id": recipient_id
        },
        "message": message
    }
    data = json.dumps(raw_data)

    logging.info("Enviando mensaje a %r: %s", recipient_id, message_text)
    
    r = urlfetch.fetch("https://graph.facebook.com/v2.6/me/messages?access_token=%s" % ACCESS_TOKEN, 
                        method=urlfetch.POST,headers=headers, payload=data)
    if r.status_code != 200:
        logging.error("Error %r enviando mensaje: %s", r.status_code, r.content)

def get_postback_buttons_message(message_text, possible_answers):
    if possible_answers is None or len(possible_answers) > 3:
        return None

    buttons= []
    for answer in possible_answers:
        buttons.append({
            "type": "postback",
            "title": answer,
            "payload": answer
        })

    return {
            "attachment":{
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": message_text,
                    "buttons": buttons
                }
            }

    }


class PrivacyPolicyPage(webapp2.RequestHandler):  
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        htmlContent = open('privacy_policy.html').read()
        self.response.write(htmlContent)
        



app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/privacy-policy', PrivacyPolicyPage),
], debug=True)

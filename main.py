from dialog_bot_sdk.bot import DialogBot
from dialog_bot_sdk import interactive_media
from pymongo import MongoClient
import grpc
import time

# Utils
client = MongoClient(
    "mongodb://team:123ert@ds018839.mlab.com:18839/new_hackaton", retryWrites=False
)
db = client.new_hackaton
reviews = db.reviews
guides = db.guides
bot_token = "fc1595f3591f137461a1ad6441062e083fd366a1"
tokens = db.tokens
peers = db.peers
cost = db.cost
# https://github.com/dialogs/chatbot-hackathon - basic things
# https://hackathon.transmit.im/web/#/im/u2108492517 - bot

def auth(id, peer, *params):
    if is_exist(id):
        getting_leftover(peer,id)
    else:
        # TODO WORK WITH TOKEN
        create_company(peer,id)

def is_exist(id):
    return False if cost.find_one({"id": id}) is None else True



def start_text(peer):
    bot.messaging.send_message(
        peer, "This is start message, you can use /info to get details!"
    )
def getting_leftover(peer,id):
    res = cost.find_one({"id": id})["leftover"]
    bot.messaging.send_message(
        peer, "На вашем счету осталось " + res
    )

def info_text(peer):
    bot.messaging.send_message(peer, "This is info message")

def create_company(peer,id):
    bot.messaging.send_message(peer, "Введите название компании")
    def waiting_of_creating_company(*params):
        company_name = params[0].message.textMessage.text
        bot.messaging.send_message(peer, "Пожалуйста введите количество денег на счету")
        def getting_current_leftover(*params):
            cost.insert_one({"leftover": params[0].message.textMessage.text, "company": company_name, "id": id})
            main(*params)
            bot.messaging.on_message(main, on_click)
        bot.messaging.on_message(getting_current_leftover)
    bot.messaging.on_message(waiting_of_creating_company)

# Main fun
def main(*params):
    id = params[0].peer.id
    peer = params[0].peer
    if params[0].message.textMessage.text == "/info":
        info_text(peer)
        return
    if params[0].message.textMessage.text == "/start":
        start_text(peer)
        return
    if params[0].message.textMessage.text == "Остаток":
        getting_leftover(peer,id)
        return
    auth(id,peer,params)
    bot.messaging.send_message(peer, "Hey")



def on_click(*params):
    id = params[0].uid
    value = params[0].value
    peer = bot.users.get_user_peer_by_id(id)



if __name__ == "__main__":
    bot = DialogBot.get_secure_bot(
        "hackathon-mob.transmit.im",  # bot endpoint (specify different endpoint if you want to connect to your on-premise environment)
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        bot_token,  # bot token Nikita , Nikita 2 - "d3bdd8ab024c03560ecf3350bcc3c250a0bbe9cd",
        verbose=False,  # optional parameter, when it's True bot prints info about the called methods, False by default
    )

# work like return , block code after, if want to use code after, use async vers
bot.messaging.on_message(main, on_click)

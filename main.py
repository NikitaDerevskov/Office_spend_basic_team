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

# https://github.com/dialogs/chatbot-hackathon - basic things
# https://hackathon.transmit.im/web/#/im/u2108492517 - bot


def add_user_to_admins(id):
    reviews.insert_one({"type": "Office-manager", "id": id})


def is_exist(id):
    return False if reviews.find_one({"id": id}) is None else True


def is_manager(id):
    return True if reviews.find_one({"id": id})["type"] == "Office-manager" else False


def on_msg(msg, peer):
    bot.messaging.send_message(peer, msg)


def add_user_to_users(id):
    reviews.insert_one({"type": "User", "id": id})


def has_token(id, *params):
    message = params[0].message.textMessage.text
    if message == "hello":
        return whose_token(message, id, params[0].peer)
    else:
        return want_to_create(*params)


def whose_token(text_token, id, peer):
    token_type = tokens.find_one({"token": text_token})

    if token_type is None:
        return on_msg("Братан, ты опоздал", peer)
    #if token_type["Type"] == "Office-manager":
        #on_msg("Ты одмен", peer)
        #return add_user_to_admins(id)
    #else:
        #on_msg("Ты юзер", peer)
        #return add_user_to_users(id)


def want_to_create(*params):
    bot.messaging.send_message(
        params[0].peer,
        "Создай компанию, плз",
        [
            interactive_media.InteractiveMediaGroup(
                [
                    interactive_media.InteractiveMedia(
                        1, interactive_media.InteractiveMediaButton("create_company", "Давай")
                    ),
                    interactive_media.InteractiveMedia(
                        1, interactive_media.InteractiveMediaButton("Test", "Не давай")
                    ),
                ]
            )
        ],
    )


# TODO
def send_manager_buttons(id, peer):
    bot.messaging.send_message(peer, "Sending manager buttons")

    buttons = [
        interactive_media.InteractiveMediaGroup(
            [
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton("add_guide", "Add guide"),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton("get_token", "Get token"),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "get_guides", "Give me guides"
                    ),
                ),
            ]
        )
    ]

    bot.messaging.send_message(peer, "Choose option", buttons)


# TODO
def send_guides(id, peer):
    bot.messaging.send_message(peer, "Sending guides")

    buttons = [
        interactive_media.InteractiveMediaGroup(
            [
                interactive_media.InteractiveMedia(
                    2,
                    interactive_media.InteractiveMediaButton(
                        "kitchen", "Guide about kitchen"
                    ),
                ),
                interactive_media.InteractiveMedia(
                    3,
                    interactive_media.InteractiveMediaButton(
                        "wifi", "Guide about wifi"
                    ),
                ),
            ]
        )
    ]

    bot.messaging.send_message(peer, "Choose guide", buttons)


def auth(id, peer, *params):
    if is_exist(id):
        send_manager_buttons(id, peer) if is_manager(id) else send_guides(id, peer)
    else:
        # TODO WORK WITH TOKEN
        has_token(id, *params)


def start_text(peer):
    bot.messaging.send_message(
        peer, "This is start message, you can use /info to get details!"
    )


def info_text(peer):
    bot.messaging.send_message(peer, "This is info message")


# Main fun
def main(*params):
    id = params[0].peer.id
    peer = params[0].peer
    if params[0].message.textMessage.text == "/info":
        info_text(peer)
        return

    bot.messaging.send_message(peer, "Hey")

    if params[0].message.textMessage.text == "/start":
        start_text(peer)
        return


    #time.sleep(2)  # for better usage
    auth(id, peer, *params)
    # user = bot.users.get_user_by_id(id)
    # on_msg("Hello user " + user.data.name, params[0].peer)
    #
    # return
def render_guides_buttons(peer, guides):
    def make_button(guide):
        return interactive_media.InteractiveMedia(
            1, interactive_media.InteractiveMediaButton(guide["value"], guide["title"])
        )

    buttons = [
        interactive_media.InteractiveMediaGroup([make_button(x) for x in guides])
    ]

    bot.messaging.send_message(peer, "Choose guide", buttons)


def guide_list(id, peer):
    user = reviews.find_one({"id": id})
    guide_list_res = list(guides.find({"company": user["company"]}))
    return guide_list_res


def get_guides(id, peer):
    guide_list_data = guide_list(id, peer)
    render_guides_buttons(peer, guide_list_data)


def generate_guide_value(company):
    number = len(list(guides.find({"company": company})))
    if number == 0:
        res = company + "1"
    else:
        res = company + str(number + 2)

    return res


def get_company(id):
    res = reviews.find_one({"id": id})["company"]
    return res


def add_guide(id, company, content, title):
    value = generate_guide_value(company)
    guides.insert_one(
        {"company": company, "value": value, "content": content, "title": title}
    )



def on_click(*params):
    id = params[0].uid
    value = params[0].value
    peer = bot.users.get_user_peer_by_id(id)
    if (value == "create_company"):
            bot.messaging.send_message(peer, "Введите имя компании")
            def waiting_of_creating_company(*params):
                reviews.insert_one({"type": "Office-manager", "company": params[0].message.textMessage.text, "id": id})
                bot.messaging.send_message(peer, "Компания успешно создана. Теперь вы админ")
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)
            bot.messaging.on_message(waiting_of_creating_company)

    all_guides = guide_list(id, peers)
    guides_values = [x["value"] for x in all_guides]

    if value in guides_values:
        guide = guides.find_one({"value": value})
        bot.messaging.send_message(peer, guide["title"])

        time.sleep(1)

        bot.messaging.send_message(peer, guide["content"])

    if value == "add_guide":
        bot.messaging.send_message(peer, "Write Title for guide")

        # TODO DO BETTER PLEASE IT IS SIDE EFFECTS!
        def get_content_and_go_main(*params):
            title = params[0].message.textMessage.text

            bot.messaging.send_message(peer, "Write Content for guide content")

            def fn_and_go_main(*params):
                content = params[0].message.textMessage.text
                company = get_company(id)

                # save guide
                add_guide(id, company, content, title)
                bot.messaging.send_message(peer, "You created guide")

                main(*params)

                bot.messaging.on_message(main, on_click)

            bot.messaging.on_message(fn_and_go_main)

        bot.messaging.on_message(get_content_and_go_main)

    if value == "get_token":
        bot.messaging.send_message(peer, "you click button " + value)

    if value == "get_guides":
        get_guides(id, peer)


if __name__ == "__main__":
    bot = DialogBot.get_secure_bot(
        "hackathon-mob.transmit.im",  # bot endpoint (specify different endpoint if you want to connect to your on-premise environment)
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        bot_token,  # bot token Nikita , Nikita 2 - "d3bdd8ab024c03560ecf3350bcc3c250a0bbe9cd",
        verbose=False,  # optional parameter, when it's True bot prints info about the called methods, False by default
    )

# work like return , block code after, if want to use code after, use async vers
bot.messaging.on_message(main, on_click)

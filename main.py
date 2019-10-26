from dialog_bot_sdk.bot import DialogBot
from dialog_bot_sdk import interactive_media
from threading import Timer
from pymongo import MongoClient
import grpc
import time

# Utils
client = MongoClient(
    "mongodb://team:123ert@ds018839.mlab.com:18839/new_hackaton", retryWrites=False
)
db = client.new_hackaton
users = db.users
guides = db.guides
bot_token = "fc1595f3591f137461a1ad6441062e083fd366a1"
tokens = db.tokens
cost = db.cost
# https://github.com/dialogs/chatbot-hackathon - basic things
# https://hackathon.transmit.im/web/#/im/u2108492517 - bot


def add_user_to_admins(id, company):
    users.insert_one({"type": "Office-manager", "id": id, "company": company})


def add_user_to_users(id, company):
    users.insert_one({"type": "User", "id": id, "company": company})


def is_exist(id):
    return False if users.find_one({"id": id}) is None else True


def is_manager(id):
    return True if users.find_one({"id": id})["type"] == "Office-manager" else False


def on_msg(msg, peer):
    bot.messaging.send_message(peer, msg)


def has_token(id, *params):
    message = params[0].message.textMessage.text
    token = tokens.find_one({"token": message})
    if token is None:
        return want_to_create(*params)
    else:
        return whose_token(token, id, params[0].peer)


def whose_token(token, id, peer):
    current_time = int(time.time() * 1000.0)

    if current_time - int(token["time"]) >= 24 * 60 * 60 * 1000:
        delete_token(token)
        return on_msg("Ваш токен устарел", peer)

    if token["type"] == "Office-manager":
        add_user_to_admins(id, token["company"])
        send_manager_buttons(id, peer)
    else:
        add_user_to_users(id, token["company"])
        get_guides(id, peer)


def want_to_create(*params):
    bot.messaging.send_message(
        params[0].peer,
        "Хотите создать новую компанию в списке?",
        [
            interactive_media.InteractiveMediaGroup(
                [
                    interactive_media.InteractiveMedia(
                        1,
                        interactive_media.InteractiveMediaButton(
                            "create_company", "Да"
                        ),
                    ),
                    interactive_media.InteractiveMedia(
                        1,
                        interactive_media.InteractiveMediaButton(
                            "not_create_company", "Нет"
                        ),
                    ),
                ]
            )
        ],
    )


def send_manager_buttons(id, peer):
    buttons = [
        interactive_media.InteractiveMediaGroup(
            [
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "add_money", "Добавить деньги"
                    ),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "add_costs", "Добавить расходы"
                    ),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "get_admin_token",
                        "Получить ключ для приглашения Офис менеджера",
                    ),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "current", "Узнать баланс"
                    ),
                ),

            ]
        )
    ]

    bot.messaging.send_message(peer, "Выберите действие", buttons)


def auth(id, peer, *params):
    if is_exist(id):
        send_manager_buttons(id, peer) if is_manager(id) else get_guides(id, peer)
    else:
        has_token(id, *params)


def start_text(peer):
    bot.messaging.send_message(
        peer,
        "Здравствуйте это бот для онбординга. Чтобы узнать дополнительную информацию напишите /info (вставтьте ключ или напишите сообщение)",
    )


def info_text(peer):
    bot.messaging.send_message(
        peer,
        "Вход в бота может осуществляться через ключ, либо он выполнится автоматически на написание любого сообщения если вы уже зарегистрированны",
    )


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

    auth(id, peer, *params)


def render_guides_buttons(peer, guides):
    def make_button(guide):
        return interactive_media.InteractiveMedia(
            1, interactive_media.InteractiveMediaButton(guide["value"], guide["title"])
        )

    buttons = [
        interactive_media.InteractiveMediaGroup([make_button(x) for x in guides])
    ]

    bot.messaging.send_message(peer, "Выберите гайд", buttons)


def guide_list(id):
    user = users.find_one({"id": id})
    guide_list_res = list(guides.find({"company": user["company"]}))
    return guide_list_res


def get_guides(id, peer):
    guide_list_data = guide_list(id)
    render_guides_buttons(peer, guide_list_data)


def generate_guide_value(company):
    number = len(list(guides.find({"company": company})))
    if number == 0:
        res = company + "1"
    else:
        res = company + str(number + 2)

    return res


def get_company(id):
    res = users.find_one({"id": id})["company"]
    return res


def add_guide(company, content, title):
    value = generate_guide_value(company)
    guides.insert_one(
        {"company": company, "value": value, "content": content, "title": title}
    )


def delete_guide(id, peer):
    bot.messaging.send_message(peer, "Напишите название гайда который хотите удалить")

    def delete(*params):
        guide_name = params[0].message.textMessage.text
        delete_res = guides.find_one_and_delete({"title": guide_name})
        if delete_res is None:
            bot.messaging.send_message(peer, "Гайда с таким названием не существует")
        else:
            bot.messaging.send_message(peer, "Гайд " + guide_name + " удалён")
        auth(id, peer, *params)
        bot.messaging.on_message(main, on_click)

    bot.messaging.on_message(delete)


def delete_token(token):
    tokens.delete_one({"_id": token["_id"]})


def on_click(*params):
    id = params[0].uid
    value = params[0].value
    peer = bot.users.get_user_peer_by_id(id)

    if value == "not_create_company":
        bot.messaging.send_message(
            peer,
            "Чтобы пользоваться ботом нужно иметь ключ или создать компанию или быть зарегистрированным",
        )
        return
    if value == "create_company":
        bot.messaging.send_message(peer, "Введите имя компании")

        def waiting_of_creating_company(*params):
            company_name = params[0].message.textMessage.text
            exits_companies_dict = list(users.find({"company": company_name}))
            exits_companies_list = [x["company"] for x in exits_companies_dict]
            def getting_current_leftover(*params):
                bot.messaging.send_message(peer, "Мне заебись я попал сюда")
                cost.insert_one({"leftover": params[0].message.textMessage.text})
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)
            if company_name in exits_companies_list:
                bot.messaging.send_message(
                    peer, "Компания с таким именем уже существует"
                )
            else:
                users.insert_one({"type": "Office-manager", "company": company_name, "id": id})
                bot.messaging.send_message(peer, "Компания успешно создана. Введите количество денег на счету")
                bot.messaging.on_message(getting_current_leftover)

        bot.messaging.on_message(waiting_of_creating_company)

    all_guides = guide_list(id)
    guides_values = [x["value"] for x in all_guides]

    if value in guides_values:
        guide = guides.find_one({"value": value})
        bot.messaging.send_message(peer, guide["title"])

        time.sleep(1)

        bot.messaging.send_message(peer, guide["content"])

    if value == "add_money":
        pass

    if value == "delete_guide":
        delete_guide(id, peer)

    if value == "get_user_token":
        #TODO heer 
        bot.messaging.send_message(peer, "Введите название расхода: " )

    if value == "get_admin_token":
        current_time = str(int(time.time() * 1000.0))
        token = get_company(id) + current_time
        tokens.insert_one(
            {
                "token": token,
                "type": "Office-manager",
                "company": get_company(id),
                "time": current_time,
            }
        )
        bot.messaging.send_message(peer, "Ключ для офис менеджера: " + token)

    if value == "get_guides":
        get_guides(id, peer)


if __name__ == "__main__":
    bot = DialogBot.get_secure_bot(
        "hackathon-mob.transmit.im",  # bot endpoint (specify different endpoint if you want to connect to your on-premise environment)
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        bot_token,
        verbose=False,  # optional parameter, when it's True bot prints info about the called methods, False by default
    )

bot.messaging.on_message(main, on_click)

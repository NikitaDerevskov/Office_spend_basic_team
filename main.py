from dialog_bot_sdk.bot import DialogBot
from dialog_bot_sdk import interactive_media
from threading import Timer
from pymongo import MongoClient
import grpc
import time
import datetime
# Utils
client = MongoClient(
    "mongodb://team:123ert@ds018839.mlab.com:18839/new_hackaton", retryWrites=False
)
now = datetime.datetime.now()
db = client.new_hackaton
users = db.users
guides = db.guides
bot_token = "fc1595f3591f137461a1ad6441062e083fd366a1"
tokens = db.tokens
cost = db.cost
company = db.company
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
                        "current", "Узнать баланс"
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
                        "listOfCosts", "Список расходов"
                    ),
                ),
                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "add_money", "Добавить деньги"
                    ),
                ),

                interactive_media.InteractiveMedia(
                    1,
                    interactive_media.InteractiveMediaButton(
                        "get_admin_token",
                        "Получить ключ для приглашения Офис менеджера",
                    ),
                ),
            ]
        )
    ]

    bot.messaging.send_message(peer, "Выберите действие", buttons)


def auth(id, peer, *params):
    if is_exist(id):
        send_manager_buttons(id, peer)
    else:
        has_token(id, *params)


def start_text(peer):
    bot.messaging.send_message(
        peer,
        "Здравствуйте это бот для подсчета расходов. Чтобы узнать дополнительную информацию напишите /info (вставтьте ключ или напишите сообщение)",
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

def get_company(id):
    res = users.find_one({"id": id})["company"]
    return res


def delete_token(token):
    tokens.delete_one({"_id": token["_id"]})

def get_current(id,peer):
    company_res = get_company(id)
    res = company.find_one({"company": company_res})["leftover"]
    bot.messaging.send_message(peer,res)

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
    if value == "listOfCosts":
        user = get_company(id)
        title_list_res = list(cost.find({"company": user}))
        exits_companies_list = [x["title"] for x in title_list_res]
        exits_companies_list2 = [x["changing"] for x in title_list_res]
        exits_companies_list3 = [x["time"] for x in title_list_res]
        for i in range (len(exits_companies_list)):
            bot.messaging.send_message(peer,str(i+1)+") Название: " + exits_companies_list[i]+ "; Сумма: "+ exits_companies_list2[i] + "; Время создания: " + exits_companies_list3[i] )
        auth(id, peer, *params)
        bot.messaging.on_message(main, on_click)
    if value == "current":
        get_current(id,peer)
    if value == "add_costs":
        bot.messaging.send_message(peer, "Введите название расхода")

        def get_cost_name(*params):
            bot.messaging.send_message(peer, "Введите величину расхода ")
            cost_name = params[0].message.textMessage.text
            def cost_value(*params):
                try:
                    cost_value = int(params[0].message.textMessage.text)
                except ValueError:
                    bot.messaging.send_message(peer, "Введена некорректная величина. Попробуйте еще раз")
                    auth(id, peer, *params)
                    bot.messaging.on_message(main, on_click)
                if cost_value <= 0:
                    bot.messaging.send_message(peer, "Введена некорректная величина. Попробуйте еще раз")
                    auth(id, peer, *params)
                    bot.messaging.on_message(main, on_click)
                company_name = get_company(id)
                current_time2 = now.strftime("%d-%m-%Y %H:%M")
                cost.insert_one({"company": company_name, "title":str(cost_name), "changing": str(cost_value),"time": str(current_time2) })
                company_res = get_company(id)
                current_leftover = company.find_one({"company": company_res})["leftover"]
                company.remove({"company" : company_res})
                company.insert_one({"company": company_res,  "leftover": str(int(current_leftover)-int(params[0].message.textMessage.text))})
                res = company.find_one({"company": company_res})["leftover"]
                if int(res)<0:
                    bot.messaging.send_message(peer,"Вы ушли в минус! Пополните баланс!")
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)

            bot.messaging.on_message(cost_value)

        bot.messaging.on_message(get_cost_name)
    if value == "add_money":
        def adding_money(*params):
            try:
                cost_value = int(params[0].message.textMessage.text)
            except ValueError:
                bot.messaging.send_message(peer, "Введена некорректная величина. Попробуйте еще раз")
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)
            if cost_value <= 0:
                bot.messaging.send_message(peer, "Введена некорректная величина. Попробуйте еще раз")
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)

            company.remove({"company" : company_res})
            company.insert_one({"company": company_res,  "leftover": str(cost_value)})
            auth(id, peer, *params)
            bot.messaging.on_message(main, on_click)
        company_res = get_company(id)
        res = company.find_one({"company": company_res})["leftover"]
        bot.messaging.send_message(peer,"Ваш текущий баланс равен " + res +" Сколько должно быть денег?")
        bot.messaging.on_message(adding_money)
    if value == "create_company":
        bot.messaging.send_message(peer, "Введите имя компании")

        def waiting_of_creating_company(*params):
            company_name = params[0].message.textMessage.text
            exits_companies_dict = list(users.find({"company": company_name}))
            exits_companies_list = [x["company"] for x in exits_companies_dict]

            def getting_current_leftover(*params):
                leftover_try = params[0].message.textMessage.text
                try:
                    cost_value = int(params[0].message.textMessage.text)
                except ValueError:
                    bot.messaging.send_message(
                        peer, "Введено неверное значение"
                    )
                    users.remove({"company" : company_name})
                    bot.messaging.on_message(main,on_click)
                if int(leftover_try)<=0:
                    bot.messaging.send_message(
                        peer, "Введено неверное значение"
                    )
                    users.remove({"company" : company_name})
                    bot.messaging.on_message(main,on_click)
                company.insert_one({"company": company_name,"leftover": leftover_try })
                auth(id, peer, *params)
                bot.messaging.on_message(main, on_click)

            if company_name in exits_companies_list:
                bot.messaging.send_message(
                    peer, "Компания с таким именем уже существует"
                )
            else:
                users.insert_one(
                    {"type": "Office-manager", "company": company_name, "id": id}
                )
                bot.messaging.send_message(
                    peer, "Введите количество денег на счету"
                )

            bot.messaging.on_message(getting_current_leftover)

        bot.messaging.on_message(waiting_of_creating_company)

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




if __name__ == "__main__":
    bot = DialogBot.get_secure_bot(
        "hackathon-mob.transmit.im",  # bot endpoint (specify different endpoint if you want to connect to your on-premise environment)
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        bot_token,
        verbose=False,  # optional parameter, when it's True bot prints info about the called methods, False by default
    )

bot.messaging.on_message(main, on_click)

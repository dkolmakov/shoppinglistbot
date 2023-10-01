import logging
import sys
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ApplicationBuilder, CallbackQueryHandler
from read_spreadsheet import read_items_list

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

main_menu_keyboard = [['Show list', 'Show full list', 'Reset states']]
reply_keyboard = ReplyKeyboardMarkup(main_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)

async def start(update: Update, context) -> None:
    await update.message.reply_text('Hello! It\'s your buying list bot!', reply_markup=reply_keyboard)

class ItemState:
    def __init__(self, name, default):
        self.name = name
        self.default = default
        self.active = default
        logger.info(f"create - {self.name}")

    def is_active(self):
        return self.active
    
    def activate(self):
        logger.info(f"activate - {self.name}")
        self.active = True

    def deactivate(self):
        logger.info(f"deactivate - {self.name}")
        self.active = False

    def reset(self):
        logger.info(f"reset - {self.name}")
        self.active = self.default

    def make_button(self, data):
        logger.info(f"make {data} button - {self.name}")
        symbol = '\U0001F7E2' if self.active else '\U0001F534'
        return InlineKeyboardButton(f"{symbol} {self.name}", callback_data=f"{data}")


class ItemsState:
    def __init__(self):
        self.items_state = {}
        self.item_to_id = {}

        items, users = read_items_list()

        self.users = users

        for i, (item, default) in enumerate(items):
            self.items_state[item] = ItemState(item, default)
            self.item_to_id[item] = i

    def update_list(self):
        new_list = {}

        logger.info(f"ItemsState.update_list")
        items, users = read_items_list()

        self.users = users

        for item, default in items:
            if item in self.items_state.keys():
                new_list[item] = self.items_state[item]
                new_list[item].default = default
            else:
                new_list[item] = ItemState(item, default)
                new_list[item].reset()

        self.items_state = new_list
        self.item_to_id = {}

        for i, item in enumerate(self.items_state.keys()):
            self.item_to_id[item] = i

    def get_item_by_id(self, num):
        for name, i in self.item_to_id.items():
            if i == num:
                return name
            
        return ""

    def get_id_by_item(self, item):
        if item in self.item_to_id.keys():
            return self.item_to_id[item]
        
        return ""
    
    def activate(self, item) -> bool:
        logger.info(f"ItemsState.activate {item}")

        if item in self.items_state.keys():
            self.items_state[item].activate()
            return True
        
        return False

    def deactivate(self, item) -> bool:
        # Create ordering here
        logger.info(f"ItemsState.deactivate {item}")

        if item in self.items_state.keys():
            self.items_state[item].deactivate()
            return True

        return False

    def reset(self):
        self.update_list()

        for item, state in self.items_state.items():
            state.reset()

    def active_item_list_keyboard(self):
        keyboard = []

        logger.info(f"active items list")

        # Apply ordering here
        for item, state in self.items_state.items():
            if state.is_active():
                keyboard.append([state.make_button(f"active_list|deactivate|{self.get_id_by_item(item)}")])

        return InlineKeyboardMarkup(keyboard)

    def full_item_list_keyboard(self):
        keyboard = []

        logger.info(f"full items list")

        # Apply ordering here
        for item, state in self.items_state.items():
            if state.is_active():
                keyboard.append([state.make_button(f"full_list|deactivate|{self.get_id_by_item(item)}")])
            else:
                keyboard.append([state.make_button(f"full_list|activate|{self.get_id_by_item(item)}")])

        return InlineKeyboardMarkup(keyboard)
    

class ShowListHandler:
    def __init__(self, state):
        self.state = state

    async def __call__(self, update: Update, context) -> None:
        self.state.update_list()

        user = update.message.from_user
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=f"Hello {user.first_name}! Current list:",
                                    reply_markup=self.state.active_item_list_keyboard())

class ShowFullListHandler:
    def __init__(self, state):
        self.state = state

    async def __call__(self, update: Update, context) -> None:
        self.state.update_list()

        user = update.message.from_user
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                    text=f"Hello {user.first_name}! Full items list:",
                                    reply_markup=self.state.full_item_list_keyboard())

class ResetHandler:
    def __init__(self, state):
        self.state = state

    async def __call__(self, update: Update, context) -> None:
        self.state.reset()
        await update.message.reply_text('Reset is done!', reply_markup=reply_keyboard)

class DeactivateItemHandler:
    def __init__(self, state):
        self.state = state

    async def __call__(self, update: Update, context) -> None:
        query = update.callback_query
        current_list = query.data.split('|')[0]
        item_num = int(query.data.split('|')[2])

        await query.answer()

        if self.state.deactivate(self.state.get_item_by_id(item_num)):
            if current_list == "active_list":
                new_keyboard = self.state.active_item_list_keyboard()
            else:
                new_keyboard = self.state.full_item_list_keyboard()

            await query.edit_message_text(
                text="Updated!",
                reply_markup=new_keyboard,
            )    

class ActivateItemHandler:
    def __init__(self, state):
        self.state = state

    async def __call__(self, update: Update, context) -> None:
        query = update.callback_query
        item_num = int(query.data.split('|')[2])

        await query.answer()

        if self.state.activate(self.state.get_item_by_id(item_num)):
            new_keyboard = self.state.full_item_list_keyboard()

            await query.edit_message_text(
                text="Updated!",
                reply_markup=new_keyboard,
            )    


class UserFilter(filters.MessageFilter):
    def __init__(self, users):
        self.users = users
        self._data_filter = True

    def filter(self, message):
        return message.from_user.id in self.users

def main() -> None:
    bot_token = sys.argv[1]

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))

    state = ItemsState()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex('^Show list$') & UserFilter(state.users), ShowListHandler(state)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex('^Show full list$') & UserFilter(state.users), ShowFullListHandler(state)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex('^Reset states$') & UserFilter(state.users), ResetHandler(state)))

    app.add_handler(CallbackQueryHandler(DeactivateItemHandler(state), pattern=r"^(active_list|full_list)\|deactivate\|.+"))
    app.add_handler(CallbackQueryHandler(ActivateItemHandler(state), pattern=r"^full_list\|activate\|.+"))

    # Start the Bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

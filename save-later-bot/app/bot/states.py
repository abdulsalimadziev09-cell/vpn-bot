from aiogram.fsm.state import State, StatesGroup


class AddTags(StatesGroup):
    waiting_for_tags = State()


class Search(StatesGroup):
    waiting_for_query = State()

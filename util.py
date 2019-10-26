from enum import Enum
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton


class Icons:
    Back = '🔙'
    Shrugging = '🤷🏽‍'
    Cancel = '✖'
    Cup = '🏆'
    CancelBold = '❌'
    OK = '✔'
    CheckBox = '☑'
    Male = '👔'
    Female = '👠'
    People = '👤'
    Peoples = '👥'
    Photo = '📷'
    Voice = '🗣'
    Geo = '🌍'
    Pizza = '🍕'
    Dating = '🍓'
    Nan = ''
    Like = '❤'
    Question = '❓'
    Calc = '🗣'
    Find = '🔍'
    Settings = '⚙'
    Wait = '⏳'
    Lite = '🚦'
    Circle = '⭕'
    Stop = '⛔'
    Megaphone = '🔊'
    Record = '🎙'
    ManWoman = '🚻'
    Warning = '❕'
    WarningFill = '❗'
    Info = 'ℹ'
    Telephone = '📞'
    TelephoneOld = '☎'
    Basket = '🛒'
    Cash = '💰'
    Flash = '⚡'
    SatelliteDish = '📡'
    PowerOn = '🔅'
    Lamp = '💡'
    Baloon = '💬'
    ThoughtBaloon = '💭'
    Clipboard = '📋'
    WhiteCircle = '⚪'


def reply_keyboard(*buttons, row_width=3):
    kb = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=True)
    keys = [KeyboardButton(text=btn.value) for btn in buttons]
    # for btn in buttons:
    #     keys.append(KeyboardButton(text=btn.value))
    kb.add(*keys)
    return {'keyboard': kb, 'buttons': buttons}


def button(text, icon=None):
    if icon is None:
        return text
    else:
        return f'{icon} {text}'


def inline_button(text, icon=Icons.Nan, callback_data=None):
    text = f'{icon} {str(text)}'
    callback_data = str(text) if callback_data is None else callback_data
    return InlineKeyboardButton(text, callback_data=callback_data)


def inline_keyboard(*buttons, row_width=2):
    keyboard = InlineKeyboardMarkup()
    keyboard.row_width = row_width
    buttons = [b.value if isinstance(b, InlineButtons) else b for b in buttons]
    keyboard.add(*buttons)
    return keyboard


class RoomUserStatus(Enum):
    Entered = 0
    SentMessage = 1
    PressedInlineButton = 2
    PressedButton = 3


class InlineButtons(Enum):
    CreateGame = inline_button('Создать', Icons.Lamp)
    ConnectToGame = inline_button('Подключиться', Icons.SatelliteDish)
    SinglePlayer = inline_button('Одиночная игра', Icons.People)
    MultiPlayer = inline_button('Сетевая игра', Icons.Peoples)
    Cancel = inline_button('Отменить', Icons.Cancel)
    SetupBoardScale = inline_button('Установить размер поля', Icons.Settings)
    SetScaleCount3 = inline_button('3x3')
    SetScaleCount4 = inline_button('4x4')
    SetScaleCount5 = inline_button('5x5')
    SetScaleCount6 = inline_button('6x6')


def make_inline_keyboard_from_board(board):
    buttons = []
    for x, line in enumerate(board):
        for y, item in enumerate(line):
            if item == 1:
                text = Icons.CancelBold
            elif item == 2:
                text = Icons.WhiteCircle
            else:
                text = ''
            buttons.append(inline_button(text, callback_data=f'board_{x}_{y}'))
    return inline_keyboard(*buttons, row_width=board.count)


class InlineKeyboards:
    CreateConnect = inline_keyboard(InlineButtons.CreateGame, InlineButtons.ConnectToGame)
    SingleMultiPlayer = inline_keyboard(InlineButtons.SinglePlayer, InlineButtons.MultiPlayer,
                                        InlineButtons.SetupBoardScale)
    Cancel = inline_keyboard(InlineButtons.Cancel)
    SetBoardScale = inline_keyboard(InlineButtons.SetScaleCount3, InlineButtons.SetScaleCount4,
                                    InlineButtons.SetScaleCount5, InlineButtons.SetScaleCount6,
                                    row_width=3)


class ReplyKeyboardButtons(Enum):
    Off = button('Сдаться', Icons.Cancel)
    Cancel = button('Вернуться в меню', Icons.Cancel)


class ReplyKeyboards:
    Off = reply_keyboard(ReplyKeyboardButtons.Off)
    Cancel = reply_keyboard(ReplyKeyboardButtons.Cancel)


class Rooms(Enum):
    Start = 0
    MenuSingleMultiPlayer = 2
    MenuSetBoardScale = 3
    WaitingPartner = 4
    GameMultiPlayer = 5
    GameSinglePlayer = 6
    GameFinish = 7


rooms_keyboards = {
    Rooms.MenuSingleMultiPlayer: InlineKeyboards.SingleMultiPlayer,
    Rooms.WaitingPartner: InlineKeyboards.Cancel,
    Rooms.GameMultiPlayer: ReplyKeyboards.Off,
    Rooms.GameSinglePlayer: ReplyKeyboards.Off
}

global_keyboards = [ReplyKeyboards.Cancel]

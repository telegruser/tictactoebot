from aiogram import Bot
from random import choice
from util import RoomUserStatus, rooms_keyboards, Icons, InlineButtons, ReplyKeyboardButtons, global_keyboards, \
    ReplyKeyboardMarkup


class User:

    bot: Bot = None
    users = []

    def delete(self):
        self.__class__.users.remove(self)

    @classmethod
    def identification(cls, account_id: int):
        """
        Получает id пользователя, если пользователь уже есть в памяти то возвращает его.
        В противном случае инициализирует и возвращает нового.
        """
        for user in cls.users:
            if user.account_id == account_id:
                return user
        return cls(account_id)

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.control_message_id = None
        self.control_message_with_keyboard = False
        self.room = None
        self.state = RoomUserStatus.Entered
        self.callback_data = None
        self.message = None
        self.call_message = None
        self.button = None
        self.game = None
        self.game_queue = None
        self.board_scale = 3
        if self not in self.__class__.users:
            self.__class__.users.append(self)

    # def get_reply_markup(self, reply_markup=None):
    #     """Предоставляет клавиатуру в соответствии с текущей комнатой пользователя"""
    #     if reply_markup is None:
    #         reply_markup = rooms_keyboards.get(self.room, ReplyKeyboardRemove())
    #     if isinstance(reply_markup, dict):
    #         reply_markup = reply_markup.get('keyboard', None)
    #     return reply_markup

    async def send_message(self, text, parse_mode=None, keyboard=None, **opts):
        # reply_markup = self.get_reply_markup(keyboard)
        # opts['reply_markup'] = reply_markup
        return await self.send_method(self.bot.send_message, text, parse_mode=parse_mode, reply_markup=keyboard)

    async def send_method(self, method, *args, **kwargs):
        """
        Выполняет полученный метод отправки сообщения,
        подставив нужную клавиатуру и параметры
        """
        reply_markup = kwargs.get('reply_markup', None)
        if reply_markup is None:
            reply_markup = rooms_keyboards.get(self.room, None)
        if isinstance(reply_markup, dict):
            reply_markup = reply_markup.get('keyboard', reply_markup)
        kwargs['reply_markup'] = reply_markup
        try:
            return await method(self.account_id, *args, **kwargs)
        except Exception as e:
            print(f'ошибка при отправке сообщения. {e}')
            if not await self.is_available:
                self.delete()

    @property
    async def is_available(self):
        """Проверяет, заблокировал ли пользователь бота, отправив ему typing
        True - доступен
        False - заблокирован
        """
        try:
            await self.bot.send_chat_action(self.account_id, 'typing')
        except Exception as e:
            return False
        else:
            return True

    async def show_control_message(self, title,
                                   text='',
                                   keyboard=None,
                                   icon=Icons.Nan,
                                   new=False,
                                   delete_previous_control_message=True,
                                   breaking=False):
        """ Отправляет room_content следя за тем, что-бы оно было последним """
        full_text = f'{icon} <b>{title}</b>\n\n<i>{text}</i>'
        # Если у user еще нет control_message
        if self.control_message_id is None:
            new_room_content = await self.send_message(full_text, 'HTML', keyboard)
            self.control_message_id = None if breaking else new_room_content.message_id
            return new_room_content
        # Если это клавиатура то удаляем и заного посылаем
        if self.control_message_with_keyboard:
            if not new:
                await self.bot.delete_message(self.account_id, self.control_message_id)
            new_room_content = await self.send_message(full_text, 'HTML', keyboard)
            self.control_message_id = None if breaking else new_room_content.message_id
            return new_room_content
        self.control_message_with_keyboard = isinstance(keyboard, ReplyKeyboardMarkup)
        # Пробуем отредактировать сообщение, не получилось - переотправляем
        if new:
            new_room_content = await self.send_message(full_text, 'HTML', keyboard)
            self.control_message_id = None if breaking else new_room_content.message_id
            return new_room_content
        else:
            try:
                edited = await self.bot.edit_message_text(
                    full_text, self.account_id, self.control_message_id, parse_mode='HTML', reply_markup=keyboard)
            except:
                # pass
            # if not edited:
                await self.bot.delete_message(self.account_id, self.control_message_id)
                new_room_content = await self.send_message(full_text, 'HTML', keyboard)
                self.control_message_id = None if breaking else new_room_content.message_id
                return new_room_content
            else:
                if breaking:
                    self.control_message_id = None
                return edited

    def check_state(self, message, call_data):
        """
        Возвращает состояние пользователя,
        определяет нажатую кнопку если она заранее определена
        """
        if call_data is not None:
            dct = {ib.value.callback_data: ib for ib in InlineButtons}
            self.button = dct.get(call_data, None)
            self.callback_data = call_data
            self.state = RoomUserStatus.PressedInlineButton
            self.call_message = message
        elif message is None:
            self.state = RoomUserStatus.Entered
            # keys = rooms_keyboards.get(self.room, None)
            # if message.text in [b. for b in keys.]
            # elif message.text in [b.value for b in rooms_keyboards.get(self.room, {'buttons': []})['buttons']]:
        elif (message.text in [b for b in rooms_keyboards.get(self.room, {'buttons': []})] or
              message.text in [b.value for b in sum([list(b['buttons']) for b in global_keyboards], [])]):
            # dct = {b.value: b for b in ReplyKeyboardButtons}
            # btn = dct.get(message.text, None)
            self.button = {b.value: b for b in ReplyKeyboardButtons}.get(message.text, None)
            self.state = RoomUserStatus.PressedButton
        else:
            self.state = RoomUserStatus.SentMessage
        self.message = message
        return self.state


class Board:

    @staticmethod
    def make_board(count):
        if count < 3 or count > 8:
            raise Exception('Количество ячеек должно быть не меньше 3 и не больше 8')
        board = []
        for x in range(count):
            line = []
            for y in range(count):
                line.append(None)
            board.append(line)
        return board

    def __getitem__(self, item):
        return self._board[item]

    def __init__(self, count, board=None):
        self._board = self.make_board(count) if board is None else board
        self.count = count
        self.step_number = 1

    @property
    def copy(self):
        new_board = []
        for b in self._board:
            new_board.append(b.copy())
        return Board(self.count, new_board)

    @property
    def legal_moves(self):
        legal_moves = []
        for x in range(self.count):
            for y in range(self.count):
                if self.empty(x, y):
                    legal_moves.append((x, y))
        return legal_moves

    def empty(self, x, y):
        return True if self[x][y] is None else False

    def choose_random_move(self, *moves):
        # Возвращает случайный ход из полученного списка возможных ходов
        # Возвращает None если ходов нет
        legal_moves_set = set(self.legal_moves)
        moves_set = set(moves)
        try:
            x, y = choice(list(moves_set.intersection(legal_moves_set)))
            return x, y
        except IndexError as e:
            return None

    def set(self, x, y, value):
        self._board[x][y] = value
        self.step_number += 1
        print('ПРОВЕРКА НА ВЫЙГРЫШЬ. ПОЛНАЯ ТАБЛИЦА ВЫГЛЯДИТ ТАК:')
        for line in self._board:
            print(line)
        print('Проверка каждой линии..')
        return self.check(value)

    def check_diagonals(self, value):
        for x in range(self.count-2):
            diagonal = []
            for y in range(self.count-x):
                diagonal.append(self._board[x+y][y])
            if self._check_list(diagonal, value):
                return True

        for y in range(1, self.count - 2):
            diagonal = []
            for x in range(self.count - y):
                diagonal.append(self._board[x][y+x])
            if self._check_list(diagonal, value):
                return True

        for x0 in range(self.count-2):
            diagonal = []
            for y0 in range(self.count-x0):
                diagonal.append(self._board[self.count-x0-y0-1][y0])
            if self._check_list(diagonal, value):
                return True

        for y0 in range(1, self.count-2):
            diagonal = []
            for x0 in range(self.count-y0):
                diagonal.append(self._board[self.count-x0-1][self.count-y0-x0])
            if self._check_list(diagonal, value):
                return True

    def check_diagonal(self, x, y, value):
        lst = []
        for i in range(self.count):
            lst.append(self._board[x+i][y+i])
        return self._check_list(lst, value)

    @staticmethod
    def _check_list(lst, value):
        print(lst)
        count = 0
        for item in lst:
            if item == value:
                count += 1
            if count == 3:
                return True
            if item != value:
                count = 0
        return False

    def _check_line(self, n, direction, value):
        line = []
        if direction == 0:
            line = self._board[n]
        elif direction == 1:
            for i in range(self.count):
                line.append(self._board[i][n])
        return self._check_list(line, value)

    def check_lines(self, value):
        for i in range(self.count):
            if self._check_line(i, 0, value):
                return True
        for i in range(self.count):
            if self._check_line(i, 1, value):
                return True

    def check(self, gamer):
        if self.check_lines(gamer):
            return True
        if self.check_diagonals(gamer):
            return True
        return False


class Game:

    char_dict = {1: Icons.CancelBold, 2: Icons.WhiteCircle, 0: ''}

    def user_symbol(self, user):
        return self.symbol(user.game_queue)

    def __repr__(self):
        board = self.board.copy
        for x, line in enumerate(board):
            for y, el in enumerate(line):
                board[x][y] = self.symbol(board[x][y])
        return board

    def start_with_pc(self):
        if choice((1, 0)):
            self.players_queue = {1: self.creator, 2: 'pc'}
            self.creator.game_queue = 1
            self.pc_queue = 2
            self.creator_queue = 1
        else:
            self.players_queue = {2: self.creator, 1: 'pc'}
            self.creator.game_queue = 2
            self.pc_queue = 1
            self.creator_queue = 2

        if self.now_user_queue == 'pc':
            self.step_auto()

    def start_waiting_partner(self):
        self.waiting_partner = True

    def start_with_user(self, user):
        user.game = self
        self.waiting_partner = False
        self.players_queue = {1: self.creator, 2: user}
        self.creator.game_queue = 1
        user.game_queue = 2

    def __init__(self, user: User, count):
        self.board = Board(count)
        self.winner = None
        self.queue = 1
        self.pc_queue = None
        self.creator_queue = None
        self.creator: User = user
        self.players_queue = {}
        user.game = self
        self.waiting_partner = False

    @property
    def now_user_queue(self):
        return self.players_queue[self.queue]

    def symbol(self, num):
        return self.__class__.char_dict[num]

    def queue_reverse(self):
        if self.queue == 2:
            self.queue = 1
            return
        if self.queue == 1:
            self.queue = 2
            return

    @property
    def step_number(self):
        return self.board.step_number

    def step(self, x, y):
        """
        Производит ход на клетку с координатами x, y.
        Если после хода игра завершилась,
        то возвращает победителя или 0 если ничья.
        """
        if self.board.set(x, y, self.queue):
            self.winner = self.queue
            # return self.finish_game()
        elif len(self.board.legal_moves) == 0:
            self.winner = 0
        self.queue_reverse()
        if self.winner is not None:
            if self.winner == 0:
                return self.winner
            return self.players_queue[self.winner]

    def step_auto(self):
        x, y = self.compute_coord()
        return self.step(x, y)

    def compute_coord(self):
        legal_moves = self.board.legal_moves

        # Проверка возможности выйгрыша с одного хода
        for x, y in legal_moves:
            board = self.board.copy
            if board.set(x, y, self.queue):
                self.winner = self.queue
                return x, y

        # self.queue_reverse()
        # Проверяем, может ли игрок выиграть на следющем ходу, чтобы заблокировать его
        for x, y in legal_moves:
            board = self.board.copy
            if board.set(x, y, self.creator_queue):
                # self.queue_reverse()
                return x, y

        # self.queue_reverse()
        return choice(self.board.legal_moves)
        # Попытаемся занять один из углов, если они свободны
        # angles = (0, 0), (0, 2), (2, 0), (2, 2)
        # xy = self.board.choose_random_move(self.queue, *angles)
        # if xy is not None:
        #     x, y = xy
        #     return x, y
        #
        # # Занимаем центр, если он свободен
        # if self.board.empty(1, 1):
        #     return 1, 1
        #
        # # Занимаем одну из боковых клеток
        # xy = self.board.choose_random_move(self.queue, (1, 0), (0, 1), (2, 1), (1, 2))
        # if xy is not None:
        #     x, y, = xy
        #     return x, y

from typing import List
from bot_types import User, Game
from util import RoomUserStatus, Rooms, InlineButtons, make_inline_keyboard_from_board, ReplyKeyboardButtons, \
    InlineKeyboards, Icons, ReplyKeyboards

games: List[Game] = []


async def user_to_room(user, room):
    """Фунция перехода по комнатам (состояниям)"""
    user.room = room
    user.state = RoomUserStatus.Entered
    user.callback_data = None
    user.message = None
    user.button = None
    user.callback_data = None
    await rooms(user)


async def rooms(user: User):
    """ Обработка состояний пользователя """
    async def user_to(room):
        await user_to_room(user, room)

    if user.room is None:
        await user_to(Rooms.Start)

    # Стартовая комната с приветствием
    elif user.room == Rooms.Start:
        await user.show_control_message(
            'Добро пожаловать в игру "Крестики-Нолики"!',
            keyboard=ReplyKeyboards.Cancel,
            breaking=True)
        await user_to(Rooms.MenuSingleMultiPlayer)

    elif user.button == ReplyKeyboardButtons.Cancel:
        # Глобальная кнопка возврата в меню
        game = user.game
        if game is not None:
            user1, user2 = user.game.players_queue.values()
            if user1 == user:
                partner = user2
            else:
                partner = user1
            if partner != 'pc':
                game.winner = partner.game_queue
                await user_to_room(partner, Rooms.GameFinish)
            else:
                game.winner = -1
            return await user_to(Rooms.GameFinish)
        return await user_to(Rooms.MenuSingleMultiPlayer)

    # Комната настройки размера поля
    elif user.room == Rooms.MenuSetBoardScale:
        # Ветка для обработки события входа в комнату
        if user.state == RoomUserStatus.Entered:
            await user.show_control_message(
                'Создание игры. Размер поля.',
                'Выберите величину поля:',
                InlineKeyboards.SetBoardScale)
        # Ветка обработки нажатий InlineButton кнопок в комнате
        elif user.state == RoomUserStatus.PressedInlineButton:
            if user.button == InlineButtons.SetScaleCount3:
                user.board_scale = 3
            elif user.button == InlineButtons.SetScaleCount4:
                user.board_scale = 4
            elif user.button == InlineButtons.SetScaleCount5:
                user.board_scale = 5
            elif user.button == InlineButtons.SetScaleCount6:
                user.board_scale = 6
            await user_to(Rooms.MenuSingleMultiPlayer)

    # Комната выбора одиночной или многопользовательской игры
    elif user.room == Rooms.MenuSingleMultiPlayer:

        if user.state == RoomUserStatus.Entered:
            await user.show_control_message(
                'Выберите режим игры:',
                'Можно начать играть с компьютером или сделать игру доступной для подключения и дождаться соперника',
                InlineKeyboards.SingleMultiPlayer,
                Icons.Lamp)

        elif user.state == RoomUserStatus.PressedInlineButton:

            if user.button == InlineButtons.SinglePlayer:
                games.append(Game(user, user.board_scale))
                user.game.start_with_pc()
                await user_to(Rooms.GameSinglePlayer)

            if user.button == InlineButtons.MultiPlayer:
                # Поиск уже созданной и готовой для подключения игры
                for g in games:
                    if g.waiting_partner:
                        g.start_with_user(user)
                        await user_to_room(g.creator, Rooms.GameMultiPlayer)
                        return await user_to(Rooms.GameMultiPlayer)

                # При отсутствии таковой инициализируется новая игра
                games.append(Game(user, user.board_scale))
                user.game.start_waiting_partner()
                await user_to(Rooms.WaitingPartner)

            if user.button == InlineButtons.SetupBoardScale:
                await user_to(Rooms.MenuSetBoardScale)

    # Комната одиночной игры
    elif user.room == Rooms.GameSinglePlayer:

        if user.state == RoomUserStatus.Entered:
            await user.show_control_message(
                f'Ход #{user.game.step_number}',
                f'Знак игрока: {user.game.user_symbol(user)}',
                make_inline_keyboard_from_board(user.game.board))

        elif user.state == RoomUserStatus.PressedInlineButton:
            if str(user.callback_data).startswith('board'):
                game = user.game
                board, x, y = user.callback_data.split('_')
                x = int(x)
                y = int(y)
                if game.board.empty(x, y):
                    winner = game.step(x, y)
                    if winner is not None:
                        return await user_to(Rooms.GameFinish)

                    winner = game.step_auto()
                    if winner is not None:
                        return await user_to(Rooms.GameFinish)

                    await user_to(Rooms.GameSinglePlayer)

    # Комната завершеня игры
    elif user.room == Rooms.GameFinish:
        if user.state == RoomUserStatus.Entered:
            game = user.game
            # Если игра завершена с победой
            if user.game_queue == game.winner:
                title = 'Победа'
                icon = Icons.Cup
                text = 'Поздравляем, вы выйграли!' if game.game_over else 'Противник сдался.'
            # Если ничья
            elif game.winner == 0:
                title = 'Ничья'
                icon = Icons.OK
                text = 'Победила дружба.'
            # Если поражение
            else:
                title = 'Поражение.'
                icon = Icons.Shrugging
                text = 'Повезет в следующий раз!' if game.game_over \
                    else 'Вы отключлись от игры.'

            await user.show_control_message(
                title,
                text,
                make_inline_keyboard_from_board(user.game.board),
                icon=icon,
                breaking=True)

            if game in games:
                games.remove(game)

            user.game = None
            await user_to(Rooms.MenuSingleMultiPlayer)

    # Комната ождания соперника
    elif user.room == Rooms.WaitingPartner:

        if user.state == RoomUserStatus.Entered:
            await user.show_control_message('Ожидание соперника..', 'Дождитесь подключения соперника..',
                                            InlineKeyboards.Cancel, Icons.Wait)

        elif user.state == RoomUserStatus.PressedInlineButton:
            if user.button == InlineButtons.Cancel:
                games.remove(user.game)
                user.game = None
                await user_to(Rooms.MenuSetBoardScale)

    # Комната многопользовательской игры
    elif user.room == Rooms.GameMultiPlayer:
        if user.state == RoomUserStatus.Entered:
            game = user.game
            if game.queue == user.game_queue:
                # Если сейчас его ход:
                await user.show_control_message(f'Ваш ход.. ',
                                                f'Ход #{game.step_number}\n'
                                                f'Ваш знак: {game.user_symbol(user)}\n\nВаша очередь..',
                                                make_inline_keyboard_from_board(user.game.board), Icons.Baloon)
            else:
                # Если сейчас ходит противник:
                await user.show_control_message(f'Ход соперника..',
                                                f'Ход #{game.step_number}\n'
                                                f'Ваш знак: {game.user_symbol(user)}\n\nСоперник ходит..',
                                                make_inline_keyboard_from_board(user.game.board), Icons.Wait)

        elif user.state == RoomUserStatus.PressedInlineButton:

            if str(user.callback_data).startswith('board') and user.game.queue == user.game_queue:
                board, x, y = user.callback_data.split('_')
                x = int(x)
                y = int(y)
                user1, user2 = user.game.players_queue.values()
                if user1 == user:
                    partner = user2
                else:
                    partner = user1
                if user.game.board.empty(x, y):
                    winner = user.game.step(int(x), int(y))
                    if winner is not None:
                        await user_to_room(partner, Rooms.GameFinish)
                        return await user_to(Rooms.GameFinish)
                    await user_to(Rooms.GameMultiPlayer)
                    return await user_to_room(partner, Rooms.GameMultiPlayer)

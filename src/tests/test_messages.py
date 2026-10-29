from pyrusgeom.angle_deg import AngleDeg
from pyrusgeom.vector_2d import Vector2D

from lib.messenger.ball_goalie_messenger import BallGoalieMessenger
from lib.messenger.ball_messenger import BallMessenger
from lib.messenger.ball_player_messenger import BallPlayerMessenger
from lib.messenger.converters import MessengerConverter
from lib.messenger.goalie_messenger import GoalieMessenger
from lib.messenger.goalie_player_messenger import GoaliePlayerMessenger
from lib.messenger.messenger_memory import MessengerMemory
from lib.messenger.one_player_messenger import OnePlayerMessenger
from lib.messenger.recovery_message import RecoveryMessenger
from lib.messenger.stamina_messenger import StaminaMessenger
from lib.messenger.three_player_messenger import ThreePlayerMessenger
from lib.messenger.two_player_messenger import TwoPlayerMessenger
from lib.player.action_effector import ActionEffector
from lib.messenger.messenger import Messenger
from lib.player.world_model import WorldModel
from lib.rcsc.game_time import GameTime


def test_decode_player_pos_and_ball():
    wm_sender = WorldModel('sender')
    wm_reciever = WorldModel('reciever')

    wm_reciever._time = GameTime(10, 0)
    wm_reciever._messenger_memory._time = GameTime(10)
    wm_reciever._messenger_memory._ball_time = GameTime(10)
    wm_reciever._messenger_memory._player_time = GameTime(10)

    msg = Messenger.encode_all([BallPlayerMessenger(Vector2D(3, 4), Vector2D(2, -2), 5, Vector2D(10, 20), AngleDeg(0))])
    Messenger.decode_all(wm_reciever._messenger_memory, msg, 4, wm_reciever.time())
    wm_reciever.update_ball_by_hear(ActionEffector())
    wm_reciever.update_players_by_hear()

    assert abs(wm_reciever._ball.pos().x() - 3) < 0.5
    assert abs(wm_reciever._ball.pos().y() - 4) < 0.5


def test_converter_roundtrip():
    cc = MessengerConverter(7, [(-52.5, 52.5, 2 ** 10), (-34, 34, 2 ** 9), (-2.7, 2.7, 2 ** 6), (-2.7, 2.7, 2 ** 6)])
    w = cc.convert_to_word([3, 4, 2, -2])
    v = cc.convert_to_values(w)
    for expected, got in zip([3, 4, 2, -2], v):
        assert abs(got - expected) < 0.5


def test_ball_player_messenger_roundtrip():
    data = [3, 4, 2, -2, 0, 10, -30, 40]
    msg = BallPlayerMessenger.CONVERTER.convert_to_word(data)
    val = BallPlayerMessenger.CONVERTER.convert_to_values(msg)
    for expected, got in zip(data, val):
        assert abs(got - expected) <= 1.0


def test_goalie_player_messenger():
    gu = 1
    gp = Vector2D(40., 12)
    gb = AngleDeg(170)
    pu = 3
    pp = Vector2D(40., 33.9)

    mm = MessengerMemory()
    msg = GoaliePlayerMessenger(gu, gp, gb, pu, pp).encode()
    Messenger.decode_all(mm, msg, 3, GameTime(10))

    assert len(mm._goalie) == 1
    assert len(mm.players()) == 1
    goalie = mm._goalie[0]
    player = mm.players()[0]
    assert abs(goalie.pos_.x() - gp.x()) < 1.0
    assert abs(goalie.pos_.y() - gp.y()) < 1.0
    assert abs(player.pos_.x() - pp.x()) < 1.0
    assert abs(player.pos_.y() - pp.y()) < 1.0


def test_two_player_stamina():
    u1 = 22
    p1 = Vector2D(-24.5, 0.6)
    u2 = 1
    p2 = Vector2D(-51.5, 2)
    stamina = 1500

    mm = MessengerMemory()
    msg = Messenger.encode_all([TwoPlayerMessenger(u1, p1, u2, p2), StaminaMessenger(stamina)])
    Messenger.decode_all(mm, msg, 3, GameTime(10))

    assert len(mm.players()) == 2
    assert len(mm._stamina) == 1


def test_one_player():
    unum = 1
    pos = Vector2D(-52., 30)
    msg = OnePlayerMessenger(unum, pos).encode()
    values = OnePlayerMessenger.CONVERTER.convert_to_values(msg[1:])
    assert values[0] == float(unum)
    assert abs(values[1] - pos.x()) < 1.0
    assert abs(values[2] - pos.y()) < 1.0


def test_two_player():
    u1 = 22
    p1 = Vector2D(-24.5, 0.6)
    u2 = 1
    p2 = Vector2D(-51.5, 2)
    msg = TwoPlayerMessenger(u1, p1, u2, p2).encode()
    values = TwoPlayerMessenger.CONVERTER.convert_to_values(msg[1:])
    assert values[0] == float(u1)
    assert values[3] == float(u2)


def test_three_player():
    u1 = 2 + 11
    p1 = Vector2D(5.441864657550282, -36.15640365877976)
    u2 = 3 + 11
    p2 = Vector2D(9.548082361799027, -37.26023761462523)
    u3 = 4 + 11
    p3 = Vector2D(12.174446180516131, -10.985076789602786)
    msg = ThreePlayerMessenger(u1, p1, u2, p2, u3, p3).encode()
    values = ThreePlayerMessenger.CONVERTER.convert_to_values(msg[1:])
    assert values[0] == float(u1)
    assert values[3] == float(u2)
    assert values[6] == float(u3)


def test_goalie_messenger():
    gu = 1
    gp = Vector2D(40., 12)
    gb = AngleDeg(170)
    msg = GoalieMessenger(gu, gp, gb).encode()
    values = GoalieMessenger.CONVERTER.convert_to_values(msg[1:])
    assert len(values) == 3
    assert abs(values[0] - gp.x()) < 2.0  # pos del portero (rango 37..53)


def test_ball_goalie_messenger():
    bp = Vector2D(12, 30)
    bv = Vector2D(1, -1)
    gp = Vector2D(40., 33.9)
    gb = AngleDeg(170)
    msg = BallGoalieMessenger(bp, bv, gp, gb).encode()
    values = BallGoalieMessenger.CONVERTER.convert_to_values(msg[1:])
    assert abs(values[0] - bp.x()) < 1.0
    assert abs(values[1] - bp.y()) < 1.0


def test_ball_messenger():
    bp = Vector2D(12, 30)
    bv = Vector2D(1, -1)
    msg = BallMessenger(bp, bv).encode()
    values = BallMessenger.CONVERTER.convert_to_values(msg[1:])
    assert abs(values[0] - bp.x()) < 1.0
    assert abs(values[1] - bp.y()) < 1.0


def test_ball_player_messenger():
    bp = Vector2D(0, 0)
    bv = Vector2D(0, 0)
    pu = 10
    pp = Vector2D(-9.15, 10.5)
    pb = AngleDeg(2.1)
    msg = BallPlayerMessenger(bp, bv, pu, pp, pb).encode()
    values = BallPlayerMessenger.CONVERTER.convert_to_values(msg[1:])
    assert values[4] == float(pu)
    assert abs(values[5] - pp.x()) < 1.0
    assert abs(values[6] - pp.y()) < 1.0


def test_goalie_player_messenger_values():
    gu = 1
    gp = Vector2D(40., 12)
    gb = AngleDeg(170)
    pu = 3
    pp = Vector2D(40., 33.9)
    msg = GoaliePlayerMessenger(gu, gp, gb, pu, pp).encode()
    values = GoaliePlayerMessenger.CONVERTER.convert_to_values(msg[1:])
    assert values[3] == float(pu)


def test_recovery_messenger():
    recovery = 0.99
    msg = RecoveryMessenger(recovery).encode()
    values = RecoveryMessenger.CONVERTER.convert_to_values(msg[1:])
    assert abs(values[0] - recovery) < 0.01


def test_stamina_messenger():
    stamina = 5000
    msg = StaminaMessenger(stamina).encode()
    values = StaminaMessenger.CONVERTER.convert_to_values(msg[1:])
    assert abs(values[0] - stamina) < 100


if __name__ == "__main__":
    for name in list(globals()):
        if name.startswith("test_"):
            globals()[name]()
            print(name, "OK")
    print("test_messages OK")
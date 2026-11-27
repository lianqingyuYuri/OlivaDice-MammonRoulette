# -*- encoding: utf-8 -*-
"""Core/base.py 的纯逻辑单元测试。"""

import pytest

from MammonRoulette.Core.base import (
    BaseBot,
    BaseEffect,
    BaseMode,
    BaseProp,
    BotAction,
    GameState,
    Moment,
    PlayerView,
)


def test_moment_values():
    assert [m.value for m in Moment] == ["reload", "shoot", "damage", "dead", "done", "switch"]


def test_base_classes_have_empty_defaults():
    assert BaseMode.name == ""
    assert BaseProp.name == ""
    assert BaseEffect.name == ""
    assert BaseBot.name == ""
    assert BaseMode.try_over(None) is False
    assert BaseProp.apply(None, None) is False
    assert BaseProp.can_use(None, None) is True
    assert BaseEffect.apply(None, None, 0) is False
    with pytest.raises(NotImplementedError):
        BaseBot.decide(None, None, {})


def test_base_class_pass_through_methods():
    BaseMode.start(None)
    BaseMode.join(None, None)
    BaseMode.reload(None)
    BaseMode.shoot(None)
    BaseMode.damage(None)
    BaseMode.dead(None)
    BaseMode.done(None)
    BaseMode.switch(None)
    BaseProp.on_moment(None, None)
    BaseProp.on_unregister(None, None)
    BaseProp.sustain(None, None)
    BaseEffect.init()
    BaseEffect.init_after()
    BaseEffect.on_moment(None, None, None, None)
    BaseEffect.on_unregister(None)
    BaseBot.init()
    BaseBot.init_after()
    BaseBot.load()
    BaseBot.save()


def test_player_view_defaults():
    view = PlayerView()
    assert view.id == ""
    assert view.props == ()
    assert view.is_shooter is False
    assert view.is_dead is False


def test_game_state_to_vector_includes_mode_and_players():
    state = GameState(
        pl_self=PlayerView(id="p1", hp=3, actions=1, is_shooter=True),
        mode_name="经典",
        players=(
            PlayerView(id="p1", hp=3, actions=1, props=("锯子",), effects=(("束缚", 1),), is_shooter=True),
        ),
        props_event=({"name": "锯子", "stacks": 2, "user_id": "p1"},),
        shooter="p1",
        order=("p1",),
        player_count=1,
        alive_count=1,
        ammo_live=1,
        ammo_blank=1,
        ammo_total=2,
        ammo_visible=True,
        bullet=1,
        bullet_visible=True,
        dmg=1,
    )
    vector = state.to_vector()
    assert isinstance(vector, tuple)
    assert vector[0] == 1  # dmg
    assert vector[7] == 1  # player_count
    assert vector[8] == 1  # alive_count


def test_bot_action_factories():
    assert BotAction.shoot().type == "shoot"
    assert BotAction.shoot().target == ""
    assert BotAction.shoot("u2").target == "u2"
    assert BotAction.use_prop("锯子", 3).prop == "锯子"
    assert BotAction.use_prop("锯子", 3).target == "3"
    assert BotAction.shoot(memory={"k": 1}).memory == {"k": 1}
    assert not hasattr(BotAction, "SKIP")
    assert not hasattr(BotAction, "skip")

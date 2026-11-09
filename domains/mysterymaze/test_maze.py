"""The maze's grounding, as tests (LESSONS_LEARNED.md, section 1): what each push does is force on an object; every reading is a doing;
a word's force on a wall shows the wall's type; coming into view is not a change.

    python -X utf8 -m pytest -q test_maze.py
"""
import gerundelle_path  # noqa: F401  (reference/v2 on the path)
from maze import HANGING, PRESSED, QUIET, Maze, wall_id

DOINGS = {"bearing", "free", "pressed", "blocking", "yielding", "resting", "borne", "decreasing", "increasing", "holding"}


def facing_closed_wall():
    """Seed 0 from the start, turned south: the type-b wall between (0,0) and (0,1) is in front."""
    w = Maze(0)
    w.act(("press_south", "controller", "resting"))
    w.act(None)
    e = w.wall_in_front()
    assert e is not None and e not in w.open_now
    return w, e


def test_every_reading_is_a_doing():
    w = Maze(0)
    for o, st in w.states().items():
        assert st in DOINGS or st.startswith("pointing_"), (o, st)


def test_a_word_opens_only_its_own_wall_type():
    w, e = facing_closed_wall()
    own = w.opens[w.walls[e]]
    other = next(x for x in w.opens.values() if x != own)
    w.act((f"say_{other}", "voice", "resting"))
    w.act(None)
    assert e not in w.open_now
    w.act((f"say_{own}", "voice", "resting"))
    w.act(None)
    assert e in w.open_now
    assert w.states()[wall_id(e, w.walls[e])] == "yielding"


def test_a_words_force_shows_the_walls_type():
    w, e = facing_closed_wall()
    own = w.opens[w.walls[e]]
    pot = w.potentials()
    assert pot[f"say_{own}_push:voice_resting"] == HANGING
    assert all(v == PRESSED for k, v in pot.items() if k.startswith("say_") and not k.startswith(f"say_{own}_"))
    assert all(v == QUIET for k, v in pot.items() if not k.startswith("say_"))


def test_words_are_offered_only_facing_a_closed_wall():
    w = Maze(0)   # facing a free position at the start
    assert not any(i[0].startswith("say_") for i in w.invitations())
    w, _ = facing_closed_wall()
    assert sum(1 for i in w.invitations() if i[0].startswith("say_")) == 26


def test_in_the_push_slice_only_the_thing_pushed_changes():
    w = Maze(0)
    diffs = w.act(("press_south", "controller", "resting"))
    assert diffs == ["controller_heading: pointing_east -> pointing_south"]


def test_coming_into_view_is_no_change_to_a_mind_that_notices_for_itself():
    """With Params.self_noticed the mind compares what it perceives with what it last perceived: turning away from an open wall and
    back is no change."""
    from molecules import Params
    from sov_agent import SovAgent
    from gerundelle_path import ForceMind
    w, e = facing_closed_wall()
    a = SovAgent(w, ForceMind(Params(self_noticed=True)))
    a.noticing()
    w.act((f"say_{w.opens[w.walls[e]]}", "voice", "resting"))
    w.act(None)
    w.act(("press_north", "controller", "resting"))
    w.act(None)
    w.act(("press_south", "controller", "resting"))
    assert w.act(None) == []   # the wall back in view, as it was


def test_the_maze_resets_only_after_the_cheese_is_perceived():
    w = Maze(4)
    w.pos, w.heading = (4, 3), "south"
    w.shown.update(w.view())
    w.act(("walk", "pos_4_4", w.shown["pos_4_4"]))
    w.act(None)
    w.renew()
    assert w.shown["cheese"] == "borne"   # not yet: its news is still to be perceived
    w.act(None)
    w.renew()
    assert w.pos == w.start and w.shown["cheese"] == "resting"

"""The Textual command palette."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Callable, NamedTuple, TypeAlias
from uuid import UUID, uuid4

from rich.text import Text

from . import on
from ._fuzzy import Matcher
from .app import ComposeResult
from .binding import Binding
from .message import Message
from .reactive import var
from .screen import ModalScreen
from .widgets import Input, OptionList


class CommandSourceHit(NamedTuple):
    """Holds the details of a single hit."""

    match_value: float
    """The match value of the command hit."""

    match_text: Text
    """The [rich.text.Text][`Text`] representation of the hit."""

    command_text: str
    """The command text associated with the hit."""


HitsAdder: TypeAlias = Callable[[list[CommandSourceHit]], None]
"""The type of a call back for registering hits."""


class CommandSource:
    """Base class for command palette command sources."""

    @dataclass
    class Hits(Message):
        """Message sent by a command source to pass on some hits."""

        request_id: UUID
        """The ID of the request."""

        hits: list[CommandSourceHit]
        """A list of hits."""

    def command_hunt(self, user_input: str, add_hits: HitsAdder) -> None:
        """A request to hunt for commands relevant to the given user input.

        Args:
            user_input: The user input to be matched.
            add_hits: The function to call to add the hits.
        """


class TotallyFakeCommandSource(CommandSource):
    """Really, this isn't going to be the UI. Not even close."""

    DATA = """\
A bird in the hand is worth two in the bush.
A chain is only as strong as its weakest link.
A fool and his money are soon parted.
A man's reach should exceed his grasp.
A picture is worth a thousand words.
A stitch in time saves nine.
Absence makes the heart grow fonder.
Actions speak louder than words.
Although never is often better than *right* now.
Although practicality beats purity.
Although that way may not be obvious at first unless you're Dutch.
Anything is possible.
Be grateful for what you have.
Be kind to yourself and to others.
Be open to new experiences.
Be the change you want to see in the world.
Beautiful is better than ugly.
Believe in yourself.
Better late than never.
Complex is better than complicated.
Curiosity killed the cat.
Don't judge a book by its cover.
Don't put all your eggs in one basket.
Enjoy the ride.
Errors should never pass silently.
Explicit is better than implicit.
Flat is better than nested.
Follow your dreams.
Follow your heart.
Forgive yourself and others.
Fortune favors the bold.
He who hesitates is lost.
If the implementation is easy to explain, it may be a good idea.
If the implementation is hard to explain, it's a bad idea.
If wishes were horses, beggars would ride.
If you can't beat them, join them.
If you can't do it right, don't do it at all.
If you don't like something, change it. If you can't change it, change your attitude.
If you want something you've never had, you have to do something you've never done.
In the face of ambiguity, refuse the temptation to guess.
It's better to have loved and lost than to have never loved at all.
It's not over until the fat lady sings.
Knowledge is power.
Let go of the past and focus on the present.
Life is a journey, not a destination.
Live each day to the fullest.
Live your dreams.
Look before you leap.
Make a difference.
Make the most of every moment.
Namespaces are one honking great idea -- let's do more of those!
Never give up.
Never say never.
No man is an island.
No pain, no gain.
Now is better than never.
One for all and all for one.
One man's trash is another man's treasure.
Readability counts.
Silence is golden.
Simple is better than complex.
Sparse is better than dense.
Special cases aren't special enough to break the rules.
The answer is always in the last place you look.
The best defense is a good offense.
The best is yet to come.
The best way to predict the future is to create it.
The early bird gets the worm.
The exception proves the rule.
The future belongs to those who believe in the beauty of their dreams.
The future is not an inheritance, it is an opportunity and an obligation.
The grass is always greener on the other side.
The journey is the destination.
The journey of a thousand miles begins with a single step.
The more things change, the more they stay the same.
The only person you are destined to become is the person you decide to be.
The only way to do great work is to love what you do.
The past is a foreign country, they do things differently there.
The pen is mightier than the sword.
The road to hell is paved with good intentions.
The sky is the limit.
The squeaky wheel gets the grease.
The whole is greater than the sum of its parts.
The world is a beautiful place, don't be afraid to explore it.
The world is your oyster.
There is always something to be grateful for.
There should be one-- and preferably only one --obvious way to do it.
There's no such thing as a free lunch.
Too many cooks spoil the broth.
United we stand, divided we fall.
Unless explicitly silenced.
We are all in this together.
What doesn't kill you makes you stronger.
When in doubt, consult a chicken.
You are the master of your own destiny.
You can't have your cake and eat it too.
You can't teach an old dog new tricks.
    """.strip().splitlines()

    def command_hunt(self, user_input: str, add_hits: HitsAdder) -> None:
        """A request to hunt for commands relevant to the given user input.

        Args:
            user_input: The user input to be matched.
            add_hits: The function to call to add the hits.
        """
        matcher = Matcher(user_input)
        add_hits(
            [
                CommandSourceHit(
                    matcher.match(candidate), matcher.highlight(candidate), candidate
                )
                for candidate in self.DATA
                if matcher.match(candidate)
            ]
        )


class CommandList(OptionList, can_focus=False):
    """The command palette command list."""

    DEFAULT_CSS = """
    CommandList {
        visibility: hidden;
        max-height: 70%;
        border: blank;
    }

    CommandList:focus {
        border: blank;
    }

    CommandList.--visible {
        visibility: visible;
    }

    CommandList > .option-list--option-highlighted {
        background: $accent;
    }
    """


class CommandInput(Input):
    """The command palette input control."""

    DEFAULT_CSS = """
    CommandInput {
        margin-top: 3;
        border: blank;
    }

    CommandInput:focus {
        border: blank;
    }
    """


class CommandPalette(ModalScreen[None], inherit_css=False):
    """The Textual command palette."""

    DEFAULT_CSS = """
    CommandPalette {
        background: $background 30%;
        align-horizontal: center;
    }

    CommandPalette > * {
        width: 90%;
    }
    """

    BINDINGS = [
        Binding("escape", "escape", "Exit the command palette"),
        Binding("down", "command('cursor_down')", show=False),
        Binding("pagedown", "command('page_down')", show=False),
        Binding("pageup", "command('page_up')", show=False),
        Binding("up", "command('cursor_up')", show=False),
        Binding("enter", "command('select'),", show=False, priority=True),
    ]

    placeholder: var[str] = var("Textual spotlight search", init=False)
    """The placeholder text for the command palette input."""

    _list_visible: var[bool] = var(False, init=False)
    """Internal reactive to toggle the visibility of the command list."""

    def __init__(self) -> None:
        super().__init__()
        self._current_request: UUID = uuid4()

    def compose(self) -> ComposeResult:
        """Compose the command palette."""
        yield CommandInput(placeholder=self.placeholder)
        yield CommandList()

    def _watch_placeholder(self) -> None:
        """Pass the new placeholder text down to the `CommandInput`."""
        self.query_one(CommandInput).placeholder = self.placeholder

    def _watch__list_visible(self) -> None:
        """React to the list visible flag being toggled."""
        self.query_one(CommandList).set_class(self._list_visible, "--visible")

    def _process_hits(self, request_id: UUID, hits: list[CommandSourceHit]) -> None:
        """Process incoming hits.

        Args:
            request_id: The ID of the request that resulted in these hits.
            hits: The list of hits.
        """
        if request_id == self._current_request:
            self.query_one(CommandList).add_options([prompt for (_, prompt, _) in hits])

    @on(Input.Changed)
    def _input(self, event: Input.Changed) -> None:
        """React to input in the command palette.

        Args:
            event: The input event.
        """
        search_value = event.value.strip()
        self._list_visible = bool(search_value)
        command_list = self.query_one(CommandList)
        command_list.clear_options()
        if search_value:
            self._current_request = uuid4()
            TotallyFakeCommandSource().command_hunt(
                search_value, partial(self._process_hits, self._current_request)
            )

    @on(OptionList.OptionSelected)
    def _select_command(self, event: OptionList.OptionSelected) -> None:
        """React to a command being selected from the dropdown.

        Args:
            event: The option selection event.
        """
        event.stop()
        input = self.query_one(CommandInput)
        with self.prevent(Input.Changed):
            input.value = str(event.option.prompt)
        input.action_end()
        self._list_visible = False

    def _action_escape(self) -> None:
        """Handle a request to escape out of the command palette."""
        self.dismiss()

    def _action_command(self, action: str) -> None:
        """Pass an action on to the `CommandList`.

        Args:
            action: The action to pass on to the `CommandList`.
        """
        try:
            command_action = getattr(self.query_one(CommandList), f"action_{action}")
        except AttributeError:
            return
        command_action()

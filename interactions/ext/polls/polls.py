from inspect import iscoroutinefunction
from logging import Logger, getLogger
from random import randint
from typing import Callable, Coroutine, Dict, List, Optional, Union
from interactions import Client, ComponentContext, CommandContext, Embed, SelectMenu
import interactions

from .exceptions import NotEnoughChoices, TooManyChoices

NUMBER_EMOJIS = [
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
]
END_POLL_EMOJI = "🔴"
log: Logger = getLogger("polls")


class Poll:
    def __init__(
        self,
        client: Client,
        title: str,
        choices: Optional[List[str]] = None,
        func_after_vote: Optional[Union[Callable, Coroutine]] = None,
        owner_id: Optional[int] = None
    ) -> None:
        self.client = client
        self.title = title
        self.func_after_vote = func_after_vote
        self.owner_id = owner_id

        self.votes: Dict[int, int] = {}
        self.choices = choices or []
        if len(self.choices) > len(NUMBER_EMOJIS):
            raise TooManyChoices

        self.id = randint(0, 999_999_999)
        log.info(f"Poll #{self.id} - Created with title: {self.title}")
        for choice in self.choices:
            log.info(f"Poll #{self.id} - Choice added: {choice}")

    def add_choice(self, choice: str):
        if len(self.choices) >= len(NUMBER_EMOJIS):
            raise TooManyChoices
        self.choices.append(choice)
        log.info(f"Poll #{self.id} - Choice added: {choice}")

    async def show(self, ctx: Union[CommandContext, ComponentContext]):
        if len(self.choices) < 2:
            raise NotEnoughChoices

        select_menu = SelectMenu(
            custom_id=f"polls_{self.id}",
            options=[interactions.SelectOption(
                label=choice,
                value=f"polls_{self.id}_{i}",
                emoji={"name": NUMBER_EMOJIS[i]}
            ) for i, choice in enumerate(self.choices)],
            placeholder=self.title
        )

        channel = await ctx.get_channel()
        self.message = await channel.send(embeds=await self.__create_embed(), components=select_menu)
        await ctx.send(embeds=Embed(
            title="",
            description=f"Your poll named `{self.title}` has successfully been created. React to it with {END_POLL_EMOJI} to close the poll!"
        ), ephemeral=True)
        self.client.component(select_menu)(self.__on_poll_select)
        self.client.event(self.on_message_reaction_add)
        log.info(f"Poll #{self.id} - Shown in channel #{ctx.channel_id}")

    async def __on_poll_select(self, ctx: interactions.ComponentContext, options: List[str]):
        _, _, option = options[0].split('_')  # TODO: Add support for multiple options to be selected
        option = int(option)
        voter_id: int = int(ctx.author.id)

        self.votes[voter_id] = option
        self.message = await self.message.edit(embeds=await self.__create_embed())
        await self.__run_function(self.func_after_vote, ctx, voter_id, option)

    async def __run_function(self, func, *args):
        if func is not None:
            if iscoroutinefunction(func):
                return await func(self, *args)
            else:
                return func(self, *args)

    async def __create_embed(self) -> Embed:
        # Create list of percentages for each choice
        votes = [0 for _ in self.choices]
        for option in self.votes.values():
            votes[option] += 1

        num_votes = len(self.votes)
        if num_votes == 0:
            percentages = [0 for _ in range(len(votes))]
        else:
            percentages = [vote / num_votes for vote in votes]

        # Create a bar to represent the percentage visually
        bars = []
        for percentage in percentages:
            num: int = round(percentage * 10)
            bars.append("█" * num)

        # Create embed to send and return
        embed = interactions.Embed(
            title=self.title
        )
        for i, choice in enumerate(self.choices):
            embed.add_field(
                name=f"{NUMBER_EMOJIS[i]} {choice}",
                value=f"{bars[i]} **{round(percentages[i] * 100)}%** ({votes[i]})",
                inline=False
            )
        return embed

    async def on_message_reaction_add(self, message_reaction: interactions.MessageReaction):
        if message_reaction.emoji.name != END_POLL_EMOJI:
            return

        if int(message_reaction.message_id) != int(self.message.id):
            return

        if self.owner_id:
            if int(message_reaction.user_id) != self.owner_id:
                return
        else:
            return  # TODO: Check if a user has the MANAGE_CHANNELS permission in the given channel

        embed: interactions.Embed = self.message.embeds[0]
        embed.set_footer(text="Poll closed.")
        await self.message.edit(embeds=embed, components=[])
        await self.message.remove_reaction_from(END_POLL_EMOJI, int(message_reaction.user_id))

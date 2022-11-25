import logging
import re
from datetime import datetime

import discord
from discord import ApplicationContext
from discord.channel import TextChannel
from discord.commands import option
from discord.ext import commands, tasks

from ilo.bot import Ilo
from ilo.ui import TranslationApprovalView, TranslationCogSubmitModal

LEARNING_SERVER = 969386329513295872
CHALLENGE_CHANNEL = 1014694309557186600
APPROVAL_CHANNEL = 1026141020993368116
CHALLENGER_ROLE = 1014695304605470811
TEACHER_ROLE = 969795956264554537

CHALLENGE_NUMBER_RE = re.compile(r"\d+")

LOG = logging.getLogger()


async def _post_translation_challenge(bot: Ilo):
    # TODO: get server from db
    guild = bot.get_guild(LEARNING_SERVER)
    assert guild
    channel = guild.get_channel(CHALLENGE_CHANNEL)
    assert channel and isinstance(channel, TextChannel)
    role = guild.get_role(CHALLENGER_ROLE)
    assert role

    sentence = bot.db.get_use_challenge(LEARNING_SERVER)
    assert sentence

    challenge_number = sentence.challenge_number

    msg = await channel.send(
        f"__**Biweekly Translation Challenge {challenge_number}**__\n\n"
        f"{role.mention} Translate this sentence into toki pona!\n"
        f"> {sentence.sentence}\n\n"
        f"Discuss in the thread below. **Spoiler your answers!**",
        allowed_mentions=discord.AllowedMentions(roles=[role]),
    )
    await msg.create_thread(name=f"Challenge {challenge_number}")


class TranslationCog(commands.Cog):
    def __init__(self, bot: Ilo):
        self.bot = bot
        self.post_translation_challenge.start()

    @commands.guild_only()
    @commands.slash_command(
        name="submit", description="Submit a sentence to the translation challenge!"
    )
    async def submit(self, ctx: ApplicationContext):
        modal = TranslationCogSubmitModal(title="Sentence submission")

        # Send the prompt for the sentence
        await ctx.send_modal(modal)
        await modal.wait()

        submission = modal.children[0].value
        assert submission
        cleaned = submission.replace("\n", " ")
        assert ctx.user
        channel = self.bot.get_channel(APPROVAL_CHANNEL)
        assert channel and isinstance(channel, TextChannel)
        resp = await channel.send(
            content=f"{ctx.user.mention} li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {cleaned}\n"
            "*ni li pona ala pona tawa sina?*",
            view=TranslationApprovalView(self.bot.db),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        assert resp
        assert ctx.guild
        self.bot.db.add_sentence(
            server_id=ctx.guild.id,
            user_id=ctx.user.id,
            approval_msg_id=resp.id,
            sentence=cleaned,
        )

    @commands.has_role(TEACHER_ROLE)  # TODO: get role from DB
    @commands.message_command(name="Approve a sentence suggestion")
    async def approve(self, ctx: ApplicationContext, message: discord.Message):
        sentence = self.bot.db.set_sentence_approval(message.id, False)
        assert sentence
        assert ctx.user
        await message.edit(
            content=f"<@{sentence.user_id}> li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            f"*toki ni li **pona** tawa {ctx.user.mention}. toki li ken lon.*"
        )

        await ctx.respond(content="toki ni li kama pona!", ephemeral=True)

    @commands.has_role(TEACHER_ROLE)  # TODO: get from DB
    @commands.message_command(name="Deny a sentence suggestion")
    async def deny(self, ctx: ApplicationContext, message: discord.Message):
        sentence = self.bot.db.set_sentence_approval(message.id, False)
        assert sentence
        assert ctx.user
        await message.edit(
            content=f"<@{sentence.user_id}> li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            f"*toki ni li **ike** tawa {ctx.user.mention}. toki li ken **ala** lon.*"
        )

        await ctx.respond(content="toki ni li kama ike!", ephemeral=True)

    @tasks.loop(minutes=1)
    async def post_translation_challenge(self):
        time = datetime.utcnow()
        # race condition: bot can finish init of this cog before login
        # if the time is right, posting will fail
        if time.weekday() == 2 or time.weekday() == 5:
            if time.hour == 18 and time.minute == 0:
                await _post_translation_challenge(self.bot)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.slash_command(name="config")
    @option("challenge_channel", description="Where to send challenges", required=False)
    @option(
        "approval_channel", description="Where to send new sentences", required=False
    )
    @option(
        "challenger_role", description="Role to ping for challenges", required=False
    )
    @option(
        "approver_role", description="Role that may approve sentences", required=False
    )
    @option("challenge_number", description="Last challenge number", required=False)
    async def configure_bot(
        self,
        ctx: ApplicationContext,
        challenge_channel: discord.TextChannel,
        approval_channel: discord.TextChannel,
        challenger_role: discord.Role,
        approver_role: discord.Role,
        challenge_number: int,
    ):
        assert ctx.guild_id
        self.bot.db.configure_server(
            ctx.guild_id,
            challenge_channel.id,
            approval_channel.id,
            challenger_role.id,
            approver_role.id,
            challenge_number,
        )
        await ctx.respond(content="Configured your server!", ephemeral=True)

    @commands.is_owner()
    @commands.slash_command(name="start_challenge")
    async def start_challenge(self, ctx: ApplicationContext):
        await _post_translation_challenge(self.bot)
        await ctx.respond(content="Sent a challenge!", ephemeral=True)


def setup(bot: Ilo):
    bot.add_cog(TranslationCog(bot))

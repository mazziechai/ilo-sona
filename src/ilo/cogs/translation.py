import logging
from datetime import datetime

import discord
from discord import ApplicationContext
from discord.channel import TextChannel
from discord.ext import commands, tasks

from ilo.bot import Ilo
from ilo.db import Challenges, Sentences
from ilo.ui import TranslationCogSubmitModal, TranslationVerificationView

LEARNING_SERVER = 969386329513295872
CHALLENGE_CHANNEL = 1014694309557186600
APPROVAL_CHANNEL = 1026141020993368116
CHALLENGER_ROLE = 1014695304605470811
TEACHER_ROLE = 969795956264554537

LOG = logging.getLogger()


async def _post_translation_challenge(bot: Ilo):
    guild = bot.get_guild(LEARNING_SERVER)
    assert guild
    channel = guild.get_channel(CHALLENGE_CHANNEL)
    assert channel and isinstance(channel, TextChannel)
    role = guild.get_role(CHALLENGER_ROLE)
    assert role

    # Since getting a random document returns a pymongo command cursor, we have to use
    # list comprehension to get the document from it, then we need to get the document id
    # specifically so we can pull the document and embed it in the challenge
    sentence_id = [i["_id"] for i in Sentences.objects(used=False, verified=True).aggregate([{"$sample": {"size": 1}}])].pop()  # type: ignore
    sentence = Sentences.objects(id=sentence_id).first()  # type: ignore
    assert sentence

    challenge_number = Challenges.objects.count() + 1  # type: ignore
    challenge = Challenges(number=challenge_number, sentence=sentence).save()

    msg = await channel.send(
        f"__**Biweekly Translation Challenge {challenge_number}**__\n\n"
        f"{role.mention} Translate this sentence into toki pona!\n"
        f"> {sentence.sentence}\n\n"
        f"Discuss in the thread below. **Spoiler your answers!**",
        allowed_mentions=discord.AllowedMentions(roles=[role]),
    )
    await msg.create_thread(name=f"Challenge {challenge_number}")

    challenge.sentence.used = True
    challenge.save(cascade=True)


class TranslationCog(commands.Cog):
    def __init__(self, bot: Ilo):
        self.bot = bot
        self.post_translation_challenge.start()

    @commands.slash_command(
        name="submit", description="Submit a sentence to the translation challenge!"
    )
    async def submit(self, ctx: ApplicationContext):
        modal = TranslationCogSubmitModal(title="Sentence submission")
        assert ctx.user

        # Send the prompt for the sentence
        await ctx.send_modal(modal)
        await modal.wait()

        # Stripping new lines from the entry
        submission = modal.children[0].value
        assert submission
        submission = submission.replace("\n", " ")
        sentence = Sentences(user=ctx.user.id, sentence=submission)
        assert sentence

        channel = self.bot.get_channel(APPROVAL_CHANNEL)
        assert channel and isinstance(channel, TextChannel)
        msg = await channel.send(
            content=f"{ctx.user.mention} li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            "*ni li pona ala pona tawa sina?*",
            view=TranslationVerificationView(submission),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        assert msg
        sentence.verification_message = msg.id
        sentence.save()

    @commands.has_role(TEACHER_ROLE)
    @commands.message_command(name="Approve a sentence suggestion")
    async def approve(self, ctx: ApplicationContext, message: discord.Message):
        sentence = Sentences.objects(verification_message=message.id).first()  # type: ignore
        assert sentence
        assert ctx.user
        if sentence is None:
            await ctx.respond(
                content="That is not a sentence suggestion!", ephemeral=True
            )

        sentence.verified = True
        sentence.save()

        await message.edit(
            content=f"<@{sentence.user}> li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            f"*toki ni li **pona** tawa {ctx.user.mention}. toki li ken lon.*"
        )

        await ctx.respond(content="toki ni li kama pona!", ephemeral=True)

    @commands.has_role(TEACHER_ROLE)
    @commands.message_command(name="Deny a sentence suggestion")
    async def deny(self, ctx: ApplicationContext, message: discord.Message):
        sentence = Sentences.objects(verification_message=message.id).first()  # type: ignore
        assert sentence
        assert ctx.user
        if sentence is None:
            await ctx.respond(
                content="That is not a sentence suggestion!", ephemeral=True
            )

        sentence.verified = False
        sentence.save()

        await message.edit(
            content=f"<@{sentence.user}> li wile pana e toki ni tawa musi pi ante toki:\n"
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

    @post_translation_challenge.after_loop
    async def translation_after_loop(self):
        pass

    @commands.is_owner()  # TODO: admins only?
    @commands.slash_command(name="start_challenge")
    async def start_challenge(self, ctx: ApplicationContext):
        await _post_translation_challenge(self.bot)
        await ctx.respond(content="Sent a challenge!", ephemeral=True)


def setup(bot: Ilo):
    bot.add_cog(TranslationCog(bot))

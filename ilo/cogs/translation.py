from datetime import datetime

import discord
from discord import ApplicationContext
from discord.ext import commands, tasks

from ..bot import Ilo
from ..db import Challenges, Sentences
from ..ui import TranslationCogSubmitModal, TranslationVerificationView


async def _post_translation_challenge(bot: Ilo):
    guild = bot.get_guild(969386329513295872)
    channel = guild.get_channel(1014694309557186600)
    role = guild.get_role(1014695304605470811)

    # Since getting a random document returns a pymongo command cursor, we have to use
    # list comprehension to get the document from it, then we need to get the document id
    # specifically so we can pull the document and embed it in the challenge
    sentence_id = [i["_id"] for i in Sentences.objects(used=False, verified=True).aggregate([{"$sample": {"size": 1}}])].pop()  # type: ignore
    sentence = Sentences.objects(id=sentence_id).first()  # type: ignore

    challenge_number = Challenges.objects.count() + 1  # type: ignore
    challenge = Challenges(number=challenge_number, sentence=sentence).save()

    msg = await channel.send(  # type: ignore
        f"__**Biweekly Translation Challenge {challenge_number}**__\n\n"
        f"{role.mention} Translate this sentence into toki pona!\n"
        f"> {sentence.sentence}\n\n"
        f"Discuss in the thread below. **Spoiler your answers!**",
        allowed_mentions=discord.AllowedMentions(roles=[role]),  # type: ignore
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

        # Send the prompt for the sentence
        await ctx.send_modal(modal)
        await modal.wait()

        # Stripping new lines from the entry
        sentence_content = modal.children[0].value.replace("\n", " ")
        sentence = Sentences(user=ctx.user.id, sentence=sentence_content)

        msg = await self.bot.get_channel(1026141020993368116).send(  # type: ignore
            content=f"{ctx.user.mention} li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            "*ni li pona ala pona tawa sina?*",
            view=TranslationVerificationView(sentence),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        sentence.verification_message = msg.id
        sentence.save()

    @commands.has_role(969795956264554537)
    @commands.message_command(name="Approve a sentence suggestion")
    async def approve(self, ctx: ApplicationContext, message: discord.Message):
        sentence = Sentences.objects(verification_message=message.id).first()  # type: ignore

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

    @commands.has_role(969795956264554537)
    @commands.message_command(name="Deny a sentence suggestion")
    async def deny(self, ctx: ApplicationContext, message: discord.Message):
        sentence = Sentences.objects(verification_message=message.id).first()  # type: ignore

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
        if time.weekday() == 2 or time.weekday() == 5:
            if time.hour == 18:
                await _post_translation_challenge(self.bot)

    @commands.check(lambda ctx: ctx.author.id == 712104395747098656)
    @commands.slash_command(name="debug")
    async def debug(self, ctx: ApplicationContext):
        await _post_translation_challenge(self.bot)
        await ctx.respond(content="I hope this worked")


def setup(bot: Ilo):
    bot.add_cog(TranslationCog(bot))

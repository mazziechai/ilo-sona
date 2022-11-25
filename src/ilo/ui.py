import logging

import discord

from ilo.db import ChallengeDB

LOG = logging.getLogger()


class TranslationCogSubmitModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_item(
            discord.ui.InputText(
                label="Your sentence here!",
                max_length=200,
                style=discord.InputTextStyle.long,
                required=True,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            content="mi pana e toki sina tawa lawa ma! lawa li wile lukin e toki sina. o awen."
            "I submitted your sentence to the overlords! Please wait for approval.",
            ephemeral=True,
        )
        self.stop()


class TranslationApprovalView(discord.ui.View):
    def __init__(self, db: ChallengeDB):
        super().__init__(timeout=None)
        self.db: ChallengeDB = db

    @discord.ui.button(label="pona", style=discord.ButtonStyle.success)
    async def pona_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        for child in self.children:
            child.disabled = True  # type: ignore

        msg = interaction.message
        assert msg
        sentence = self.db.set_sentence_approval(msg.id, True)
        assert sentence

        assert interaction.user
        await interaction.response.edit_message(
            content=f"<@{sentence.user_id}> li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            f"*toki ni li **pona** tawa {interaction.user.mention}. toki li ken lon.*",
            view=self,
        )

    @discord.ui.button(label="ike", style=discord.ButtonStyle.danger)
    async def ike_callback(
        self, _: discord.ui.Button, interaction: discord.Interaction
    ):
        for child in self.children:
            child.disabled = True  # type: ignore

        msg = interaction.message
        assert msg
        sentence = self.db.set_sentence_approval(msg.id, False)
        assert sentence

        assert interaction.user
        await interaction.response.edit_message(
            content=f"<@{sentence.user_id}> li wile pana e toki ni tawa musi pi ante toki:\n"
            f"> {sentence.sentence}\n"
            f"*toki ni li **ike** tawa {interaction.user.mention}. toki li ken **ala** lon.*",
            view=self,
        )

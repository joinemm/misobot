import discord
from discord.ext import commands
import math
import main
import asyncio

database = main.database


class SorterInstance:

    def __init__(self, sort_list):

        self.namMember = sort_list

        self.lstMember = []
        self.parent = []
        self.equal = []
        self.rec = []

        n = 0

        self.lstMember.append([])

        for i in range(len(self.namMember)):
            self.lstMember[0].append(i)

        self.parent.append(-1)
        self.totalSize = 0
        n += 1

        i = 0
        while i < len(self.lstMember):
            if len(self.lstMember[i]) >= 2:
                mid = math.ceil(len(self.lstMember[i])/2)
                self.lstMember.append(self.lstMember[i][:mid])
                self.totalSize += len(self.lstMember[n])
                self.parent.append(i)
                n += 1
                self.lstMember.append(self.lstMember[i][mid:])
                self.totalSize += len(self.lstMember[n])
                self.parent.append(i)
                n += 1
            i += 1

        for i in range(len(self.namMember)):
            self.rec.append(0)

        self.nrec = 0

        for i in range(len(self.namMember)):
            self.equal.append(-1)

        self.cmp1 = len(self.lstMember) - 2
        self.cmp2 = len(self.lstMember) - 1
        self.head1 = 0
        self.head2 = 0
        self.numQuestion = 1
        self.finishSize = 0
        self.finishFlag = 0

    def sortList(self, flag):
        if flag < 0:
            self.rec[self.nrec] = self.lstMember[self.cmp1][self.head1]
            self.head1 += 1
            self.nrec += 1
            self.finishSize += 1

            while not self.equal[self.rec[self.nrec-1]] == -1:
                self.rec[self.nrec] = self.lstMember[self.cmp1][self.head1]
                self.head1 += 1
                self.nrec += 1
                self.finishSize += 1

        elif flag > 0:
            self.rec[self.nrec] = self.lstMember[self.cmp2][self.head2]
            self.head2 += 1
            self.nrec += 1
            self.finishSize += 1

            while not self.equal[self.rec[self.nrec-1]] == -1:
                self.rec[self.nrec] = self.lstMember[self.cmp2][self.head2]
                self.head2 += 1
                self.nrec += 1
                self.finishSize += 1

        else:
            self.rec[self.nrec] = self.lstMember[self.cmp1][self.head1]
            self.head1 += 1
            self.nrec += 1
            self.finishSize += 1

            while not self.equal[self.rec[self.nrec - 1]] == -1:
                self.rec[self.nrec] = self.lstMember[self.cmp1][self.head1]
                self.head1 += 1
                self.nrec += 1
                self.finishSize += 1

            self.equal[self.rec[self.nrec-1]] = self.lstMember[self.cmp2][self.head2]
            self.rec[self.nrec] = self.lstMember[self.cmp2][self.head2]
            self.head2 += 1
            self.nrec += 1
            self.finishSize += 1

            while not self.equal[self.rec[self.nrec - 1]] == -1:
                self.rec[self.nrec] = self.lstMember[self.cmp2][self.head2]
                self.head2 += 1
                self.nrec += 1
                self.finishSize += 1

        if self.head1 < len(self.lstMember[self.cmp1]) and self.head2 == len(self.lstMember[self.cmp2]):
            while self.head1 < len(self.lstMember[self.cmp1]):
                self.rec[self.nrec] = self.lstMember[self.cmp1][self.head1]
                self.head1 += 1
                self.nrec += 1
                self.finishSize += 1

        elif self.head1 == len(self.lstMember[self.cmp1]) and self.head2 < len(self.lstMember[self.cmp2]):
            while self.head2 < len(self.lstMember[self.cmp2]):
                self.rec[self.nrec] = self.lstMember[self.cmp2][self.head2]
                self.head2 += 1
                self.nrec += 1
                self.finishSize += 1

        if self.head1 == len(self.lstMember[self.cmp1]) and self.head2 == len(self.lstMember[self.cmp2]):

            for i in range(len(self.lstMember[self.cmp1]) + len(self.lstMember[self.cmp2])):
                self.lstMember[self.parent[self.cmp1]][i] = self.rec[i]

            del self.lstMember[-1]
            del self.lstMember[-1]
            self.cmp1 = self.cmp1 - 2
            self.cmp2 = self.cmp2 - 2
            self.head1 = 0
            self.head2 = 0

            if self.head1 == 0 and self.head2 == 0:
                for i in range(len(self.namMember)):
                    self.rec[i] = 0
                self.nrec = 0

        if self.cmp1 < 0:
            self.finishFlag = 1

    def showResult(self):
        ranking = 1
        sameRank = 1

        content = discord.Embed(title="Final Ranking:")
        content.description = ""

        for i in range(len(self.namMember)):
            content.description += f"\n{ranking}. **{self.namMember[self.lstMember[0][i]]}**"

            if i < len(self.namMember)-1:
                if self.equal[self.lstMember[0][i]] == self.lstMember[0][i+1]:
                    sameRank += 1

                else:
                    ranking += sameRank
                    sameRank = 1

        return content

    def showImage(self):
        text = f"Battle #{self.numQuestion} ({math.floor(self.finishSize * 100 / self.totalSize)}% sorted"
        text2 = self.namMember[self.lstMember[self.cmp1][self.head1]]
        text3 = self.namMember[self.lstMember[self.cmp2][self.head2]]
        self.numQuestion += 1

        content = discord.Embed(title=text)
        content.description = f"**{text2}** vs **{text3}**"

        return content


class Sorter:

    def __init__(self, client):
        self.client = client
        self.instances = {}

    @commands.command()
    async def sorter(self, ctx, *args):
        """Bias sorting tool"""
        if not args:
            helpmsg = "Usage:\n" \
                      "`>sorter [name, name, etc..]`\n" \
                      "`>sorter preset [saved preset]`\n" \
                      "`>sorter save [name, name, etc..] > [name to save as]`\n" \
                      "`>sorter remove [preset name]`"
            await ctx.send(helpmsg)
            return
        if args[0] in ["preset", "presets"]:
            try:
                # use a preset
                # noinspection PyStatementEffect
                args[1]
                preset = " ".join(args[1:])
                sort_list = database.get_attr("data", f"sorter_presets.{preset}")
                if sort_list is None:
                    await ctx.send(f"ERROR: No preset named `{preset}` found")
                    return

            except IndexError:
                # list presets
                content = discord.Embed(title="Sorter Presets:")
                content.description = ""
                for x in database.get_attr("data", "sorter_presets"):
                    content.description += f"\n{x}"
                if content.description == "":
                    content.description = "No presets saved!"
                await ctx.send(embed=content)
                return

        elif args[0] == "save":
            # save preset
            text, preset = " ".join(args[1:]).split(">")
            sort_list = [x.strip() for x in text.split(",")]
            database.set_attr("data", f"sorter_presets.{preset.strip()}", sort_list)
            await ctx.send(f"Preset saved as `{preset}`")
            return

        elif args[0] == "remove":
            # remove preset
            preset = " ".join(args[1:])
            response = database.delete_attr("data", f"sorter_presets", preset)
            if response is True:
                await ctx.send(f"deleted preset `{preset}`")
            else:
                await ctx.send(f'ERROR: No preset named "{preset}" found')
            return

        else:
            sort_list = [x.strip() for x in " ".join(args).split(",")]
            if not args or len(sort_list) < 2:
                await ctx.send("Invalid list given. separate entries with a comma. minimum entries: 2")
                return

        sorter = SorterInstance(sort_list)
        content = sorter.showImage()
        msg = await ctx.send(ctx.message.author.mention, embed=content)
        self.instances[str(msg.id)] = sorter
        await msg.add_reaction("⬅")
        await msg.add_reaction("👔")
        await msg.add_reaction("➡")
        await self.run_picker(msg, ctx.message.author)

    async def run_picker(self, msg, _user):
        while self.instances[str(msg.id)].finishFlag == 0:
            try:
                reaction, user = await self.client.wait_for("reaction_add", check=lambda _reaction, _user:
                                                            reaction.emoji in ["⬅", "👔", "➡"], timeout=3600.0)
            except asyncio.TimeoutError:
                del self.instances[str(msg.id)]
                return
            else:
                if user == _user and reaction.message.id == msg.id:
                    if reaction.emoji == "⬅":
                        self.instances[str(msg.id)].sortList(-1)
                        await msg.remove_reaction("⬅", user)

                    elif reaction.emoji == "➡":
                        self.instances[str(msg.id)].sortList(1)
                        await msg.remove_reaction("➡", user)

                    elif reaction.emoji == "👔":
                        self.instances[str(msg.id)].sortList(0)
                        await msg.remove_reaction("👔", user)

                    else:
                        await msg.edit(content="this is bug idk hwat goin on")

                    if self.instances[str(msg.id)].finishFlag == 1:
                        content = self.instances[str(msg.id)].showResult()
                        await msg.clear_reactions()
                    else:
                        content = self.instances[str(msg.id)].showImage()

                    await msg.edit(embed=content)

        del self.instances[str(msg.id)]


def setup(client):
    client.add_cog(Sorter(client))

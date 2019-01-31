import asyncio


async def page_switcher(client, my_msg, content, pages):
    current_page = 0

    def check(_reaction, _user):
        return _reaction.message.id == my_msg.id and _reaction.emoji in ["⬅", "➡"] \
               and not _user == client.user

    await my_msg.add_reaction("⬅")
    await my_msg.add_reaction("➡")

    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=3600.0, check=check)
        except asyncio.TimeoutError:
            return
        else:
            try:
                if reaction.emoji == "⬅" and current_page > 0:
                    content.description = pages[current_page - 1]
                    current_page -= 1
                    await my_msg.remove_reaction("⬅", user)
                elif reaction.emoji == "➡":
                    content.description = pages[current_page + 1]
                    current_page += 1
                    await my_msg.remove_reaction("➡", user)
                else:
                    continue
                content.set_footer(text=f"page {current_page + 1} of {len(pages)}")
                await my_msg.edit(embed=content)
            except IndexError:
                continue

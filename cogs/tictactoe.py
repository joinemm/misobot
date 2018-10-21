import discord
from discord.ext import commands

class Gameinstance:

    def __init__(self):
        self.board = generate_board(3, 3)
        self.turns = 0
        self.message = None
        self.player1 = ""
        self.player2 = ""

class Tictactoe:

    def __init__(self, client):
        self.client = client
        self.games = {}

    @commands.command()
    async def start(self, ctx):
        this_game = self.games[ctx.channel.id] = Gameinstance()
        this_game.message = await ctx.send(print_board(this_game.board, this_game.player1, this_game.player2))

    @commands.command(name="p")
    async def place(self, ctx, *args):
        channel_id = ctx.channel.id
        if channel_id in self.games:
            game = self.games[channel_id]
            # game running
            # Change the mark for the player
            if game.turns % 2 == 0:
                mark = "X"
            else:
                mark = "O"
            if mark == "X" and game.player1 == "":
                # new player 1
                game.player1 = ctx.message.author
            elif mark == "O" and game.player2 == "":
                # new player 2
                game.player2 = ctx.message.author
            if ctx.message.author in [game.player1, game.player2]:
                if (ctx.message.author == game.player1 and mark == "X") or \
                        (ctx.message.author == game.player2 and mark == "O"):
                    coordinates = args[0]
                    print(coordinates)
                    try:
                        x, y = coordinates.split(",")
                        x = int(x)
                        y = int(y)

                        if game.board[y][x] == " ":
                            game.board[y][x] = mark
                        else:
                            print("Error: a mark has already been placed on this square.")
                            await ctx.send("Error: this square isn't empty", delete_after=2)
                            await ctx.message.delete()
                            return

                    except ValueError:
                        print("Error: enter two integers, separated with spaces.")
                        await ctx.send("Error: Invalid coordinates", delete_after=2)
                        await ctx.message.delete()
                        return

                    except IndexError:
                        print("Error: coordinates must be between 0 and 2.")
                        await ctx.send("Error: Invalid coordinates", delete_after=2)
                        await ctx.message.delete()
                        return

                    await game.message.edit(content=print_board(game.board, game.player1, game.player2))

                    if check_win(game.board, x, y) is not None:
                        if check_win(game.board, x, y) == "X":
                            winner = game.player1
                        else:
                            winner = game.player2
                        await ctx.send(f"Game has ended, winner is **{winner}**!")
                        del self.games[channel_id]
                        return
                    elif game.turns == 8:
                        await ctx.send("**Draw**!")
                        del self.games[channel_id]
                        return

                    game.turns += 1
                    await ctx.message.delete()
                else:
                    await ctx.send("Error: It's not your turn yet", delete_after=2)
            else:
                await ctx.send("Error: You are not one of the players", delete_after=2)
        else:
            # no game
            await ctx.send("Error: No game running on this channel")


def generate_board(width, height):
    board = []
    y = 0
    while y < height:
        x = 0
        board.append([])
        while x < width:
            board[y].insert(x, " ")
            x += 1
        y += 1
    return board


def print_board(board, p1, p2):
    message = f'```\n   0  1  2    {p1} vs {p2} | ">p x,y" to play'
    for y in range(len(board)):
        # message += f"\n {board[y][0]} | {board[y][1]} | {board[y][2]} "
        # message += "\n-----------"
        message += f"\n{y} [{board[y][0]}][{board[y][1]}][{board[y][2]}]"
    return message + "\n```"


def check_win(board, x, y):
    if board[y][0] == board[y][1] == board[y][2]:
        # row win
        if board[y][0] != " ":
            return board[y][0]
    if board[0][x] == board[1][x] == board[2][x]:
        # column win
        if board[0][x] != " ":
            return board[0][x]
    if board[0][0] == board[1][1] == board[2][2]:
        if board[0][0] != " ":
            return board[0][0]
    if board[0][2] == board[1][1] == board[2][0]:
        if board[0][2] != " ":
            return board[0][2]
    return None


def setup(client):
    client.add_cog(Tictactoe(client))

from colorsys import rgb_to_hsv
from json.decoder import JSONDecodeError
import discord, json
from discord.ext import commands

class roles(commands.Cog): # Setup bot (replace template with suitable name)
    def __init__ (self, bot):
        self.bot = bot
    class ConfigError(Exception):
        '''Error in provided config file.'''
        # TODO: Log errors in config file @logging

    try:
        config = json.load(open('Cogs/config.json', 'r')) # Load config file, and report error if necessary
    except JSONDecodeError as exception:
        config_error = bool(True)
        raise ConfigError('Unable to parse config file')

    



    #
    @commands.command()
    async def info(ctx, role : discord.role): # FIXME: role varable is not discord.Role object pls fix
        
        # role hex colour, number of users with role, role name, creation date, permission integer
        colour = discord.Colour.to_rgb(role.Colour) #(r, g, b)
        colour_hex = ('%02x%02x%02x' % colour)
        creation_date = role.created_at()
        members = role.members
        num_members = int(len(role.members))
        permissions = str(role.permissions.value) #put something here to get perms int

        def format_members(members):
            out_str = str("")
            for member in members:
                out_str = out_str + f"{member.display_name()}" + ", "
            return out_str[0:(len(out_str)-1)]
                

        embed=discord.Embed(title=f"Role info for {role.mention()}", description=f"Info requested by {ctx.author.mention()}", color=colour_hex)
        embed.set_author(name=discord.ClientUser.name())
        embed.add_field(name="Colour", value=f"{discord.Color.r()}, {discord.Color.g()}, {discord.Color.b()}    #{colour_hex}", inline=True)
        embed.add_field(name="Creation Date", value=creation_date, inline=True)
        embed.add_field(name="Members:", value=format_members(members), inline=False)
        embed.add_field(name="Number of Members", value=num_members, inline=True)
        embed.add_field(name="Permissions Integer", value=permissions, inline=True)
        await ctx.send(embed=embed)


    # Events are labeled '@commands.Cog.listener()
    #
    #

def setup(bot):
    bot.add_cog(roles(bot))
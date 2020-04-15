import discord
from discord.ext import commands

class BaseCmds(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.errors = client.get_data('errors')

    @commands.group(name='ext')
    async def _ext(self, ctx: commands.Context):
        pass

    @_ext.command(name='list')
    async def _ext_list(self, ctx: commands.Context):
        allexts = ''
        for oneext in self.client.get_data('allexts'):
            if oneext == __name__:
                allexts += f'🔐 {oneext}\n'
            elif oneext in self.client.extensions:
                allexts += f'{self.emj.get("check")} {oneext}\n'
            else:
                allexts += f'{self.emj.get("cross")} {oneext}\n'
        embed = discord.Embed(title=f'🔌 전체 확장 목록', color=self.color['salmon'], description=
            f"""\
                총 {len(self.client.get_data('allexts'))}개 중 {len(self.client.extensions)}개 로드됨.
                {allexts}
            """
        )
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[전체 확장 목록')

    @_ext.command(name='reload')
    async def _ext_reload(self, ctx: commands.Context, *names):
        reloads = self.client.extensions
        if (not names) or ('*' in names):
            for onename in reloads:
                self.client.reload_extension(onename)
            embed = discord.Embed(description=f'**{self.emj.get("check")} 활성된 모든 확장을 리로드했습니다: `{", ".join(reloads)}`**', color=self.color['info'])
            await ctx.send(embed=embed)
        else:
            try:
                for onename in names:
                    if not (onename in reloads):
                        raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
                for onename in names:
                    self.client.reload_extension(onename)
            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description=f'**❓ 로드되지 않았거나 존재하지 않는 확장입니다: `{onename}`**', color=self.color['error'])
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'**{self.emj.get("check")} 확장 리로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'])
                await ctx.send(embed=embed)
        
        
    @_ext.command(name='load')
    async def _ext_load(self, ctx: commands.Context, *names):
        if not names or '*' in names:
            loads = list(set(self.client.get_data('allexts')) - set(self.client.extensions.keys()))
            try:
                if len(loads) == 0:
                    raise commands.ExtensionAlreadyLoaded('모든 확장이 이미 로드되었습니다.')
                for onename in loads:
                    self.client.load_extension(onename)
                    
            except commands.ExtensionAlreadyLoaded:
                embed = discord.Embed(description='**❌ 모든 확장이 이미 로드되었습니다!**', color=self.color['error'])
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'**{self.emj.get("check")} 확장 로드를 완료했습니다: `{", ".join(loads)}`**', color=self.color['info'])
                await ctx.send(embed=embed)
        else:
            try:
                for onename in names:
                    if not (onename in self.client.get_data('allexts')):
                        raise commands.ExtensionNotFound(f'존재하지 않는 확장: {onename}')
                    if onename in self.client.extensions:
                        raise commands.ExtensionAlreadyLoaded(f'이미 로드된 확장: {onename}')
                for onename in names:
                    self.client.load_extension(onename)

            except commands.ExtensionNotFound:
                embed = discord.Embed(description=f'**❓ 존재하지 않는 확장입니다: `{onename}`**', color=self.color['error'])
                await ctx.send(embed=embed)
            except commands.ExtensionAlreadyLoaded:
                embed = discord.Embed(description=f'**❌ 이미 로드된 확장입니다: `{onename}`**', color=self.color['error'])
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'**{self.emj.get("check")} 확장 로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'])
                await ctx.send(embed=embed)

    @_ext.command(name='unload')
    async def _ext_unload(self, ctx: commands.Context, *names):
        if not names or '*' in names:
            unloads = list(self.client.extensions.keys())
            unloads = list(filter(lambda ext: ext not in self.client.get_data('lockedexts'), unloads))
            try:
                if len(unloads) == 0:
                    raise commands.ExtensionNotLoaded('로드된 확장이 하나도 없습니다!')
                for onename in unloads:
                    self.client.unload_extension(onename)
            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description='**❌ 로드된 확장이 하나도 없습니다!`**', color=self.color['error'])
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'**{self.emj.get("check")} 확장 로드를 완료했습니다: `{", ".join(unloads)}`**', color=self.color['info'])
                await ctx.send(embed=embed)
        else:
            try:
                if set(names) >= set(self.client.get_data('lockedexts')):
                    print(self.client.get_data('lockedexts'))
                    lockedinnames = ", ".join(set(names) & set(self.client.get_data("lockedexts")))
                    raise self.errors.LockedExtensionUnloading('잠긴 확장은 언로드할 수 없습니다: ' + lockedinnames)
                for onename in names:
                    if not (onename in self.client.extensions):
                        raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
                for onename in names:
                    self.client.unload_extension(onename)

            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description=f'**❌ 로드되지 않은 확장입니다: `{onename}`**', color=self.color['error'])
                await ctx.send(embed=embed)
            except self.errors.LockedExtensionUnloading:
                embed = discord.Embed(description=f'**🔐 잠긴 확장은 언로드할 수 없습니다: `{lockedinnames}`**', color=self.color['error'])
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'**{self.emj.get("check")} 확장 언로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'])
                await ctx.send(embed=embed)

def setup(client):
    cog = BaseCmds(client)
    for cmd in cog.get_commands():
        cmd.add_check(client.get_data('check').master)
    client.add_cog(cog)
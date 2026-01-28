import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import json
import os
import asyncio

# ────── INTENTS ──────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='.', intents=intents)

CONFIG_FILE = 'config.json'
PRODUTOS_FILE = 'produtos.json'

# ────── FILES ──────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "categoria_id": None,
        "pix_info": "Configure o PIX com .ConfigPix"
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_produtos():
    if os.path.exists(PRODUTOS_FILE):
        with open(PRODUTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_produtos(produtos):
    with open(PRODUTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, indent=4, ensure_ascii=False)

config = load_config()
produtos = load_produtos()

# ────── EVENTS ──────
@bot.event
async def on_ready():
    print(f'🤖 Online como {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="vendas | .ajuda"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão.")

# ────── AJUDA ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def ajuda(ctx):
    embed = discord.Embed(title="📋 Comandos", color=discord.Color.blue())
    embed.add_field(name=".CriarProdutoDrop", value="Criar produto com dropdown + GIF", inline=False)
    embed.add_field(name=".EnviarPainel", value="Enviar painel", inline=False)
    embed.add_field(name=".ConfigCategoria", value="Categoria dos carrinhos", inline=False)
    embed.add_field(name=".ConfigPix", value="Configurar PIX", inline=False)
    await ctx.send(embed=embed)

# ────── CATEGORIA ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def ConfigCategoria(ctx):
    options = [discord.SelectOption(label=c.name, value=str(c.id)) for c in ctx.guild.categories[:25]]
    select = Select(placeholder="Escolha a categoria", options=options)

    async def cb(i):
        config["categoria_id"] = int(select.values[0])
        save_config(config)
        await i.response.send_message("✅ Categoria configurada!", ephemeral=True)

    select.callback = cb
    view = View()
    view.add_item(select)
    await ctx.send("📂 Escolha a categoria:", view=view)

# ────── CRIAR PRODUTO DROPDOWN + GIF ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def CriarProdutoDrop(ctx):

    emoji_select = Select(
        placeholder="Escolha o emoji",
        options=[
            discord.SelectOption(label="Carrinho", emoji="🛒", value="🛒"),
            discord.SelectOption(label="Foguete", emoji="🚀", value="🚀"),
            discord.SelectOption(label="Dinheiro", emoji="💰", value="💰"),
            discord.SelectOption(label="Coroa", emoji="👑", value="👑"),
        ]
    )

    tipo_select = Select(
        placeholder="Tipo do produto",
        options=[
            discord.SelectOption(label="Digital", value="Digital"),
            discord.SelectOption(label="Físico", value="Fisico"),
            discord.SelectOption(label="Serviço", value="Servico"),
            discord.SelectOption(label="Assinatura", value="Assinatura"),
        ]
    )

    view = View(timeout=120)

    async def emoji_cb(i):
        if i.user != ctx.author:
            return await i.response.send_message("❌ Só quem usou o comando.", ephemeral=True)
        view.emoji = emoji_select.values[0]
        await i.response.send_message(f"Emoji escolhido {view.emoji}", ephemeral=True)

    async def tipo_cb(i):
        if i.user != ctx.author:
            return await i.response.send_message("❌ Só quem usou o comando.", ephemeral=True)

        view.tipo = tipo_select.values[0]

        class ProdutoModal(Modal):
            def __init__(self):
                super().__init__(title="Criar Produto")
                self.titulo = TextInput(label="Título")
                self.descricao = TextInput(label="Descrição", style=discord.TextStyle.paragraph)
                self.preco = TextInput(label="Preço")
                self.gif = TextInput(label="Link do GIF ou Imagem")
                self.add_item(self.titulo)
                self.add_item(self.descricao)
                self.add_item(self.preco)
                self.add_item(self.gif)

            async def on_submit(self, inter):
                pid = f"prod_{len(produtos)+1}"
                produtos[pid] = {
                    "titulo": self.titulo.value,
                    "descricao": self.descricao.value,
                    "preco": self.preco.value,
                    "emoji": view.emoji,
                    "tipo": view.tipo,
                    "gif": self.gif.value
                }
                save_produtos(produtos)

                await inter.response.send_message(
                    f"✅ Produto criado!\n{view.emoji} **{self.titulo.value}**",
                    ephemeral=True
                )

        await i.response.send_modal(ProdutoModal())

    emoji_select.callback = emoji_cb
    tipo_select.callback = tipo_cb

    view.add_item(emoji_select)
    view.add_item(tipo_select)

    await ctx.send("🧩 **Criar Produto (Dropdown + GIF)**", view=view)

# ────── PAINEL ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def EnviarPainel(ctx):
    options = [
        discord.SelectOption(
            label=p["titulo"],
            emoji=p.get("emoji", "🛒"),
            description=f"R$ {p['preco']}",
            value=i
        ) for i, p in produtos.items()
    ]

    select = Select(placeholder="Escolha o produto", options=options)

    async def cb(i):
        prod = produtos[select.values[0]]

        embed = discord.Embed(
            title=f"{prod['emoji']} {prod['titulo']}",
            description=prod["descricao"]
        )
        embed.add_field(name="Preço", value=f"R$ {prod['preco']}")
        embed.set_image(url=prod.get("gif"))

        btn = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)

        async def comprar(inter):
            await criar_carrinho(inter, prod)

        btn.callback = comprar
        v = View(timeout=None)
        v.add_item(btn)

        await i.channel.send(embed=embed, view=v)
        await i.response.send_message("✅ Painel enviado!", ephemeral=True)

    select.callback = cb
    view = View()
    view.add_item(select)
    await ctx.send("📦 Escolha o produto:", view=view)

# ────── CARRINHO ──────
async def criar_carrinho(interaction, produto):
    guild = interaction.guild
    user = interaction.user
    categoria = guild.get_channel(config["categoria_id"])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    canal = await categoria.create_text_channel(f"🛒-{user.name}", overwrites=overwrites)

    embed = discord.Embed(title="🛒 Carrinho", description=produto["descricao"])
    embed.add_field(name="Valor", value=f"R$ {produto['preco']}")
    embed.add_field(name="PIX", value=config["pix_info"], inline=False)
    embed.set_image(url=produto.get("gif"))

    fechar = Button(label="🔒 Fechar", style=discord.ButtonStyle.danger)

    async def fechar_cb(i):
        await i.response.send_message("Fechando em 5s...")
        await asyncio.sleep(5)
        await canal.delete()

    fechar.callback = fechar_cb
    view = View(timeout=None)
    view.add_item(fechar)

    await canal.send(user.mention, embed=embed, view=view)
    await interaction.response.send_message(f"✅ Carrinho criado: {canal.mention}", ephemeral=True)

# ────── PIX ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def ConfigPix(ctx):
    modal = Modal(title="Configurar PIX")
    pix = TextInput(label="Dados do PIX", style=discord.TextStyle.paragraph)
    modal.add_item(pix)

    async def submit(i):
        config["pix_info"] = pix.value
        save_config(config)
        await i.response.send_message("✅ PIX configurado!", ephemeral=True)

    modal.on_submit = submit
    btn = Button(label="Configurar PIX")

    async def cb(i):
        await i.response.send_modal(modal)

    btn.callback = cb
    view = View()
    view.add_item(btn)
    await ctx.send("💳 Configurar PIX:", view=view)

# ────── START ──────
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

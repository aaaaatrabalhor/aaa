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

# ────── ARQUIVOS ──────
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

# ────── EVENTOS ──────
@bot.event
async def on_ready():
    print(f'🤖 Bot online como {bot.user}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="vendas | .ajuda"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando.")

# ────── AJUDA ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def ajuda(ctx):
    embed = discord.Embed(title="📋 Comandos Admin", color=discord.Color.blue())
    embed.add_field(name=".CriarProdutoDrop", value="Criar produto com dropdown", inline=False)
    embed.add_field(name=".EnviarPainel", value="Enviar painel de compra", inline=False)
    embed.add_field(name=".ConfigCategoria", value="Definir categoria dos carrinhos", inline=False)
    embed.add_field(name=".ConfigPix", value="Configurar PIX", inline=False)
    await ctx.send(embed=embed)

# ────── CONFIG CATEGORIA ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def ConfigCategoria(ctx):
    options = [
        discord.SelectOption(label=cat.name, value=str(cat.id))
        for cat in ctx.guild.categories[:25]
    ]

    select = Select(placeholder="Escolha a categoria", options=options)

    async def callback(interaction):
        config["categoria_id"] = int(select.values[0])
        save_config(config)
        await interaction.response.send_message("✅ Categoria configurada!", ephemeral=True)

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("📂 Escolha a categoria dos carrinhos:", view=view)

# ────── CRIAR PRODUTO COM DROPDOWN ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def CriarProdutoDrop(ctx):

    emoji_select = Select(
        placeholder="Escolha um emoji",
        options=[
            discord.SelectOption(label="Carrinho", emoji="🛒", value="🛒"),
            discord.SelectOption(label="Foguete", emoji="🚀", value="🚀"),
            discord.SelectOption(label="Dinheiro", emoji="💰", value="💰"),
            discord.SelectOption(label="Coroa", emoji="👑", value="👑"),
            discord.SelectOption(label="Estrela", emoji="⭐", value="⭐"),
        ]
    )

    tipo_select = Select(
        placeholder="Escolha o tipo do produto",
        options=[
            discord.SelectOption(label="Produto Digital", value="Digital"),
            discord.SelectOption(label="Produto Físico", value="Fisico"),
            discord.SelectOption(label="Assinatura", value="Assinatura"),
            discord.SelectOption(label="Serviço", value="Servico"),
        ]
    )

    view = View(timeout=120)

    async def emoji_cb(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message("❌ Apenas quem executou o comando.", ephemeral=True)
        view.emoji = emoji_select.values[0]
        await interaction.response.send_message(f"Emoji escolhido: {view.emoji}", ephemeral=True)

    async def tipo_cb(interaction):
        if interaction.user != ctx.author:
            return await interaction.response.send_message("❌ Apenas quem executou o comando.", ephemeral=True)

        view.tipo = tipo_select.values[0]

        class ProdutoModal(Modal):
            def __init__(self):
                super().__init__(title="Criar Produto")
                self.titulo = TextInput(label="Título")
                self.descricao = TextInput(label="Descrição", style=discord.TextStyle.paragraph)
                self.preco = TextInput(label="Preço (ex: 10.00)")
                self.add_item(self.titulo)
                self.add_item(self.descricao)
                self.add_item(self.preco)

            async def on_submit(self, i):
                pid = f"prod_{len(produtos)+1}"
                produtos[pid] = {
                    "titulo": self.titulo.value,
                    "descricao": self.descricao.value,
                    "preco": self.preco.value,
                    "emoji": view.emoji,
                    "tipo": view.tipo
                }
                save_produtos(produtos)

                await i.response.send_message(
                    f"✅ Produto criado!\n\n"
                    f"{view.emoji} **{self.titulo.value}**\n"
                    f"💰 R$ {self.preco.value}\n"
                    f"📦 {view.tipo}",
                    ephemeral=True
                )

        await interaction.response.send_modal(ProdutoModal())

    emoji_select.callback = emoji_cb
    tipo_select.callback = tipo_cb

    view.add_item(emoji_select)
    view.add_item(tipo_select)

    await ctx.send(
        "🧩 **Criador de Produto (Dropdown)**\n"
        "1️⃣ Escolha o emoji\n"
        "2️⃣ Escolha o tipo",
        view=view
    )

# ────── ENVIAR PAINEL ──────
@bot.command()
@commands.has_permissions(administrator=True)
async def EnviarPainel(ctx):
    options = [
        discord.SelectOption(
            label=p["titulo"],
            description=f"R$ {p['preco']}",
            emoji=p.get("emoji", "🛒"),
            value=i
        )
        for i, p in produtos.items()
    ]

    select = Select(placeholder="Escolha o produto", options=options)

    async def callback(interaction):
        prod = produtos[select.values[0]]
        embed = discord.Embed(
            title=f"{prod.get('emoji','🛒')} {prod['titulo']}",
            description=prod["descricao"]
        )
        embed.add_field(name="Preço", value=f"R$ {prod['preco']}")
        button = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)

        async def comprar(i):
            await criar_carrinho(i, prod)

        button.callback = comprar
        view = View(timeout=None)
        view.add_item(button)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("📦 Selecione o produto:", view=view)

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

    embed = discord.Embed(
        title="🛒 Carrinho",
        description=produto["descricao"]
    )
    embed.add_field(name="Valor", value=f"R$ {produto['preco']}")
    embed.add_field(name="PIX", value=config["pix_info"], inline=False)

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

# ────── CONFIG PIX ──────
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
    await ctx.send("💳 Configuração de PIX:", view=view)

# ────── START ──────
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

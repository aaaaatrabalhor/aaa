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

# ────── CONFIG ──────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'categoria_id': None,
        'pix_info': 'Configure seu PIX com o comando .ConfigPix'
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
    print(f'🤖 Conectado como {bot.user}')
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

# ────── COMANDOS ──────
@bot.command(name='ajuda')
@commands.has_permissions(administrator=True)
async def ajuda(ctx):
    embed = discord.Embed(title="📋 Comandos", color=discord.Color.blue())
    embed.add_field(name=".ConfigCategoria", value="Definir categoria dos carrinhos", inline=False)
    embed.add_field(name=".CriarProduto", value="Criar produto", inline=False)
    embed.add_field(name=".EnviarPainel", value="Enviar painel de compra", inline=False)
    embed.add_field(name=".ListarProdutos", value="Listar produtos", inline=False)
    embed.add_field(name=".ConfigPix", value="Configurar PIX", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ConfigCategoria')
@commands.has_permissions(administrator=True)
async def config_categoria(ctx):
    categorias = ctx.guild.categories
    options = [discord.SelectOption(label=cat.name, value=str(cat.id)) for cat in categorias[:25]]
    select = Select(placeholder="Escolha a categoria", options=options)

    async def callback(interaction):
        config['categoria_id'] = int(select.values[0])
        save_config(config)
        await interaction.response.send_message("✅ Categoria configurada!", ephemeral=True)

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("Escolha a categoria:", view=view)

# ────── MODAL PRODUTO ──────
class CriarProdutoModal(Modal):
    def __init__(self):
        super().__init__(title="Criar Produto")
        self.titulo = TextInput(label="Título")
        self.descricao = TextInput(label="Descrição", style=discord.TextStyle.paragraph)
        self.preco = TextInput(label="Preço")
        self.add_item(self.titulo)
        self.add_item(self.descricao)
        self.add_item(self.preco)

    async def on_submit(self, interaction):
        pid = f"prod_{len(produtos)+1}"
        produtos[pid] = {
            "titulo": self.titulo.value,
            "descricao": self.descricao.value,
            "preco": self.preco.value
        }
        save_produtos(produtos)
        await interaction.response.send_message("✅ Produto criado!", ephemeral=True)

@bot.command(name='CriarProduto')
@commands.has_permissions(administrator=True)
async def criar_produto(ctx):
    button = Button(label="Criar Produto", style=discord.ButtonStyle.green)

    async def callback(interaction):
        await interaction.response.send_modal(CriarProdutoModal())

    button.callback = callback
    view = View()
    view.add_item(button)
    await ctx.send("Clique para criar um produto:", view=view)

@bot.command(name='ListarProdutos')
@commands.has_permissions(administrator=True)
async def listar(ctx):
    embed = discord.Embed(title="📦 Produtos")
    for v in produtos.values():
        embed.add_field(name=v['titulo'], value=f"R$ {v['preco']}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='EnviarPainel')
@commands.has_permissions(administrator=True)
async def enviar_painel(ctx):
    options = [discord.SelectOption(label=p['titulo'], value=i) for i, p in produtos.items()]
    select = Select(placeholder="Escolha o produto", options=options)

    async def callback(interaction):
        prod = produtos[select.values[0]]
        embed = discord.Embed(title=prod['titulo'], description=prod['descricao'])
        embed.add_field(name="Preço", value=f"R$ {prod['preco']}")
        button = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)

        async def comprar(inter):
            await criar_carrinho(inter, prod)

        button.callback = comprar
        view = View(timeout=None)
        view.add_item(button)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("Selecione o produto:", view=view)

# ────── CARRINHO ──────
async def criar_carrinho(interaction, produto):
    guild = interaction.guild
    user = interaction.user
    categoria = guild.get_channel(config['categoria_id'])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    canal = await categoria.create_text_channel(f"🚀-{user.name}", overwrites=overwrites)

    embed = discord.Embed(title="🛒 Carrinho", description=produto['descricao'])
    embed.add_field(name="Valor", value=f"R$ {produto['preco']}")
    embed.add_field(name="PIX", value=config['pix_info'], inline=False)

    fechar = Button(label="🔒 Fechar", style=discord.ButtonStyle.danger)

    async def fechar_cb(i):
        await i.response.send_message("Fechando em 5 segundos...")
        await asyncio.sleep(5)
        await canal.delete()

    fechar.callback = fechar_cb
    view = View(timeout=None)
    view.add_item(fechar)

    await canal.send(user.mention, embed=embed, view=view)
    await interaction.response.send_message(f"✅ Carrinho criado: {canal.mention}", ephemeral=True)

@bot.command(name='ConfigPix')
@commands.has_permissions(administrator=True)
async def config_pix(ctx):
    modal = Modal(title="Configurar PIX")
    pix = TextInput(label="Dados do PIX", style=discord.TextStyle.paragraph)
    modal.add_item(pix)

    async def submit(interaction):
        config['pix_info'] = pix.value
        save_config(config)
        await interaction.response.send_message("✅ PIX configurado!", ephemeral=True)

    modal.on_submit = submit

    button = Button(label="Configurar PIX")

    async def callback(interaction):
        await interaction.response.send_modal(modal)

    button.callback = callback
    view = View()
    view.add_item(button)
    await ctx.send("Clique para configurar o PIX:", view=view)

# ────── START ──────
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

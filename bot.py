import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import json
import os
import asyncio

# ================= INTENTS =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=".", intents=intents)

# ================= ARQUIVOS =================

CONFIG_FILE = "config.json"
PRODUTOS_FILE = "produtos.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

config = load_json(CONFIG_FILE, {
    "categoria_id": None,
    "pix": "Configure com .ConfigPix"
})

produtos = load_json(PRODUTOS_FILE, {})

# ================= PERMISSÃO =================

def admin_or_owner():
    async def predicate(ctx):
        return (
            ctx.author.id == ctx.guild.owner_id or
            ctx.author.guild_permissions.administrator
        )
    return commands.check(predicate)

# ================= BOT =================

@bot.event
async def on_ready():
    print(f"🤖 Online como {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="vendas"
    ))

# ================= MODALS =================

class CriarProdutoDropModal(Modal):
    def __init__(self):
        super().__init__(title="Criar Produto (Dropdown)")
        self.nome = TextInput(label="Nome do produto")
        self.descricao = TextInput(
            label="Descrição",
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.nome)
        self.add_item(self.descricao)

    async def on_submit(self, interaction):
        pid = f"prod_{len(produtos)+1}"
        produtos[pid] = {
            "titulo": self.nome.value,
            "descricao": self.descricao.value,
            "opcoes": []
        }
        save_json(PRODUTOS_FILE, produtos)
        await interaction.response.send_message(
            "✅ Produto criado! Use `.AdicionarOpcao`",
            ephemeral=True
        )

class AdicionarOpcaoModal(Modal):
    def __init__(self, pid):
        super().__init__(title="Adicionar Opção")
        self.pid = pid
        self.nome = TextInput(label="Nome da opção")
        self.preco = TextInput(label="Preço (ex: 9.90)")
        self.desc = TextInput(
            label="Descrição da opção",
            required=False
        )
        self.add_item(self.nome)
        self.add_item(self.preco)
        self.add_item(self.desc)

    async def on_submit(self, interaction):
        produtos[self.pid]["opcoes"].append({
            "label": self.nome.value,
            "preco": self.preco.value,
            "descricao": self.desc.value or "—"
        })
        save_json(PRODUTOS_FILE, produtos)
        await interaction.response.send_message(
            "✅ Opção adicionada!",
            ephemeral=True
        )

# ================= COMANDOS =================

@bot.command()
@admin_or_owner()
async def CriarProdutoDrop(ctx):
    await ctx.send_modal(CriarProdutoDropModal())

@bot.command()
@admin_or_owner()
async def AdicionarOpcao(ctx):
    if not produtos:
        return await ctx.send("❌ Nenhum produto criado")

    options = [
        discord.SelectOption(label=p["titulo"], value=pid)
        for pid, p in produtos.items()
    ]

    select = Select(
        placeholder="Escolha o produto",
        options=options
    )

    async def callback(interaction):
        await interaction.response.send_modal(
            AdicionarOpcaoModal(select.values[0])
        )

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("Selecione o produto:", view=view)

@bot.command()
@admin_or_owner()
async def EnviarPainel(ctx):
    if not produtos:
        return await ctx.send("❌ Nenhum produto disponível")

    options = [
        discord.SelectOption(label=p["titulo"], value=pid)
        for pid, p in produtos.items()
    ]

    select = Select(
        placeholder="Escolha o produto",
        options=options
    )

    async def callback(interaction):
        pid = select.values[0]
        produto = produtos[pid]

        class ProdutoView(View):
            def __init__(self):
                super().__init__(timeout=None)
                self.opcao = None

                self.dropdown = Select(
                    placeholder="Selecione uma opção",
                    options=[
                        discord.SelectOption(
                            label=o["label"],
                            description=f"R$ {o['preco']}",
                            value=str(i)
                        )
                        for i, o in enumerate(produto["opcoes"])
                    ]
                )

                async def drop_cb(i):
                    self.opcao = produto["opcoes"][
                        int(self.dropdown.values[0])
                    ]
                    await i.response.defer()

                self.dropdown.callback = drop_cb
                self.add_item(self.dropdown)

                comprar = Button(
                    label="🛒 Comprar",
                    style=discord.ButtonStyle.success
                )

                async def comprar_cb(i):
                    if not self.opcao:
                        return await i.response.send_message(
                            "❌ Selecione uma opção",
                            ephemeral=True
                        )
                    await criar_carrinho(i, produto, self.opcao)

                comprar.callback = comprar_cb
                self.add_item(comprar)

        embed = discord.Embed(
            title=produto["titulo"],
            description=produto["descricao"],
            color=discord.Color.green()
        )

        await interaction.channel.send(
            embed=embed,
            view=ProdutoView()
        )
        await interaction.response.send_message(
            "✅ Painel enviado",
            ephemeral=True
        )

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("Escolha o produto:", view=view)

# ================= CARRINHO =================

async def criar_carrinho(interaction, produto, opcao):
    guild = interaction.guild
    user = interaction.user
    categoria = guild.get_channel(config["categoria_id"])

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            read_messages=False
        ),
        user: discord.PermissionOverwrite(
            read_messages=True
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True
        )
    }

    canal = await categoria.create_text_channel(
        f"🛒-{user.name}",
        overwrites=overwrites
    )

    embed = discord.Embed(title="🛒 Carrinho")
    embed.add_field(
        name="Produto",
        value=produto["titulo"],
        inline=False
    )
    embed.add_field(
        name="Opção",
        value=opcao["label"],
        inline=False
    )
    embed.add_field(
        name="Preço",
        value=f"R$ {opcao['preco']}",
        inline=False
    )
    embed.add_field(
        name="PIX",
        value=config["pix"],
        inline=False
    )

    fechar = Button(
        label="🔒 Fechar",
        style=discord.ButtonStyle.danger
    )

    async def fechar_cb(i):
        await i.response.send_message("Fechando...")
        await asyncio.sleep(3)
        await canal.delete()

    fechar.callback = fechar_cb

    view = View(timeout=None)
    view.add_item(fechar)

    await canal.send(
        user.mention,
        embed=embed,
        view=view
    )
    await interaction.response.send_message(
        f"Carrinho criado: {canal.mention}",
        ephemeral=True
    )

# ================= CONFIG =================

@bot.command()
@admin_or_owner()
async def ConfigCategoria(ctx):
    options = [
        discord.SelectOption(
            label=c.name,
            value=str(c.id)
        )
        for c in ctx.guild.categories
    ]

    select = Select(
        placeholder="Selecione a categoria",
        options=options
    )

    async def callback(interaction):
        config["categoria_id"] = int(select.values[0])
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message(
            "✅ Categoria configurada",
            ephemeral=True
        )

    select.callback = callback
    view = View()
    view.add_item(select)
    await ctx.send("Escolha a categoria:", view=view)

@bot.command()
@admin_or_owner()
async def ConfigPix(ctx):
    modal = Modal(title="Configurar PIX")
    pix = TextInput(
        label="Dados do PIX",
        style=discord.TextStyle.paragraph
    )
    modal.add_item(pix)

    async def submit(interaction):
        config["pix"] = pix.value
        save_json(CONFIG_FILE, config)
        await interaction.response.send_message(
            "✅ PIX configurado",
            ephemeral=True
        )

    modal.on_submit = submit
    await ctx.send_modal(modal)

# ================= RUN =================

bot.run(os.getenv("DISCORD_TOKEN"))

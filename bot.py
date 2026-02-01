import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import json
import os
from datetime import datetime
import asyncio

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='.', intents=intents)

# Arquivo de configuração
CONFIG_FILE = 'config.json'
PRODUTOS_FILE = 'produtos.json'
PRODUTOS_DROP_FILE = 'produtos_drop.json'

# Carregar ou criar configuração
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'categoria_id': None,
        'pix_info': 'Configure seu PIX com o comando .ConfigPix',
        'qrcode_url': None,
        'contador_carrinhos': {}
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

def load_produtos_drop():
    if os.path.exists(PRODUTOS_DROP_FILE):
        with open(PRODUTOS_DROP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_produtos_drop(produtos_drop):
    with open(PRODUTOS_DROP_FILE, 'w', encoding='utf-8') as f:
        json.dump(produtos_drop, f, indent=4, ensure_ascii=False)

config = load_config()
produtos = load_produtos()
produtos_drop = load_produtos_drop()

# Verificar se é dono do servidor ou administrador
def is_owner_or_admin():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator
    return commands.check(predicate)

# Verificar se é dono do servidor
def is_owner():
    async def predicate(ctx):
        return ctx.author.id == ctx.guild.owner_id
    return commands.check(predicate)

# Evento quando o bot está pronto
@bot.event
async def on_ready():
    print(f'🤖 Bot conectado como {bot.user}')
    print(f'🎯 Pronto para vendas!')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="vendas | .setup"
    ))

# Comando SETUP - Painel principal
@bot.command(name='setup')
@is_owner_or_admin()
async def setup(ctx):
    embed = discord.Embed(
        title="⚙️ Painel de Configuração",
        description="**Bem-vindo ao sistema de vendas!**\n\nEscolha uma opção abaixo para configurar seu bot:",
        color=discord.Color.blue()
    )
    
    categoria_status = "✅ Configurada" if config.get('categoria_id') else "❌ Não configurada"
    pix_status = "✅ Configurado" if config.get('pix_info') != 'Configure seu PIX com o comando .ConfigPix' else "❌ Não configurado"
    qrcode_status = "✅ Configurado" if config.get('qrcode_url') else "❌ Não configurado"
    produtos_count = len(produtos)
    produtos_drop_count = len(produtos_drop)
    
    embed.add_field(name="📁 Categoria", value=categoria_status, inline=True)
    embed.add_field(name="💳 PIX", value=pix_status, inline=True)
    embed.add_field(name="📱 QR Code", value=qrcode_status, inline=True)
    embed.add_field(name="📦 Produtos", value=f"{produtos_count} cadastrados", inline=True)
    embed.add_field(name="📋 Produtos Drop", value=f"{produtos_drop_count} cadastrados", inline=True)
    
    embed.set_footer(text="Use os botões abaixo para gerenciar o bot")
    
    # Criar botões
    btn_categoria = Button(label="📁 Configurar Categoria", style=discord.ButtonStyle.primary, row=0)
    btn_pix = Button(label="💳 Configurar PIX", style=discord.ButtonStyle.primary, row=0)
    btn_qrcode = Button(label="📱 Configurar QR Code", style=discord.ButtonStyle.primary, row=0)
    
    btn_criar_produto = Button(label="➕ Criar Produto", style=discord.ButtonStyle.success, row=1)
    btn_criar_drop = Button(label="📋 Criar Produto Drop", style=discord.ButtonStyle.success, row=1)
    
    btn_editar_produto = Button(label="✏️ Editar Produto", style=discord.ButtonStyle.secondary, row=2)
    btn_editar_drop = Button(label="✏️ Editar Produto Drop", style=discord.ButtonStyle.secondary, row=2)
    
    btn_enviar_painel = Button(label="📤 Enviar Painel", style=discord.ButtonStyle.success, row=3)
    btn_enviar_drop = Button(label="📤 Enviar Painel Drop", style=discord.ButtonStyle.success, row=3)
    
    btn_listar_produtos = Button(label="📋 Listar Produtos", style=discord.ButtonStyle.secondary, row=4)
    btn_listar_drop = Button(label="📋 Listar Produtos Drop", style=discord.ButtonStyle.secondary, row=4)
    
    # Callbacks
    async def categoria_callback(interaction):
        categorias = [cat for cat in interaction.guild.categories]
        
        if not categorias:
            await interaction.response.send_message("❌ Nenhuma categoria encontrada!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(label=cat.name, value=str(cat.id), description=f"ID: {cat.id}")
            for cat in categorias[:25]
        ]
        
        select = Select(placeholder="Escolha uma categoria...", options=options)
        
        async def select_callback(select_interaction):
            config['categoria_id'] = int(select.values[0])
            save_config(config)
            await select_interaction.response.send_message(
                f"✅ Categoria configurada com sucesso!",
                ephemeral=True
            )
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        embed_cat = discord.Embed(
            title="📁 Configurar Categoria",
            description="Selecione a categoria onde os carrinhos serão criados:",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed_cat, view=view_select, ephemeral=True)
    
    async def pix_callback(interaction):
        modal = Modal(title="Configurar PIX")
        
        pix_input = TextInput(
            label="Informações do PIX",
            placeholder="Ex: Chave PIX: seuemail@exemplo.com\nTitular: Seu Nome",
            style=discord.TextStyle.paragraph,
            max_length=500,
            default=config.get('pix_info', '')
        )
        
        modal.add_item(pix_input)
        
        async def on_submit(modal_interaction):
            config['pix_info'] = pix_input.value
            save_config(config)
            
            embed_pix = discord.Embed(
                title="✅ PIX Configurado",
                description="Informações do PIX atualizadas com sucesso!",
                color=discord.Color.green()
            )
            
            await modal_interaction.response.send_message(embed=embed_pix, ephemeral=True)
        
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    async def qrcode_callback(interaction):
        await interaction.response.send_message(
            "📱 Envie a imagem do QR Code PIX neste canal (você tem 60 segundos):",
            ephemeral=True
        )
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and len(m.attachments) > 0
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            
            if msg.attachments:
                attachment = msg.attachments[0]
                
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    config['qrcode_url'] = attachment.url
                    save_config(config)
                    
                    embed_qr = discord.Embed(
                        title="✅ QR Code Configurado",
                        description="QR Code do PIX configurado com sucesso!",
                        color=discord.Color.green()
                    )
                    embed_qr.set_image(url=attachment.url)
                    
                    await interaction.followup.send(embed=embed_qr, ephemeral=True)
                    await msg.delete()
                else:
                    await interaction.followup.send("❌ O arquivo enviado não é uma imagem válida!", ephemeral=True)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Tempo esgotado! Tente novamente.", ephemeral=True)
    
    async def criar_produto_callback(interaction):
        modal = CriarProdutoModal()
        await interaction.response.send_modal(modal)
    
    async def criar_drop_callback(interaction):
        modal = CriarProdutoDropModal1()
        await interaction.response.send_modal(modal)
    
    async def editar_produto_callback(interaction):
        if not produtos:
            await interaction.response.send_message("❌ Nenhum produto cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(
                label=prod['titulo'],
                value=prod_id,
                description=f"R$ {prod['preco']}"
            )
            for prod_id, prod in produtos.items()
        ]
        
        select = Select(placeholder="Escolha o produto para editar...", options=options[:25])
        
        async def select_callback(select_interaction):
            prod_id = select.values[0]
            produto = produtos[prod_id]
            
            modal = EditarProdutoModal(prod_id, produto)
            await select_interaction.response.send_modal(modal)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        embed_edit = discord.Embed(
            title="✏️ Editar Produto",
            description="Selecione o produto que deseja editar:",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed_edit, view=view_select, ephemeral=True)
    
    async def editar_drop_callback(interaction):
        if not produtos_drop:
            await interaction.response.send_message("❌ Nenhum painel dropdown cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(
                label=drop['titulo_painel'],
                value=drop_id,
                description=f"{len(drop['opcoes'])} opções",
                emoji=drop['emoji_painel']
            )
            for drop_id, drop in produtos_drop.items()
        ]
        
        select = Select(placeholder="Escolha o painel dropdown para editar...", options=options[:25])
        
        async def select_callback(select_interaction):
            drop_id = select.values[0]
            painel = produtos_drop[drop_id]
            
            modal = EditarProdutoDropModal1(drop_id, painel)
            await select_interaction.response.send_modal(modal)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        embed_edit = discord.Embed(
            title="✏️ Editar Painel Dropdown",
            description="Selecione o painel dropdown que deseja editar:",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed_edit, view=view_select, ephemeral=True)
    
    async def enviar_painel_callback(interaction):
        if not produtos:
            await interaction.response.send_message("❌ Nenhum produto cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(
                label=prod['titulo'],
                value=prod_id,
                description=f"R$ {prod['preco']}"
            )
            for prod_id, prod in produtos.items()
        ]
        
        select = Select(placeholder="Escolha o produto...", options=options[:25])
        
        async def select_callback(select_interaction):
            prod_id = select.values[0]
            produto = produtos[prod_id]
            
            embed_produto = discord.Embed(
                title=produto['titulo'],
                description=produto['descricao'],
                color=discord.Color.gold()
            )
            embed_produto.add_field(name="💰 Preço", value=f"R$ {produto['preco']}", inline=True)
            
            tipo_imagem = produto.get('tipo_imagem', 'gif')
            
            if produto.get('imagem_url'):
                if tipo_imagem == 'gif':
                    embed_produto.set_image(url=produto['imagem_url'])
                else:
                    embed_produto.set_image(url=produto['imagem_url'])
            
            embed_produto.set_footer(text="Clique em 'Comprar' para iniciar sua compra!")
            
            button = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)
            
            async def comprar_callback(button_interaction):
                await criar_carrinho(button_interaction, produto, prod_id)
            
            button.callback = comprar_callback
            view_produto = View(timeout=None)
            view_produto.add_item(button)
            
            await select_interaction.channel.send(embed=embed_produto, view=view_produto)
            await select_interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        embed_enviar = discord.Embed(
            title="📤 Enviar Painel de Produto",
            description="Selecione o produto que deseja enviar para este canal:",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed_enviar, view=view_select, ephemeral=True)
    
    async def enviar_drop_callback(interaction):
        if not produtos_drop:
            await interaction.response.send_message("❌ Nenhum painel dropdown cadastrado!", ephemeral=True)
            return
        
        options = [
            discord.SelectOption(
                label=drop['titulo_painel'],
                value=drop_id,
                description=f"{len(drop['opcoes'])} opções disponíveis",
                emoji=drop['emoji_painel']
            )
            for drop_id, drop in produtos_drop.items()
        ]
        
        select = Select(placeholder="Escolha o painel dropdown...", options=options[:25])
        
        async def select_callback(select_interaction):
            drop_id = select.values[0]
            painel = produtos_drop[drop_id]
            
            embed_painel = discord.Embed(
                title=f"{painel['emoji_painel']} {painel['titulo_painel']}",
                description=painel['descricao_painel'],
                color=discord.Color.gold()
            )
            
            tipo_imagem = painel.get('tipo_imagem', 'gif')
            
            if painel.get('imagem_url'):
                if tipo_imagem == 'gif':
                    embed_painel.set_image(url=painel['imagem_url'])
                else:
                    embed_painel.set_image(url=painel['imagem_url'])
            
            embed_painel.set_footer(text="Selecione uma opção no menu abaixo para comprar!")
            
            opcoes_select = []
            for i, opcao in enumerate(painel['opcoes'][:25]):
                opcoes_select.append(
                    discord.SelectOption(
                        label=opcao['nome'],
                        value=str(i),
                        description=opcao['descricao'],
                        emoji=opcao['emoji']
                    )
                )
            
            produto_select = Select(
                placeholder="Selecione a quantidade de salas",
                options=opcoes_select
            )
            
            async def produto_select_callback(prod_select_interaction):
                opcao_index = int(produto_select.values[0])
                opcao_selecionada = painel['opcoes'][opcao_index]
                
                produto_temp = {
                    'titulo': f"{painel['titulo_painel']} - {opcao_selecionada['nome']}",
                    'descricao': f"{painel['descricao_painel']}\n\n**Opção selecionada:** {opcao_selecionada['nome']}",
                    'preco': opcao_selecionada['preco'],
                    'imagem_url': painel.get('imagem_url'),
                    'tipo_imagem': painel.get('tipo_imagem', 'gif')
                }
                
                await criar_carrinho(prod_select_interaction, produto_temp, f"{drop_id}_{opcao_index}")
            
            produto_select.callback = produto_select_callback
            view_painel = View(timeout=None)
            view_painel.add_item(produto_select)
            
            await select_interaction.channel.send(embed=embed_painel, view=view_painel)
            await select_interaction.response.send_message("✅ Painel dropdown enviado!", ephemeral=True)
        
        select.callback = select_callback
        view_select = View()
        view_select.add_item(select)
        
        embed_enviar = discord.Embed(
            title="📤 Enviar Painel Dropdown",
            description="Selecione o painel dropdown que deseja enviar para este canal:",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed_enviar, view=view_select, ephemeral=True)
    
    async def listar_produtos_callback(interaction):
        if not produtos:
            await interaction.response.send_message("❌ Nenhum produto cadastrado ainda!", ephemeral=True)
            return
        
        embed_lista = discord.Embed(
            title="📦 Produtos Cadastrados",
            color=discord.Color.blue()
        )
        
        for prod_id, prod in produtos.items():
            tipo_img = prod.get('tipo_imagem', 'gif')
            tipo_texto = "GIF (acima)" if tipo_img == 'gif' else "Banner (embaixo)"
            embed_lista.add_field(
                name=f"{prod['titulo']} ({prod_id})",
                value=f"💰 R$ {prod['preco']}\n📝 {prod['descricao'][:50]}...\n🖼️ {tipo_texto}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed_lista, ephemeral=True)
    
    async def listar_drop_callback(interaction):
        if not produtos_drop:
            await interaction.response.send_message("❌ Nenhum produto dropdown cadastrado ainda!", ephemeral=True)
            return
        
        embed_lista = discord.Embed(
            title="📋 Painéis Dropdown Cadastrados",
            color=discord.Color.blue()
        )
        
        for drop_id, drop in produtos_drop.items():
            opcoes_text = "\n".join([f"• {op['nome']} - R$ {op['preco']}" for op in drop['opcoes'][:3]])
            if len(drop['opcoes']) > 3:
                opcoes_text += f"\n... e mais {len(drop['opcoes']) - 3} opções"
            
            tipo_img = drop.get('tipo_imagem', 'gif')
            tipo_texto = "GIF (acima)" if tipo_img == 'gif' else "Banner (embaixo)"
            
            embed_lista.add_field(
                name=f"{drop['emoji_painel']} {drop['titulo_painel']} ({drop_id})",
                value=f"**Opções ({len(drop['opcoes'])}):**\n{opcoes_text}\n🖼️ {tipo_texto}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed_lista, ephemeral=True)
    
    # Atribuir callbacks
    btn_categoria.callback = categoria_callback
    btn_pix.callback = pix_callback
    btn_qrcode.callback = qrcode_callback
    btn_criar_produto.callback = criar_produto_callback
    btn_criar_drop.callback = criar_drop_callback
    btn_editar_produto.callback = editar_produto_callback
    btn_editar_drop.callback = editar_drop_callback
    btn_enviar_painel.callback = enviar_painel_callback
    btn_enviar_drop.callback = enviar_drop_callback
    btn_listar_produtos.callback = listar_produtos_callback
    btn_listar_drop.callback = listar_drop_callback
    
    # Criar view
    view = View(timeout=None)
    view.add_item(btn_categoria)
    view.add_item(btn_pix)
    view.add_item(btn_qrcode)
    view.add_item(btn_criar_produto)
    view.add_item(btn_criar_drop)
    view.add_item(btn_editar_produto)
    view.add_item(btn_editar_drop)
    view.add_item(btn_enviar_painel)
    view.add_item(btn_enviar_drop)
    view.add_item(btn_listar_produtos)
    view.add_item(btn_listar_drop)
    
    await ctx.send(embed=embed, view=view)

# Comando de ajuda
@bot.command(name='ajuda')
@is_owner_or_admin()
async def ajuda(ctx):
    embed = discord.Embed(
        title="📋 Comandos do Bot de Vendas",
        description="Sistema profissional de vendas para Discord",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name=".setup",
        value="🎯 **PAINEL PRINCIPAL** - Acesse todas as configurações em um só lugar!",
        inline=False
    )
    
    embed.set_footer(text="Use .setup para gerenciar tudo facilmente!")
    
    await ctx.send(embed=embed)

# Comando para configurar categoria
@bot.command(name='ConfigCategoria')
@is_owner_or_admin()
async def config_categoria(ctx):
    embed = discord.Embed(
        title="⚙️ Configurar Categoria",
        description="Selecione a categoria onde os carrinhos serão criados:",
        color=discord.Color.green()
    )
    
    categorias = [cat for cat in ctx.guild.categories]
    
    if not categorias:
        await ctx.send("❌ Nenhuma categoria encontrada no servidor!")
        return
    
    options = [
        discord.SelectOption(label=cat.name, value=str(cat.id), description=f"ID: {cat.id}")
        for cat in categorias[:25]
    ]
    
    select = Select(placeholder="Escolha uma categoria...", options=options)
    
    async def select_callback(interaction):
        config['categoria_id'] = int(select.values[0])
        save_config(config)
        await interaction.response.send_message(
            f"✅ Categoria configurada: <#{select.values[0]}>",
            ephemeral=True
        )
    
    select.callback = select_callback
    view = View()
    view.add_item(select)
    
    await ctx.send(embed=embed, view=view)

# Modal para criar produto
class CriarProdutoModal(Modal):
    def __init__(self):
        super().__init__(title="Criar Novo Produto")
        
        self.titulo = TextInput(
            label="Título do Produto",
            placeholder="Ex: VIP Premium",
            max_length=100
        )
        
        self.descricao = TextInput(
            label="Descrição do Produto",
            placeholder="Descreva o que o cliente receberá...",
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        
        self.preco = TextInput(
            label="Preço (R$)",
            placeholder="Ex: 29.90",
            max_length=10
        )
        
        self.imagem_url = TextInput(
            label="URL da Imagem (GIF ou Banner)",
            placeholder="https://...",
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo)
        self.add_item(self.descricao)
        self.add_item(self.preco)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        button_gif = Button(label="🎬 GIF (acima)", style=discord.ButtonStyle.primary)
        button_banner = Button(label="🖼️ Banner (embaixo)", style=discord.ButtonStyle.secondary)
        
        async def gif_callback(btn_interaction):
            produto_id = f"prod_{len(produtos) + 1}"
            
            produtos[produto_id] = {
                'titulo': self.titulo.value,
                'descricao': self.descricao.value,
                'preco': self.preco.value,
                'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
                'tipo_imagem': 'gif',
                'criado_em': datetime.now().isoformat()
            }
            
            save_produtos(produtos)
            
            embed = discord.Embed(
                title="✅ Produto Criado com Sucesso!",
                description=f"**ID:** {produto_id}\n**Título:** {self.titulo.value}\n**Tipo:** GIF (acima)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def banner_callback(btn_interaction):
            produto_id = f"prod_{len(produtos) + 1}"
            
            produtos[produto_id] = {
                'titulo': self.titulo.value,
                'descricao': self.descricao.value,
                'preco': self.preco.value,
                'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
                'tipo_imagem': 'banner',
                'criado_em': datetime.now().isoformat()
            }
            
            save_produtos(produtos)
            
            embed = discord.Embed(
                title="✅ Produto Criado com Sucesso!",
                description=f"**ID:** {produto_id}\n**Título:** {self.titulo.value}\n**Tipo:** Banner (embaixo)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        button_gif.callback = gif_callback
        button_banner.callback = banner_callback
        
        view = View()
        view.add_item(button_gif)
        view.add_item(button_banner)
        
        embed = discord.Embed(
            title="🖼️ Escolha o Tipo de Imagem",
            description="**GIF (acima):** Imagem exibida acima do texto\n**Banner (embaixo):** Imagem grande exibida embaixo do texto",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Modal para editar produto
class EditarProdutoModal(Modal):
    def __init__(self, produto_id, produto):
        super().__init__(title=f"Editar Produto: {produto['titulo']}")
        self.produto_id = produto_id
        
        self.titulo = TextInput(
            label="Título do Produto",
            placeholder="Ex: VIP Premium",
            max_length=100,
            default=produto['titulo']
        )
        
        self.descricao = TextInput(
            label="Descrição do Produto",
            placeholder="Descreva o que o cliente receberá...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            default=produto['descricao']
        )
        
        self.preco = TextInput(
            label="Preço (R$)",
            placeholder="Ex: 29.90",
            max_length=10,
            default=produto['preco']
        )
        
        self.imagem_url = TextInput(
            label="URL da Imagem (GIF ou Banner)",
            placeholder="https://...",
            required=False,
            max_length=500,
            default=produto.get('imagem_url', '')
        )
        
        self.add_item(self.titulo)
        self.add_item(self.descricao)
        self.add_item(self.preco)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        button_gif = Button(label="🎬 GIF (acima)", style=discord.ButtonStyle.primary)
        button_banner = Button(label="🖼️ Banner (embaixo)", style=discord.ButtonStyle.secondary)
        
        async def gif_callback(btn_interaction):
            produtos[self.produto_id]['titulo'] = self.titulo.value
            produtos[self.produto_id]['descricao'] = self.descricao.value
            produtos[self.produto_id]['preco'] = self.preco.value
            produtos[self.produto_id]['imagem_url'] = self.imagem_url.value if self.imagem_url.value else None
            produtos[self.produto_id]['tipo_imagem'] = 'gif'
            produtos[self.produto_id]['editado_em'] = datetime.now().isoformat()
            
            save_produtos(produtos)
            
            embed = discord.Embed(
                title="✅ Produto Atualizado!",
                description=f"**ID:** {self.produto_id}\n**Título:** {self.titulo.value}\n**Tipo:** GIF (acima)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def banner_callback(btn_interaction):
            produtos[self.produto_id]['titulo'] = self.titulo.value
            produtos[self.produto_id]['descricao'] = self.descricao.value
            produtos[self.produto_id]['preco'] = self.preco.value
            produtos[self.produto_id]['imagem_url'] = self.imagem_url.value if self.imagem_url.value else None
            produtos[self.produto_id]['tipo_imagem'] = 'banner'
            produtos[self.produto_id]['editado_em'] = datetime.now().isoformat()
            
            save_produtos(produtos)
            
            embed = discord.Embed(
                title="✅ Produto Atualizado!",
                description=f"**ID:** {self.produto_id}\n**Título:** {self.titulo.value}\n**Tipo:** Banner (embaixo)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        button_gif.callback = gif_callback
        button_banner.callback = banner_callback
        
        view = View()
        view.add_item(button_gif)
        view.add_item(button_banner)
        
        embed = discord.Embed(
            title="🖼️ Escolha o Tipo de Imagem",
            description="**GIF (acima):** Imagem exibida acima do texto\n**Banner (embaixo):** Imagem grande exibida embaixo do texto",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Modal para criar produto dropdown - Configuração inicial
class CriarProdutoDropModal1(Modal):
    def __init__(self):
        super().__init__(title="Criar Painel Dropdown - Parte 1")
        
        self.titulo_painel = TextInput(
            label="Título do Painel",
            placeholder="Ex: Escolha seu pacote de SALAS",
            max_length=100
        )
        
        self.descricao_painel = TextInput(
            label="Descrição do Painel",
            placeholder="Selecione a quantidade de salas que deseja comprar",
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        
        self.emoji_painel = TextInput(
            label="Emoji do Painel (opcional)",
            placeholder="Ex: 💎 ou 🎁",
            required=False,
            max_length=10
        )
        
        self.imagem_url = TextInput(
            label="URL da Imagem (GIF ou Banner)",
            placeholder="https://...",
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo_painel)
        self.add_item(self.descricao_painel)
        self.add_item(self.emoji_painel)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        button_gif = Button(label="🎬 GIF (acima)", style=discord.ButtonStyle.primary)
        button_banner = Button(label="🖼️ Banner (embaixo)", style=discord.ButtonStyle.secondary)
        
        async def gif_callback(btn_interaction):
            temp_id = f"temp_{interaction.user.id}"
            
            if not hasattr(bot, 'temp_produtos_drop'):
                bot.temp_produtos_drop = {}
            
            bot.temp_produtos_drop[temp_id] = {
                'titulo_painel': self.titulo_painel.value,
                'descricao_painel': self.descricao_painel.value,
                'emoji_painel': self.emoji_painel.value if self.emoji_painel.value else '📦',
                'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
                'tipo_imagem': 'gif',
                'opcoes': []
            }
            
            await btn_interaction.response.send_message(
                "✅ Painel configurado (GIF)! Agora adicione as opções do dropdown:",
                ephemeral=True
            )
            
            button_add = Button(label="➕ Adicionar Opção", style=discord.ButtonStyle.success)
            button_finish = Button(label="✅ Finalizar Painel", style=discord.ButtonStyle.primary)
            
            async def add_option_callback(btn_interaction2):
                modal = CriarOpcaoDropModal(temp_id)
                await btn_interaction2.response.send_modal(modal)
            
            async def finish_callback(btn_interaction2):
                if len(bot.temp_produtos_drop[temp_id]['opcoes']) == 0:
                    await btn_interaction2.response.send_message(
                        "❌ Adicione pelo menos uma opção antes de finalizar!",
                        ephemeral=True
                    )
                    return
                
                drop_id = f"drop_{len(produtos_drop) + 1}"
                produtos_drop[drop_id] = bot.temp_produtos_drop[temp_id]
                produtos_drop[drop_id]['criado_em'] = datetime.now().isoformat()
                save_produtos_drop(produtos_drop)
                
                del bot.temp_produtos_drop[temp_id]
                
                embed = discord.Embed(
                    title="✅ Painel Dropdown Criado!",
                    description=f"**ID:** {drop_id}\n**Título:** {produtos_drop[drop_id]['titulo_painel']}\n**Opções:** {len(produtos_drop[drop_id]['opcoes'])}",
                    color=discord.Color.green()
                )
                
                await btn_interaction2.response.send_message(embed=embed, ephemeral=True)
            
            button_add.callback = add_option_callback
            button_finish.callback = finish_callback
            
            view2 = View(timeout=300)
            view2.add_item(button_add)
            view2.add_item(button_finish)
            
            embed2 = discord.Embed(
                title="➕ Adicionar Opções ao Dropdown",
                description=f"**Painel:** {self.titulo_painel.value}\n\nClique em 'Adicionar Opção' para cada produto do dropdown.",
                color=discord.Color.blue()
            )
            
            await btn_interaction.followup.send(embed=embed2, view=view2, ephemeral=True)
        
        async def banner_callback(btn_interaction):
            temp_id = f"temp_{interaction.user.id}"
            
            if not hasattr(bot, 'temp_produtos_drop'):
                bot.temp_produtos_drop = {}
            
            bot.temp_produtos_drop[temp_id] = {
                'titulo_painel': self.titulo_painel.value,
                'descricao_painel': self.descricao_painel.value,
                'emoji_painel': self.emoji_painel.value if self.emoji_painel.value else '📦',
                'imagem_url': self.imagem_url.value if self.imagem_url.value else None,
                'tipo_imagem': 'banner',
                'opcoes': []
            }
            
            await btn_interaction.response.send_message(
                "✅ Painel configurado (Banner)! Agora adicione as opções do dropdown:",
                ephemeral=True
            )
            
            button_add = Button(label="➕ Adicionar Opção", style=discord.ButtonStyle.success)
            button_finish = Button(label="✅ Finalizar Painel", style=discord.ButtonStyle.primary)
            
            async def add_option_callback(btn_interaction2):
                modal = CriarOpcaoDropModal(temp_id)
                await btn_interaction2.response.send_modal(modal)
            
            async def finish_callback(btn_interaction2):
                if len(bot.temp_produtos_drop[temp_id]['opcoes']) == 0:
                    await btn_interaction2.response.send_message(
                        "❌ Adicione pelo menos uma opção antes de finalizar!",
                        ephemeral=True
                    )
                    return
                
                drop_id = f"drop_{len(produtos_drop) + 1}"
                produtos_drop[drop_id] = bot.temp_produtos_drop[temp_id]
                produtos_drop[drop_id]['criado_em'] = datetime.now().isoformat()
                save_produtos_drop(produtos_drop)
                
                del bot.temp_produtos_drop[temp_id]
                
                embed = discord.Embed(
                    title="✅ Painel Dropdown Criado!",
                    description=f"**ID:** {drop_id}\n**Título:** {produtos_drop[drop_id]['titulo_painel']}\n**Opções:** {len(produtos_drop[drop_id]['opcoes'])}",
                    color=discord.Color.green()
                )
                
                await btn_interaction2.response.send_message(embed=embed, ephemeral=True)
            
            button_add.callback = add_option_callback
            button_finish.callback = finish_callback
            
            view2 = View(timeout=300)
            view2.add_item(button_add)
            view2.add_item(button_finish)
            
            embed2 = discord.Embed(
                title="➕ Adicionar Opções ao Dropdown",
                description=f"**Painel:** {self.titulo_painel.value}\n\nClique em 'Adicionar Opção' para cada produto do dropdown.",
                color=discord.Color.blue()
            )
            
            await btn_interaction.followup.send(embed=embed2, view=view2, ephemeral=True)
        
        button_gif.callback = gif_callback
        button_banner.callback = banner_callback
        
        view = View()
        view.add_item(button_gif)
        view.add_item(button_banner)
        
        embed = discord.Embed(
            title="🖼️ Escolha o Tipo de Imagem",
            description="**GIF (acima):** Imagem exibida acima do texto\n**Banner (embaixo):** Imagem grande exibida embaixo do texto",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Modal para editar produto dropdown - Configuração inicial
class EditarProdutoDropModal1(Modal):
    def __init__(self, drop_id, painel):
        super().__init__(title=f"Editar Painel: {painel['titulo_painel']}")
        self.drop_id = drop_id
        
        self.titulo_painel = TextInput(
            label="Título do Painel",
            placeholder="Ex: Escolha seu pacote de SALAS",
            max_length=100,
            default=painel['titulo_painel']
        )
        
        self.descricao_painel = TextInput(
            label="Descrição do Painel",
            placeholder="Selecione a quantidade de salas que deseja comprar",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            default=painel['descricao_painel']
        )
        
        self.emoji_painel = TextInput(
            label="Emoji do Painel (opcional)",
            placeholder="Ex: 💎 ou 🎁",
            required=False,
            max_length=10,
            default=painel.get('emoji_painel', '📦')
        )
        
        self.imagem_url = TextInput(
            label="URL da Imagem (GIF ou Banner)",
            placeholder="https://...",
            required=False,
            max_length=500,
            default=painel.get('imagem_url', '')
        )
        
        self.add_item(self.titulo_painel)
        self.add_item(self.descricao_painel)
        self.add_item(self.emoji_painel)
        self.add_item(self.imagem_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        button_gif = Button(label="🎬 GIF (acima)", style=discord.ButtonStyle.primary)
        button_banner = Button(label="🖼️ Banner (embaixo)", style=discord.ButtonStyle.secondary)
        
        async def gif_callback(btn_interaction):
            produtos_drop[self.drop_id]['titulo_painel'] = self.titulo_painel.value
            produtos_drop[self.drop_id]['descricao_painel'] = self.descricao_painel.value
            produtos_drop[self.drop_id]['emoji_painel'] = self.emoji_painel.value if self.emoji_painel.value else '📦'
            produtos_drop[self.drop_id]['imagem_url'] = self.imagem_url.value if self.imagem_url.value else None
            produtos_drop[self.drop_id]['tipo_imagem'] = 'gif'
            produtos_drop[self.drop_id]['editado_em'] = datetime.now().isoformat()
            
            save_produtos_drop(produtos_drop)
            
            embed = discord.Embed(
                title="✅ Painel Atualizado!",
                description=f"**ID:** {self.drop_id}\n**Título:** {self.titulo_painel.value}\n**Tipo:** GIF (acima)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        async def banner_callback(btn_interaction):
            produtos_drop[self.drop_id]['titulo_painel'] = self.titulo_painel.value
            produtos_drop[self.drop_id]['descricao_painel'] = self.descricao_painel.value
            produtos_drop[self.drop_id]['emoji_painel'] = self.emoji_painel.value if self.emoji_painel.value else '📦'
            produtos_drop[self.drop_id]['imagem_url'] = self.imagem_url.value if self.imagem_url.value else None
            produtos_drop[self.drop_id]['tipo_imagem'] = 'banner'
            produtos_drop[self.drop_id]['editado_em'] = datetime.now().isoformat()
            
            save_produtos_drop(produtos_drop)
            
            embed = discord.Embed(
                title="✅ Painel Atualizado!",
                description=f"**ID:** {self.drop_id}\n**Título:** {self.titulo_painel.value}\n**Tipo:** Banner (embaixo)",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        button_gif.callback = gif_callback
        button_banner.callback = banner_callback
        
        view = View()
        view.add_item(button_gif)
        view.add_item(button_banner)
        
        embed = discord.Embed(
            title="🖼️ Escolha o Tipo de Imagem",
            description="**GIF (acima):** Imagem exibida acima do texto\n**Banner (embaixo):** Imagem grande exibida embaixo do texto",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Modal para adicionar opção ao dropdown
class CriarOpcaoDropModal(Modal):
    def __init__(self, temp_id):
        super().__init__(title="Adicionar Opção ao Dropdown")
        self.temp_id = temp_id
        
        self.nome_opcao = TextInput(
            label="Nome da Opção",
            placeholder="Ex: 10 SALAS",
            max_length=100
        )
        
        self.descricao_opcao = TextInput(
            label="Descrição da Opção",
            placeholder="Ex: Valor: 2.90",
            max_length=100,
            required=False
        )
        
        self.preco = TextInput(
            label="Preço (R$)",
            placeholder="Ex: 2.90",
            max_length=10
        )
        
        self.emoji_opcao = TextInput(
            label="Emoji da Opção (opcional)",
            placeholder="Ex: 💰",
            required=False,
            max_length=10
        )
        
        self.add_item(self.nome_opcao)
        self.add_item(self.descricao_opcao)
        self.add_item(self.preco)
        self.add_item(self.emoji_opcao)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.temp_id not in bot.temp_produtos_drop:
            await interaction.response.send_message(
                "❌ Erro: Dados temporários não encontrados. Inicie novamente.",
                ephemeral=True
            )
            return
        
        opcao = {
            'nome': self.nome_opcao.value,
            'descricao': self.descricao_opcao.value if self.descricao_opcao.value else f"Valor: {self.preco.value}",
            'preco': self.preco.value,
            'emoji': self.emoji_opcao.value if self.emoji_opcao.value else '💎'
        }
        
        bot.temp_produtos_drop[self.temp_id]['opcoes'].append(opcao)
        
        total_opcoes = len(bot.temp_produtos_drop[self.temp_id]['opcoes'])
        
        embed = discord.Embed(
            title="✅ Opção Adicionada!",
            description=f"**Nome:** {opcao['nome']}\n**Preço:** R$ {opcao['preco']}\n\n**Total de opções:** {total_opcoes}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Função para criar carrinho
async def criar_carrinho(interaction, produto, prod_id):
    guild = interaction.guild
    user = interaction.user
    
    if not config.get('categoria_id'):
        await interaction.response.send_message(
            "❌ Categoria não configurada! Peça ao administrador para usar .setup",
            ephemeral=True
        )
        return
    
    categoria = guild.get_channel(config['categoria_id'])
    
    if not categoria:
        await interaction.response.send_message(
            "❌ Categoria não encontrada! Peça ao administrador para reconfigurar.",
            ephemeral=True
        )
        return
    
    if str(guild.id) not in config['contador_carrinhos']:
        config['contador_carrinhos'][str(guild.id)] = 0
    
    numero = config['contador_carrinhos'][str(guild.id)]
    config['contador_carrinhos'][str(guild.id)] += 1
    save_config(config)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    nome_canal = f"🚀{user.name}-{numero}"
    canal = await categoria.create_text_channel(name=nome_canal, overwrites=overwrites)
    
    embed_carrinho = discord.Embed(
        title=f"🛒 Carrinho de Compra - {produto['titulo']}",
        description=produto['descricao'],
        color=discord.Color.blue()
    )
    
    embed_carrinho.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=True)
    embed_carrinho.add_field(name="👤 Cliente", value=user.mention, inline=True)
    
    tipo_imagem = produto.get('tipo_imagem', 'gif')
    
    if produto.get('imagem_url'):
        if tipo_imagem == 'gif':
            embed_carrinho.set_image(url=produto['imagem_url'])
        else:
            embed_carrinho.set_image(url=produto['imagem_url'])
    
    embed_carrinho.set_footer(text="Use os botões abaixo para gerenciar o pagamento")
    
    aprovar_btn = Button(label="✅ Aprovar Pagamento", style=discord.ButtonStyle.success)
    fechar_btn = Button(label="🔒 Fechar", style=discord.ButtonStyle.danger)
    qrcode_btn = Button(label="📱 QR Code", style=discord.ButtonStyle.primary)
    pix_btn = Button(label="💳 PIX", style=discord.ButtonStyle.secondary)
    
    async def aprovar_callback(btn_interaction):
        if btn_interaction.user.id != guild.owner_id and not btn_interaction.user.guild_permissions.administrator:
            await btn_interaction.response.send_message(
                "❌ Apenas o dono ou administradores podem aprovar pagamentos!",
                ephemeral=True
            )
            return
        
        await btn_interaction.response.send_message(
            f"✅ Pagamento aprovado! {user.mention}, obrigado pela compra! 🎉"
        )
    
    async def fechar_callback(btn_interaction):
        if btn_interaction.user.id != guild.owner_id and not btn_interaction.user.guild_permissions.administrator:
            await btn_interaction.response.send_message(
                "❌ Apenas o dono ou administradores podem fechar o carrinho!",
                ephemeral=True
            )
            return
        
        await btn_interaction.response.send_message("🔒 Fechando carrinho em 5 segundos...")
        await asyncio.sleep(5)
        await canal.delete()
    
    async def qrcode_callback(btn_interaction):
        if config.get('qrcode_url'):
            embed_qr = discord.Embed(
                title="📱 QR Code PIX",
                description="Escaneie o QR Code abaixo para realizar o pagamento:",
                color=discord.Color.green()
            )
            embed_qr.set_image(url=config['qrcode_url'])
            embed_qr.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=True)
            await btn_interaction.response.send_message(embed=embed_qr, ephemeral=True)
        else:
            await btn_interaction.response.send_message(
                "❌ QR Code não configurado! Peça ao administrador para usar .setup",
                ephemeral=True
            )
    
    async def pix_callback(btn_interaction):
        embed_pix = discord.Embed(
            title="💳 Informações PIX",
            description=config.get('pix_info', 'Configure o PIX com .setup'),
            color=discord.Color.gold()
        )
        embed_pix.add_field(name="💰 Valor a Pagar", value=f"R$ {produto['preco']}", inline=False)
        embed_pix.set_footer(text="Após realizar o pagamento, envie o comprovante neste canal")
        await btn_interaction.response.send_message(embed=embed_pix, ephemeral=True)
    
    aprovar_btn.callback = aprovar_callback
    fechar_btn.callback = fechar_callback
    qrcode_btn.callback = qrcode_callback
    pix_btn.callback = pix_callback
    
    view = View(timeout=None)
    view.add_item(qrcode_btn)
    view.add_item(pix_btn)
    view.add_item(aprovar_btn)
    view.add_item(fechar_btn)
    
    await canal.send(f"{user.mention}", embed=embed_carrinho, view=view)
    
    await interaction.response.send_message(f"✅ Carrinho criado! Acesse {canal.mention}", ephemeral=True)

# Comando para configurar PIX
@bot.command(name='ConfigPix')
@is_owner_or_admin()
async def config_pix(ctx):
    button = Button(label="Configurar PIX", style=discord.ButtonStyle.primary)
    
    modal = Modal(title="Configurar Informações do PIX")
    
    pix_input = TextInput(
        label="Informações do PIX",
        placeholder="Ex: Chave PIX: seuemail@exemplo.com\nTitular: Seu Nome",
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    modal.add_item(pix_input)
    
    async def on_submit(interaction):
        config['pix_info'] = pix_input.value
        save_config(config)
        
        embed = discord.Embed(
            title="✅ PIX Configurado",
            description="Informações do PIX atualizadas com sucesso!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    modal.on_submit = on_submit
    
    async def button_callback(interaction):
        await interaction.response.send_modal(modal)
    
    button.callback = button_callback
    view = View()
    view.add_item(button)
    
    await ctx.send("💳 Clique no botão para configurar o PIX:", view=view)

# Comando para configurar QR Code
@bot.command(name='ConfigQRCode')
@is_owner_or_admin()
async def config_qrcode(ctx):
    await ctx.send("📱 Envie a imagem do QR Code PIX:")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.attachments) > 0
    
    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        
        if msg.attachments:
            attachment = msg.attachments[0]
            
            if attachment.content_type and attachment.content_type.startswith('image/'):
                config['qrcode_url'] = attachment.url
                save_config(config)
                
                embed = discord.Embed(
                    title="✅ QR Code Configurado",
                    description="QR Code do PIX configurado com sucesso!",
                    color=discord.Color.green()
                )
                embed.set_image(url=attachment.url)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ O arquivo enviado não é uma imagem válida!")
        else:
            await ctx.send("❌ Nenhuma imagem foi anexada!")
            
    except asyncio.TimeoutError:
        await ctx.send("❌ Tempo esgotado! Use o comando novamente.")

# Tratar menções no canal de carrinho
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.name.startswith('🚀') and message.attachments:
        owner = message.guild.owner
        admins = [m for m in message.guild.members if m.guild_permissions.administrator and not m.bot]
        
        mentions = f"{owner.mention}"
        if admins and len(admins) > 0:
            mentions += " " + " ".join([m.mention for m in admins[:3]])
        
        await message.channel.send(
            f"📸 {mentions}, comprovante enviado por {message.author.mention}!"
        )
    
    await bot.process_commands(message)

import os

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == '__main__':
    print("🚀 Iniciando bot de vendas...")
    bot.run(TOKEN)

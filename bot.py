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
        'logs_privado_id': None,
        'feedback_channel_id': None,
        'pix_info': 'Configure seu PIX com o comando .ConfigPix',
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
        name="vendas | .ajuda"
    ))

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
        name=".ConfigCategoria",
        value="Configure a categoria onde os carrinhos serão criados",
        inline=False
    )
    embed.add_field(
        name=".CriarProduto",
        value="Crie um painel de produto com título, descrição, GIF e preço",
        inline=False
    )
    embed.add_field(
        name=".CriarProdutoDrop",
        value="Crie um painel com dropdown de múltiplas opções de produtos",
        inline=False
    )
    embed.add_field(
        name=".EnviarPainel",
        value="Envie um painel de produto para um canal específico",
        inline=False
    )
    embed.add_field(
        name=".EnviarPainelDrop",
        value="Envie um painel dropdown para um canal específico",
        inline=False
    )
    embed.add_field(
        name=".LogsPrivado <#canal>",
        value="Configure o canal de logs privadas",
        inline=False
    )
    embed.add_field(
        name=".ConfigFeedback <#canal>",
        value="Configure o canal de feedback dos clientes",
        inline=False
    )
    embed.add_field(
        name=".ConfigPix",
        value="Configure as informações do PIX",
        inline=False
    )
    embed.add_field(
        name=".FeedbackCliente",
        value="Solicite feedback do cliente (use no carrinho)",
        inline=False
    )
    embed.add_field(
        name=".ListarProdutos",
        value="Liste todos os produtos cadastrados",
        inline=False
    )
    embed.add_field(
        name=".ListarProdutosDrop",
        value="Liste todos os produtos dropdown cadastrados",
        inline=False
    )
    
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
        for cat in categorias[:25]  # Discord permite máximo 25 opções
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
        
        self.gif_url = TextInput(
            label="URL do GIF/Imagem",
            placeholder="https://...",
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo)
        self.add_item(self.descricao)
        self.add_item(self.preco)
        self.add_item(self.gif_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        produto_id = f"prod_{len(produtos) + 1}"
        
        produtos[produto_id] = {
            'titulo': self.titulo.value,
            'descricao': self.descricao.value,
            'preco': self.preco.value,
            'gif_url': self.gif_url.value if self.gif_url.value else None,
            'criado_em': datetime.now().isoformat()
        }
        
        save_produtos(produtos)
        
        embed = discord.Embed(
            title="✅ Produto Criado com Sucesso!",
            description=f"**ID:** {produto_id}\n**Título:** {self.titulo.value}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        
        self.gif_url = TextInput(
            label="URL do GIF/Imagem (opcional)",
            placeholder="https://...",
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo_painel)
        self.add_item(self.descricao_painel)
        self.add_item(self.emoji_painel)
        self.add_item(self.gif_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Salvar temporariamente os dados
        temp_id = f"temp_{interaction.user.id}"
        
        if not hasattr(bot, 'temp_produtos_drop'):
            bot.temp_produtos_drop = {}
        
        bot.temp_produtos_drop[temp_id] = {
            'titulo_painel': self.titulo_painel.value,
            'descricao_painel': self.descricao_painel.value,
            'emoji_painel': self.emoji_painel.value if self.emoji_painel.value else '📦',
            'gif_url': self.gif_url.value if self.gif_url.value else None,
            'opcoes': []
        }
        
        # Criar botão para adicionar opções
        await interaction.response.send_message(
            "✅ Painel configurado! Agora adicione as opções do dropdown:",
            ephemeral=True
        )
        
        # Enviar mensagem com botão para adicionar opções
        button_add = Button(label="➕ Adicionar Opção", style=discord.ButtonStyle.success)
        button_finish = Button(label="✅ Finalizar Painel", style=discord.ButtonStyle.primary)
        
        async def add_option_callback(btn_interaction):
            modal = CriarOpcaoDropModal(temp_id)
            await btn_interaction.response.send_modal(modal)
        
        async def finish_callback(btn_interaction):
            if len(bot.temp_produtos_drop[temp_id]['opcoes']) == 0:
                await btn_interaction.response.send_message(
                    "❌ Adicione pelo menos uma opção antes de finalizar!",
                    ephemeral=True
                )
                return
            
            # Salvar produto dropdown
            drop_id = f"drop_{len(produtos_drop) + 1}"
            produtos_drop[drop_id] = bot.temp_produtos_drop[temp_id]
            produtos_drop[drop_id]['criado_em'] = datetime.now().isoformat()
            save_produtos_drop(produtos_drop)
            
            # Limpar dados temporários
            del bot.temp_produtos_drop[temp_id]
            
            embed = discord.Embed(
                title="✅ Painel Dropdown Criado!",
                description=f"**ID:** {drop_id}\n**Título:** {produtos_drop[drop_id]['titulo_painel']}\n**Opções:** {len(produtos_drop[drop_id]['opcoes'])}",
                color=discord.Color.green()
            )
            
            await btn_interaction.response.send_message(embed=embed, ephemeral=True)
        
        button_add.callback = add_option_callback
        button_finish.callback = finish_callback
        
        view = View(timeout=300)
        view.add_item(button_add)
        view.add_item(button_finish)
        
        embed = discord.Embed(
            title="➕ Adicionar Opções ao Dropdown",
            description=f"**Painel:** {self.titulo_painel.value}\n\nClique em 'Adicionar Opção' para cada produto do dropdown.",
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

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

# Comando para criar produto
@bot.command(name='CriarProduto')
@is_owner_or_admin()
async def criar_produto(ctx):
    modal = CriarProdutoModal()
    await ctx.send("✨ Abrindo formulário para criar produto...", delete_after=3)
    
    button = Button(label="Criar Produto", style=discord.ButtonStyle.green, emoji="➕")
    
    async def button_callback(interaction):
        await interaction.response.send_modal(modal)
    
    button.callback = button_callback
    view = View()
    view.add_item(button)
    
    embed = discord.Embed(
        title="➕ Criar Novo Produto",
        description="Clique no botão abaixo para abrir o formulário",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=view)

# Comando para criar produto dropdown
@bot.command(name='CriarProdutoDrop')
@is_owner_or_admin()
async def criar_produto_drop(ctx):
    modal = CriarProdutoDropModal1()
    
    button = Button(label="Criar Painel Dropdown", style=discord.ButtonStyle.green, emoji="📋")
    
    async def button_callback(interaction):
        await interaction.response.send_modal(modal)
    
    button.callback = button_callback
    view = View()
    view.add_item(button)
    
    embed = discord.Embed(
        title="📋 Criar Painel Dropdown",
        description="Clique no botão abaixo para criar um painel com múltiplas opções de produtos",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=view)

# Comando para listar produtos
@bot.command(name='ListarProdutos')
@is_owner_or_admin()
async def listar_produtos(ctx):
    if not produtos:
        await ctx.send("❌ Nenhum produto cadastrado ainda!")
        return
    
    embed = discord.Embed(
        title="📦 Produtos Cadastrados",
        color=discord.Color.blue()
    )
    
    for prod_id, prod in produtos.items():
        embed.add_field(
            name=f"{prod['titulo']} ({prod_id})",
            value=f"💰 R$ {prod['preco']}\n📝 {prod['descricao'][:50]}...",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Comando para listar produtos dropdown
@bot.command(name='ListarProdutosDrop')
@is_owner_or_admin()
async def listar_produtos_drop(ctx):
    if not produtos_drop:
        await ctx.send("❌ Nenhum produto dropdown cadastrado ainda!")
        return
    
    embed = discord.Embed(
        title="📋 Painéis Dropdown Cadastrados",
        color=discord.Color.blue()
    )
    
    for drop_id, drop in produtos_drop.items():
        opcoes_text = "\n".join([f"• {op['nome']} - R$ {op['preco']}" for op in drop['opcoes'][:3]])
        if len(drop['opcoes']) > 3:
            opcoes_text += f"\n... e mais {len(drop['opcoes']) - 3} opções"
        
        embed.add_field(
            name=f"{drop['emoji_painel']} {drop['titulo_painel']} ({drop_id})",
            value=f"**Opções ({len(drop['opcoes'])}):**\n{opcoes_text}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Comando para enviar painel
@bot.command(name='EnviarPainel')
@is_owner_or_admin()
async def enviar_painel(ctx):
    if not produtos:
        await ctx.send("❌ Nenhum produto cadastrado! Use .CriarProduto primeiro.")
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
    
    async def select_callback(interaction):
        prod_id = select.values[0]
        produto = produtos[prod_id]
        
        # Criar embed do produto
        embed = discord.Embed(
            title=produto['titulo'],
            description=produto['descricao'],
            color=discord.Color.gold()
        )
        embed.add_field(name="💰 Preço", value=f"R$ {produto['preco']}", inline=True)
        
        if produto['gif_url']:
            embed.set_image(url=produto['gif_url'])
        
        embed.set_footer(text="Clique em 'Comprar' para iniciar sua compra!")
        
        # Botão de comprar
        button = Button(label="🛒 Comprar", style=discord.ButtonStyle.success)
        
        async def comprar_callback(button_interaction):
            await criar_carrinho(button_interaction, produto, prod_id)
        
        button.callback = comprar_callback
        view = View(timeout=None)
        view.add_item(button)
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
    
    select.callback = select_callback
    view = View()
    view.add_item(select)
    
    embed = discord.Embed(
        title="📤 Enviar Painel de Produto",
        description="Selecione o produto que deseja enviar para este canal:",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=view)

# Comando para enviar painel dropdown
@bot.command(name='EnviarPainelDrop')
@is_owner_or_admin()
async def enviar_painel_drop(ctx):
    if not produtos_drop:
        await ctx.send("❌ Nenhum painel dropdown cadastrado! Use .CriarProdutoDrop primeiro.")
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
    
    async def select_callback(interaction):
        drop_id = select.values[0]
        painel = produtos_drop[drop_id]
        
        # Criar embed do painel
        embed = discord.Embed(
            title=f"{painel['emoji_painel']} {painel['titulo_painel']}",
            description=painel['descricao_painel'],
            color=discord.Color.gold()
        )
        
        if painel['gif_url']:
            embed.set_image(url=painel['gif_url'])
        
        embed.set_footer(text="Selecione uma opção no menu abaixo para comprar!")
        
        # Criar select menu com as opções
        opcoes_select = []
        for i, opcao in enumerate(painel['opcoes'][:25]):  # Máximo 25 opções
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
        
        async def produto_select_callback(select_interaction):
            opcao_index = int(produto_select.values[0])
            opcao_selecionada = painel['opcoes'][opcao_index]
            
            # Criar "produto" temporário para o carrinho
            produto_temp = {
                'titulo': f"{painel['titulo_painel']} - {opcao_selecionada['nome']}",
                'descricao': f"{painel['descricao_painel']}\n\n**Opção selecionada:** {opcao_selecionada['nome']}",
                'preco': opcao_selecionada['preco'],
                'gif_url': painel['gif_url']
            }
            
            await criar_carrinho(select_interaction, produto_temp, f"{drop_id}_{opcao_index}")
        
        produto_select.callback = produto_select_callback
        view = View(timeout=None)
        view.add_item(produto_select)
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel dropdown enviado!", ephemeral=True)
    
    select.callback = select_callback
    view = View()
    view.add_item(select)
    
    embed = discord.Embed(
        title="📤 Enviar Painel Dropdown",
        description="Selecione o painel dropdown que deseja enviar para este canal:",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=view)

# Função para criar carrinho
async def criar_carrinho(interaction, produto, prod_id):
    guild = interaction.guild
    user = interaction.user
    
    # Verificar se categoria está configurada
    if not config.get('categoria_id'):
        await interaction.response.send_message(
            "❌ Categoria não configurada! Peça ao administrador para usar .ConfigCategoria",
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
    
    # Contador de carrinhos
    if str(guild.id) not in config['contador_carrinhos']:
        config['contador_carrinhos'][str(guild.id)] = 0
    
    numero = config['contador_carrinhos'][str(guild.id)]
    config['contador_carrinhos'][str(guild.id)] += 1
    save_config(config)
    
    # Criar canal do carrinho
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    nome_canal = f"🚀{user.name}-{numero}"
    canal = await categoria.create_text_channel(name=nome_canal, overwrites=overwrites)
    
    # Embed do carrinho
    embed = discord.Embed(
        title=f"🛒 Carrinho de Compra - {produto['titulo']}",
        description=produto['descricao'],
        color=discord.Color.blue()
    )
    
    embed.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=True)
    embed.add_field(name="👤 Cliente", value=user.mention, inline=True)
    
    embed.add_field(
        name="\n📱 Informações de Pagamento - PIX",
        value=config.get('pix_info', 'Configure o PIX com .ConfigPix'),
        inline=False
    )
    
    if produto['gif_url']:
        embed.set_image(url=produto['gif_url'])
    
    embed.set_footer(text="Envie o comprovante de pagamento neste canal")
    
    # Botões do carrinho
    aprovar_btn = Button(label="✅ Aprovar Pagamento", style=discord.ButtonStyle.success)
    fechar_btn = Button(label="🔒 Fechar", style=discord.ButtonStyle.danger)
    
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
        if btn_interaction.user.id != guild.owner_id and not btn_interaction.user.guild_permissions.administrator and btn_interaction.user.id != user.id:
            await btn_interaction.response.send_message(
                "❌ Você não tem permissão para fechar este carrinho!",
                ephemeral=True
            )
            return
        
        await btn_interaction.response.send_message("🔒 Fechando carrinho em 5 segundos...")
        await asyncio.sleep(5)
        await canal.delete()
    
    aprovar_btn.callback = aprovar_callback
    fechar_btn.callback = fechar_callback
    
    view = View(timeout=None)
    view.add_item(aprovar_btn)
    view.add_item(fechar_btn)
    
    await canal.send(f"{user.mention}", embed=embed, view=view)
    
    # Log privado
    if config.get('logs_privado_id'):
        log_channel = guild.get_channel(config['logs_privado_id'])
        if log_channel:
            log_embed = discord.Embed(
                title="🛒 Novo Carrinho Aberto",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="👤 Cliente", value=f"{user.mention} ({user.id})", inline=True)
            log_embed.add_field(name="📦 Produto", value=produto['titulo'], inline=True)
            log_embed.add_field(name="💰 Valor", value=f"R$ {produto['preco']}", inline=True)
            log_embed.add_field(name="📝 Canal", value=canal.mention, inline=True)
            
            await log_channel.send(embed=log_embed)
    
    await interaction.response.send_message(
        f"✅ Carrinho criado! Acesse {canal.mention}",
        ephemeral=True
    )

# Comando para configurar logs privado
@bot.command(name='LogsPrivado')
@is_owner_or_admin()
async def logs_privado(ctx, canal: discord.TextChannel):
    config['logs_privado_id'] = canal.id
    save_config(config)
    
    embed = discord.Embed(
        title="✅ Logs Privado Configurado",
        description=f"Canal de logs: {canal.mention}",
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

# Comando para configurar feedback
@bot.command(name='ConfigFeedback')
@is_owner_or_admin()
async def config_feedback(ctx, canal: discord.TextChannel):
    config['feedback_channel_id'] = canal.id
    save_config(config)
    
    embed = discord.Embed(
        title="✅ Canal de Feedback Configurado",
        description=f"Canal de feedback: {canal.mention}",
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

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

# Comando para solicitar feedback
@bot.command(name='FeedbackCliente')
@is_owner_or_admin()
async def feedback_cliente(ctx):
    # Verificar se está em um canal de carrinho
    if not ctx.channel.name.startswith('🚀'):
        await ctx.send("❌ Este comando só pode ser usado em canais de carrinho!")
        return
    
    if not config.get('feedback_channel_id'):
        await ctx.send("❌ Canal de feedback não configurado! Use .ConfigFeedback")
        return
    
    # Encontrar o cliente
    cliente = None
    for member in ctx.channel.members:
        if member.id != ctx.guild.me.id and member.id != ctx.guild.owner_id:
            cliente = member
            break
    
    if not cliente:
        await ctx.send("❌ Cliente não encontrado no canal!")
        return
    
    embed = discord.Embed(
        title="⭐ Avaliação de Atendimento",
        description=f"{cliente.mention}, como foi sua experiência?\n\nPor favor, avalie nosso atendimento e produto!",
        color=discord.Color.gold()
    )
    
    # Criar seletor de estrelas
    options = [
        discord.SelectOption(label="⭐⭐⭐⭐⭐ (5 estrelas)", value="5", emoji="⭐"),
        discord.SelectOption(label="⭐⭐⭐⭐ (4 estrelas)", value="4", emoji="⭐"),
        discord.SelectOption(label="⭐⭐⭐ (3 estrelas)", value="3", emoji="⭐"),
        discord.SelectOption(label="⭐⭐ (2 estrelas)", value="2", emoji="⭐"),
        discord.SelectOption(label="⭐ (1 estrela)", value="1", emoji="⭐"),
    ]
    
    select = Select(placeholder="Selecione a quantidade de estrelas...", options=options)
    
    feedback_text = None
    
    async def select_callback(interaction):
        nonlocal feedback_text
        
        # Modal para comentário
        modal = Modal(title="Deixe seu Comentário")
        
        comentario = TextInput(
            label="O que achou do atendimento/produto?",
            placeholder="Deixe seu comentário aqui...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=False
        )
        
        modal.add_item(comentario)
        
        async def modal_submit(modal_interaction):
            estrelas = int(select.values[0])
            estrelas_visual = "⭐" * estrelas
            
            # Enviar feedback para o canal configurado
            feedback_channel = ctx.guild.get_channel(config['feedback_channel_id'])
            
            if feedback_channel:
                feedback_embed = discord.Embed(
                    title="⭐ Novo Feedback Recebido",
                    color=discord.Color.gold(),
                    timestamp=datetime.now()
                )
                
                feedback_embed.add_field(name="👤 Cliente", value=cliente.mention, inline=True)
                feedback_embed.add_field(name="⭐ Avaliação", value=estrelas_visual, inline=True)
                feedback_embed.add_field(name="📊 Nota", value=f"{estrelas}/5", inline=True)
                
                if comentario.value:
                    feedback_embed.add_field(
                        name="💬 Comentário",
                        value=comentario.value,
                        inline=False
                    )
                
                feedback_embed.set_footer(text=f"Canal: {ctx.channel.name}")
                
                await feedback_channel.send(embed=feedback_embed)
            
            # Confirmar para o cliente
            await modal_interaction.response.send_message(
                f"✅ Obrigado pelo seu feedback, {cliente.mention}! 🎉",
                ephemeral=False
            )
        
        modal.on_submit = modal_submit
        await interaction.response.send_modal(modal)
    
    select.callback = select_callback
    view = View()
    view.add_item(select)
    
    await ctx.send(embed=embed, view=view)

# Tratar menções no canal de carrinho
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Se for upload de imagem em canal de carrinho
    if message.channel.name.startswith('🚀') and message.attachments:
        # Mencionar o dono e administradores
        owner = message.guild.owner
        admins = [m for m in message.guild.members if m.guild_permissions.administrator and not m.bot]
        
        mentions = f"{owner.mention}"
        if admins and len(admins) > 0:
            mentions += " " + " ".join([m.mention for m in admins[:3]])  # Máximo 3 admins
        
        await message.channel.send(
            f"📸 {mentions}, comprovante enviado por {message.author.mention}!"
        )
    
    await bot.process_commands(message)

import os

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == '__main__':
    print("🚀 Iniciando bot de vendas...")
    bot.run(TOKEN)
